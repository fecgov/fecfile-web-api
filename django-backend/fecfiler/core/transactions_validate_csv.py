import hashlib
import os
import os.path
from os import path
import psycopg2
import pandas as pd 
from pandas_schema import Column, Schema
from pandas_schema.validation import MatchesPatternValidation, InListValidation
import boto3
from botocore.exceptions import ClientError
from io import StringIO
from pandas.util import hash_pandas_object
import numpy
from psycopg2.extensions import register_adapter, AsIs
import logging
import time
import re
from sqlalchemy import create_engine
from sqlalchemy.types import String
from sqlalchemy.types import NVARCHAR
from sqlalchemy.types import Text
from django.db import connection

# Postgres Database Settings - local
PG_HOST = os.getenv('DB_HOST')
PG_PORT = os.getenv('DB_PORT')
PG_DATABASE = os.getenv('DB_NAME')
PG_USER = os.getenv('DB_USERNAME')
PG_PASSWORD = os.getenv('DB_PASSWORD')


# Setting the logging level
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR)

def validate_dataframe(data):
    #check if the column contains only values of a particular schedule 
    # print(sched)
    # print(data['SCHEDULE NAME'])
    sched = data['SCHEDULE NAME'][0][0:2]
    #print("data['SCHEDULE NAME']",data['SCHEDULE NAME'][0],'sched:',sched)     
    if data['SCHEDULE NAME'].str.contains(sched).any():
        print ("schedule matches")
        return "Validate_Pass"
    else: 
        print ("Non schedule matches available")
        return "Multiple_Sched"


def save_data_from_excel_to_db(data):
    #print('in the get_data_from_csv')
    postgreSQLTable = 'ref_forms_scheds_format_specs'
    try:
        # "postgres://PG_USER:PG_PASSWORD@PG_HOST:PG_PORT/PG_DATABASE"
        connectionstring = "postgres://" + PG_USER + ":" + PG_PASSWORD + "@" + PG_HOST + ":" + PG_PORT + "/" + PG_DATABASE
        #print("connectionstring : ",connectionstring)
        engine   = create_engine(connectionstring, pool_recycle=3600);
        postgreSQLConnection = engine.connect()
        data.to_sql(postgreSQLTable, postgreSQLConnection,  if_exists='append', index=False, dtype={'AUTO-GENERATE': Text} )
        #time.sleep(1)
    except ValueError as vx:
        print("valuerror; ")
        print(vx)
    except Exception as ex:  
        print("In EXCEPTION BLOCK ")
        print(ex)
    finally:
        postgreSQLConnection.close()



def export_excel_to_db(filename, path):
    try:
        filelocation = path
        filewithpath = filelocation + filename
        print("File name",filewithpath)
        str = filename.split('_')
        formname  = str[0]
        schedname = str[1] 
        xls = pd.ExcelFile(filewithpath)
        res = len(xls.sheet_names)
        sheet_to_start = 1
        if res == 1:
            sheet_to_start = 0
        #print(xls.sheet_names)
        for sheet_name in xls.sheet_names[sheet_to_start:]:
            print(sheet_name)
            if sheet_name != 'All Receipts':
                df = pd.read_excel(filewithpath, 
                                    sheet_name=sheet_name, 
                                    index_col=0,
                                    skiprows = range(0, 2)
                                    ,usecols="A,B,C,D,E,F,G")
                                    #,dtype=String)
                df.dropna(how="all", inplace=True)
                df.rename(columns = {'Auto populate ': 'AUTO-GENERATE', 
                                        'Auto populate': 'AUTO-GENERATE',
                                        'FIELD DESCRIPTION':'FIELD\nDESCRIPTION',
                                        'SAMPLE DATA':'SAMPLE\nDATA',
                                        'VALUE REFERENCE':'VALUE\nREFERENCE'}, inplace=True)
                df.insert (0, "formname", formname)         
                df.insert (1, "schedname", schedname)         
                df.insert (2, "transaction_type", sheet_name)         

                #print(df)
                save_data_from_excel_to_db(df)
                #break
    except Exception as ex:  
        print("In export_excel_to_db EXCEPTION BLOCK ")
        print(ex)

def rename_files_folder(filelocation):
    #RENAME XLS FILES TO PARSE AND UPDATE
    #filename = "F3X_ScheduleA_FormatSpecs_Import_Transactions_UNIQUE_CODE.xlsx"
    #F3X - Schedule A_Format Specs_Import Transactions_MAPPED
    with os.scandir(filelocation) as entries:
        for entry in entries:
            if ' - ' in entry.name:
                res = re.split(' |-|_|!', entry.name)
                #print(res[4])
                filename = 'F3L_Schedule' + res[4] + '_FormatSpecs_Import_Transactions_MAPPED.xlsx'
                # print(filelocation+entry.name)
                # print(filelocation+filename)   
                os.rename(filelocation+entry.name,filelocation+filename)

def move_data_from_excel_to_db(form):
    try:
        dirname = os.path.dirname
        filelocation = dirname(dirname(os.getcwd()))+"/csv/Final_SPECS/F3L/unique_code_final/"
        if form == 'F3X':
            filelocation = dirname(dirname(os.getcwd()))+"/csv/Final_SPECS/F3X/unique_code_final/"
        counter = 1
        rename_files_folder(filelocation)
        with os.scandir(filelocation) as entries:
            for entry in entries:
                export_excel_to_db(entry.name,filelocation)
                counter+=1
    except Exception as ex:
        print(ex)


def schema_validation(dataframe, schema, bktname, key, errorfilename):
    try:
        #print('msg',dataframe)
        errors = schema.validate(dataframe)
        #print(errors)
        errdf = []       
        for error in errors:
            msg = error.message 
            error.message = re.sub("[\"@*&?].*[\"@*&?]", "", msg)
            #print('[',error.row,',',error.column,',',error.value,',',error.message,']')
            errdf.append({  	'row_no':       error.row,
				'field_name':   error.column,
				'msg':          error.message
				})                

        errors_index_rows = [e.row for e in errors]
        #print('errors_index_rows: ',len(errors_index_rows))
        if len(errors_index_rows) > 0:
            if path.exists(errorfilename):
                pd.DataFrame(errdf, columns=['row_no', 'field_name', 'msg']).to_csv(errorfilename, mode='a', header=False, index = False)
            else:
                pd.DataFrame(errdf, columns=['row_no', 'field_name', 'msg']).to_csv(errorfilename, mode='a', header=True, index = False)

        data_clean = dataframe.drop(index=errors_index_rows)
        data_dirty = pd.concat([data_clean, dataframe]).drop_duplicates(keep=False)
        data = {"errors": data_dirty, "data_clean": data_clean}
        return data
    except ClientError as e:
        print('ClientError Exception in schema_validation:',e)
        logging.debug("error in schema_validation method")
        logging.debug(e)
        raise
    except Exception as e:
        print('Exception Regular in schema_validation:',e)
        logging.debug("error in schema_validation method")
        logging.debug(e)
        raise

def build_schemas(formname, sched, trans_type):
    try:
        # connection = psycopg2.connect(user='postgres',
        #                               password = 'postgres',
        #                               host='localhost',
        #                               port='5432',
        #                               database='postgres'  )
        connection = psycopg2.connect(user=PG_USER,
                                      password = PG_PASSWORD,
                                      host=PG_HOST,
                                      port=PG_PORT,
                                      database=PG_DATABASE)
        cursor = connection.cursor()
        # print('formname',formname) 
        # print('sched',sched) 
        # print('trans_type',trans_type)
        cursor.execute("SELECT rfsfs.formname, rfsfs.schedname, rfsfs.transaction_type, rfsfs.field_description, rfsfs.type, rfsfs.required	FROM public.ref_forms_scheds_format_specs rfsfs WHERE rfsfs.formname  = %s AND rfsfs.schedname = %s AND rfsfs.transaction_type = %s and rfsfs.type IS NOT NULL",(formname, sched, trans_type)) 
        format_specs = cursor.fetchall()
        columns = []
        headers = []
        for counter, row in enumerate(format_specs):
            field = row[3]
            type  = row[4]
            required = row[5]
            #print('----------------------------------------------------------------------------')
            s = type.split('-')
            len = s[1]
            if 'A/N' in type:
                if required is None:
                    pattern = '^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,' + len + '}$'
                    mpv = MatchesPatternValidation(pattern)
                    column = Column(field, [mpv],allow_empty=True)
                else:
                    #print('A/N is mandatory with len: ', len,' field: ',field)
                    if field in ['REPORT TYPE', 'REPORT YEAR', 'SCHEDULE NAME', 'TRANSACTION IDENTIFIER', 'TRANSACTION NUMBER', 'ENTITY TYPE']:
                        pattern = '^[A-Za-z0-9_-]{1,' + len + '}$'
                    else:
                        #print('field:',field)
                        pattern = '^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,' + len + '}$'
                    pattern = '^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,' + len + '}$'
                    mpv = MatchesPatternValidation(pattern)
                    column = Column(field, [mpv], allow_empty= False)
                columns.append(column)
                headers.append(field)
                print(field)
            elif 'NUM' in type:
                print(field)
                pattern = '^[0-9]\d{0,'+ len + '}(\.\d{1,3})?%?$'
                mpv = MatchesPatternValidation(pattern)
                column = Column(field, [mpv])
                columns.append(column)
                headers.append(field)
            elif 'AMT' in type:
                print(field)
                pattern = '^-?\d\d*[,]?\d*[,]?\d*[.,]?\d*\d$' #'^((\d){1,3},*){1,5}\.(\d){2}$' #'^[\\w\\s]{1,'+ len + '}$'
                mpv = MatchesPatternValidation(pattern)
                column = Column(field, [mpv])
                columns.append(column)
                headers.append(field)
        schema = Schema(columns)
        head_schema = [headers,schema]
        return head_schema
    except ValueError as vx:
        print("valuerror; ")
        print('Exception in build_schemas:',vx)
    except Exception as ex:  
        print("In EXCEPTION BLOCK ")
        print('Exception in build_schemas:',vx)
    finally:
        connection.close();

def check_errkey_exists(bktname, key):
    errkey = key.split('/')
    print()
    errkey = errkey[0] + '/error_files/' + errkey[1]
    #errkey = key + '/error_files'

    print('key', key)
    print('errkey', errkey)
    s3 = boto3.client('s3')    
    result = s3.list_objects(Bucket=bktname, Prefix=errkey )
    exists=False
    #print(result)
    if "Contents" not in result:
        print("list objects doesn'texist:")
        s3.put_object(Bucket=bktname, Key=(errkey+'/'))

def create_cmte_error_folder(bktname, key, errfilerelpath):
    #print('create_cmte_error_folder:',bktname)
    #print('create_cmte_error_folder:',errfilerelpath)
    
    s3 = boto3.client('s3')
    #check_errkey_exists(bktname, key)
    result = s3.list_objects(Bucket=bktname, Prefix=errfilerelpath )
    #print('cmteid result',result)
    exists=False
    if "Contents" not in result:
        print("list objects doesn'texist:")
        s3.put_object(Bucket=bktname, Key=(errfilerelpath+'/'))
    # else:
    #     print("list objects exist:")
    

def move_error_files_to_s3(bktname, key, errorfilename, cmteid):
    try:
        keyfolder = key.split('/')[0]
        #print(keyfolder)
        #print(bktname)
        #print('222222222222222')
        cmte_err_folder = keyfolder + '/error_files/' + cmteid

        create_cmte_error_folder(bktname, key, cmte_err_folder)
        errfilerelpath = keyfolder + '/error_files/' + cmteid + '/' + errorfilename
        s3 = boto3.resource('s3')
        s3.Bucket(bktname).upload_file(errorfilename, errfilerelpath)
        #os.remove(errorfilename)
        return errfilerelpath
    except ClientError as e:
        print(e)
        logging.debug("error in move_error_files_to_s3 method")
        logging.debug(e)
        raise
    except Exception as e: 
        print(e)
        logging.debug("error in move_error_files_to_s3 method")
        logging.debug(e)
        raise

def load_dataframe_from_s3(bktname, key, size, sleeptime, cmteid):
    #print(bktname, key)
    resvalidation=""
    errorfilename=""
    try:
        str = key.split('_')
        schedule  = str[1]
        formname = (str[0].split('/'))[1] 
        if 'H' in schedule or 'h' in schedule:
            sched = schedule.replace('Schedule','')
        else:
            sched = schedule.replace('Schedule','S')
        # print('sched:',sched)
        print('schedule ',schedule) 
        print('formname ',formname)        
        tablename = 'temp'
        if "/" in key:
            tablename=key[key.find("/")+1:-4].split()[0]
        else:
            raise Exception('S3 key not having a / char')
        tablename = tablename.lower() 
        # print("tablename:", tablename)  
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bktname, Key=key)
        body = obj['Body']
        csv_string = body.read().decode('utf-8')
        res = ''
        flag = False
        for data in pd.read_csv(StringIO(csv_string), dtype=object,  iterator=True, chunksize=size):
            data = data.dropna(axis=[0], how='all')
            res = validate_dataframe(data)
            if "Validate_Pass" != res:
               return res                        
            data = data.sort_values(by=["TRANSACTION IDENTIFIER"], ascending=False)
            # print('...............')
            #loop through the data set to pick unique tranid's 
            cntr = 1
            for tranid in data['TRANSACTION IDENTIFIER'].unique():
                cntr+=1
                #print('cntr',cntr)
                # build schema based on tranid
                head_schema = build_schemas(formname, schedule, tranid)
                headers = head_schema[0]
                schema  = head_schema[1]

                #print('....headers....',(",".join(headers)))
                #print('....schema....',schema) 
                
                # headersstr = pd.Series(headers.flatten())
                # data_temp = data[headers]
                #include_clique = products[products.str.contains("Product A")]
                #print(headers)
                # for h in headers:
                #     print(h)    
                        
                data_temp = data[headers]
                #print('tranid:',tranid)
                print('tranid:',tranid.strip())
                #data_temp = data_temp.loc[(data['TRANSACTION IDENTIFIER'] == tranid)]
                #print(data_temp)
                errorfilename = re.match(r"(.*)\.csv", key).group(1).split('/')[1] + '_error.csv'
                resvalidation = schema_validation(data_temp, schema, bktname, key, errorfilename)
            flag = True
            print('AAAAAAAAA:',errorfilename)
        if path.exists(errorfilename):
            print('11111111111111111')
            errfilerelpath = move_error_files_to_s3(bktname, key, errorfilename, cmteid)     
            return errfilerelpath
        elif flag is True:
            return 'Validate_Pass' 
        else: 
            return 'Validate_Fail' 
    except ClientError as e:
        print('Exception in load_dataframe_from_s3:',e)
        logging.debug("error in load_dataframe_from_s3 method")
        logging.debug(e)
        raise
    except Exception as e:
        print('Exception in load_dataframe_from_s3:',e)
        logging.debug("error in load_dataframe_from_s3 method")
        logging.debug(e)
        raise
        

#main method to call the process 
def validate_transactions(bktname, key, cmteid):
    try:

        #send_message_to_queue()
        #aws sqs receive-message --queue-url https://queue.amazonaws.com/813218302951/fecfile-importtransactions --attribute-names All --message-attribute-names All --max-number-of-messages 10
        #aws sqs purge-queue --queue-url https://queue.amazonaws.com/813218302951/fecfile-importtransactions
        #print("bktname: ",bktname, ", Key : ", key)
        returnstr = "File_not_found"
        check_errkey_exists(bktname, key)
        if check_file_exists(bktname, key):
            if bktname and key:
                res = load_dataframe_from_s3(bktname, key, 100000, 1, cmteid) #100,000 records and 1s timer is for testing and need to be updated.
                #print(res)
                if res != 'Validate_Pass':
                    print("Error with data validation:", res)
                    returnstr = res 
                else:
                    print("Queue is empty!!!")

            #print(returnstr)
            if returnstr is not "File_not_found":
                print(returnstr.split('/'))

            returnstr = {    "errorfilename": returnstr,
                            "bktname" : bktname,
                            "key"     : key }
            
            
            return returnstr
    except Exception as ex:
        print(ex)
        logging.debug("error in process_transactions method")
        returnstr = {    "errorfilename": "File_not_found",
                        "bktname" : bktname,
                        "key"     : key }
        print(returnstr)                
        return returnstr



def check_file_exists(bktname, key):
    s3 = boto3.client('s3')
    try:
        s3.head_object(Bucket=bktname, Key=key)
        return True
    except ClientError:
        # Not found
        raise



# cmteid =  "C00011111"
# bktname = "fecfile-filing-frontend"
                    
# key = "transactions/F3X_ScheduleB_Import_Transactions_11_25_TEST_Data.csv"
# if bktname and key:
#     print(validate_transactions(bktname, key, cmteid))
# else: 
#     print("No data")

#move_data_from_excel_to_db('F3X')



# errfilerelpath = 'transactions/error_files/' + cmteid
# s3 = boto3.client('s3')
# result = s3.list_objects(Bucket=bktname, Prefix=errfilerelpath )
# #print('cmteid result',result)
# exists=False
# if "Contents" not in result:
#     print("list objects doesn'texist:")
#     s3.put_object(Bucket=bktname, Key=(errfilerelpath+'/'))
# else:
#     print("list objects exist:")
