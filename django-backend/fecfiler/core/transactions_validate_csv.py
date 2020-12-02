import hashlib
import os
import psycopg2
import pandas as pd 
from pandas_schema import Column, Schema
from pandas_schema.validation import MatchesPatternValidation, InListValidation
import boto3
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
from sqlalchemy import create_engine
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

def validate_dataframe(data, sched):
    #check if the column contains only values of a particular schedule 
    print(sched)
    print(data['SCHEDULE NAME'])
        
    if data['SCHEDULE NAME'].str.contains(sched).any():
        print ("schedule matches")
    else: 
        print ("Non schedule matches available")
        return "Multiple_Sched"
    return "Validate_Pass"

# to drop tables  ​
#     sql = "DROP TABLE IF EXISTS srini_temp_trans;COMMIT;"
#     conn = psycopg2.connect("host=localhost dbname=postgres user=postgres")
#     cur = conn.cursor()
#     cur.execute(sql)
#     cur.close()


# df.to_sql('people', con=engine, if_exists='append', index=False, dtype={'First Name': String(length=255),
#                                                                         'Last Name': String(length=255),
#                                                                         'Age': SmallInteger, 'Phone Number': String(length=255)})

def load_data_from_csv_to_db(data):
    #print('in the get_data_from_csv')
    postgreSQLTable = 'ref_forms_scheds_format_specs'
    try:
        # Create an engine instance
        engine   = create_engine('postgres://postgres:postgres@localhost:5432', pool_recycle=3600);
        # Connect to PostgreSQL server
        postgreSQLConnection = engine.connect()
        #print("1111; ")
        data.to_sql(postgreSQLTable, postgreSQLConnection,  if_exists='append', index=False, dtype={'AUTO-GENERATE': Text} )
        #data.to_sql(postgreSQLTable, postgreSQLConnection,  if_exists='append', index=False, dtype={'AUTO-GENERATE': String(length=5)})

        time.sleep(1)
        #temp = engine.execute("SELECT * FROM srini_temp_trans").fetchall()
        #print("22222; ")
    except ValueError as vx:
        print("valuerror; ")
        print(vx)
    except Exception as ex:  
        print("In EXCEPTION BLOCK ")
        print(ex)
    finally:
        postgreSQLConnection.close();


def export_excel_to_db(filename, path):
    try:
        #dirname = os.path.dirname
        #print(dirname(dirname(os.getcwd())))
        
        #filelocation = dirname(dirname(os.getcwd()))+"/csv/Final_SPECS/F3X/Unique_code_new/"
        #filename = "F3X_ScheduleA_FormatSpecs_Import_Transactions_UNIQUE_CODE.xlsx"
        # Original file name to be renamed as above F3X - Schedule A_Format Specs_Import Transactions_MAPPED
        filelocation = path
        filewithpath = filelocation + filename
        print("File name",filewithpath)
        str = filename.split('_')
        formname  = str[0]
        schedname = str[1] 
        #print(dirname(dirname(os.getcwd()))+"/csv/Final_SPECS/F3X/F3X_ScheduleA_FormatSpecs_Import_Transactions_UNIQUE_CODE.xlsx") 
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
                load_data_from_csv_to_db(df)
                #break
    except Exception as ex:  
        print("In export_excel_to_db EXCEPTION BLOCK ")
        print(ex)

def rename_files_folder(filelocation):
    #filename = "F3X_ScheduleA_FormatSpecs_Import_Transactions_UNIQUE_CODE.xlsx"
    #F3X - Schedule A_Format Specs_Import Transactions_MAPPED
    with os.scandir(filelocation) as entries:
        for entry in entries:
            if ' - ' in entry.name:
                res = re.split(' |-|_|!', entry.name)
                print(res[4])
                filename = 'F3L_Schedule' + res[4] + '_FormatSpecs_Import_Transactions_MAPPED.xlsx'
                # print(filelocation+entry.name)
                # print(filelocation+filename)   
                os.rename(filelocation+entry.name,filelocation+filename)

def move_data_from_excel_to_db(form):
    try:
        filename = "F3X_ScheduleA_FormatSpecs_Import_Transactions_UNIQUE_CODE.xlsx"        
                
        dirname = os.path.dirname
        filelocation = dirname(dirname(os.getcwd()))+"/csv/Final_SPECS/F3L/unique_code_final/"
        if form == 'F3X':
            print('its F3X') 
            filelocation = dirname(dirname(os.getcwd()))+"/csv/Final_SPECS/F3X/unique_code_final/"
        filename = "F3X_ScheduleA_FormatSpecs_Import_Transactions_UNIQUE_CODE.xlsx"
        counter = 1
        rename_files_folder(filelocation)
        with os.scandir(filelocation) as entries:
            for entry in entries:
                print('counter',counter)
                print('........................Schedule File Name:',entry.name)
                
                export_excel_to_db(entry.name,filelocation)
                print('....................... End....',entry.name)
                counter+=1
    except Exception as ex:
        print(ex)


def schema_validation(dataframe, schema):
    try:
        #print(dataframe)
        errors = schema.validate(dataframe)
        for error in errors:
            # print('Lit of errors:',error)
            print('[',error.row,',',error.column,',',error.value,']')
        errors_index_rows = [e.row for e in errors]
        print('errors_index_rows: ',errors_index_rows)

        pd.DataFrame({'col':errors}).to_csv('errors.csv', mode='a', header=False)

        data_clean = dataframe.drop(index=errors_index_rows)
        data_dirty = pd.concat([data_clean, dataframe]).drop_duplicates(keep=False)
        data = {"errors": data_dirty, "data_clean": data_clean}
        #print("data:",data)
        return data
    except Exception as e:
        print(e)
        #logger.debug(e)
        #raise NoOPError("Error occurred while validating file structure. Please ensure header and data values are in "
                        #"proper format.")

def build_schemas(formname, sched, trans_type):
    # formname = 'F3X' 
    # sched    = 'ScheduleA'
    #trans_type = 'PARTN_MEMO'
    try:
        # query_string = """SELECT rfsfs.formname, rfsfs.schedname, rfsfs.transaction_type, rfsfs.field_description, rfsfs.TYPE, rfsfs.REQUIRED	
        #                     FROM public.ref_forms_scheds_format_specs rfsfs 
        #                     WHERE rfsfs.formname  = %s 
        #                     AND rfsfs.schedname = %s
        #                     AND rfsfs.transaction_type = %s"""
        connection = psycopg2.connect(user='postgres',
                                      password = 'postgres',
                                      host='localhost',
                                      port='5432',
                                      database='postgres'  )
        cursor = connection.cursor()
        print('formname',formname) 
        print('sched',sched) 
        print('trans_type',trans_type)
        cursor.execute("SELECT rfsfs.formname, rfsfs.schedname, rfsfs.transaction_type, rfsfs.field_description, rfsfs.type, rfsfs.required	FROM public.ref_forms_scheds_format_specs rfsfs WHERE rfsfs.formname  = %s AND rfsfs.schedname = %s AND rfsfs.transaction_type = %s and rfsfs.type IS NOT NULL",(formname, sched, trans_type)) 
        format_specs = cursor.fetchall()
        columns = []
        headers = []
        #print('format_specs',format_specs)
        for counter, row in enumerate(format_specs):
            #"A/N-3" "NUM-4"
            # Column('ZIP', [MatchesPatternValidation('^[\\w\\s]{1,9}$')]),
            # Column('EMPLOYER', [MatchesPatternValidation('^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,38}$')]),
            #print(row)
            field = row[3]
            type  = row[4]
            required = row[5]
            #print(field, type)
            s = type.split('-')
            #field = s[0] 
            len = s[1]
            #print(s[0],len)
            #print('required:',required)
            if 'A/N' in type:
                if required is None:
                    # print("in required is None")
                    # print(field)
                    pattern = '^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,' + len + '}$'
                    mpv = MatchesPatternValidation(pattern)
                    column = Column(field, [mpv],allow_empty=True)
                else:
                    #print("in ELSE required is None")
                    pattern = '^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,' + len + '}$'
                    mpv = MatchesPatternValidation(pattern)
                    column = Column(field, [mpv])
                columns.append(column)
                headers.append(field)
                #print(s[0],len)            
            elif 'NUM' in type:
                #pattern = '^[\\w\\s]{1,'+ len + '}$'
                pattern = '^[0-9]\d{0,'+ len + '}(\.\d{1,3})?%?$'
                mpv = MatchesPatternValidation(pattern)
                column = Column(field, [mpv])
                #print(s[0],len)            
                columns.append(column)
                headers.append(field)
            elif 'AMT' in type:
                pattern = '^-?\d\d*[,]?\d*[,]?\d*[.,]?\d*\d$' #'^((\d){1,3},*){1,5}\.(\d){2}$' #'^[\\w\\s]{1,'+ len + '}$'
                #pattern = '^[0-9]\d{0,'+ len + '}(\.\d{1,3})?%?$'
                mpv = MatchesPatternValidation(pattern)
                column = Column(field, [mpv])
                #print(s[0],len)            
                columns.append(column)
                headers.append(field)
            #print(field)
        # for col in columns:
        #     print(col.__dict__)
        schema = Schema(columns)
        head_schema = [headers,schema]
        return head_schema
    except Exception as e:
        raise e

def load_dataframe_from_s3(bktname, key, size, sleeptime):
    print(bktname, key)
    try:
        str = key.split('_')
        schedule  = str[1]
        formname = (str[0].split('/'))[1] 
        if 'H' in schedule or 'h' in schedule:
            sched = schedule.replace('Schedule','')
        else:
            sched = schedule.replace('Schedule','S')
        print('sched:',sched)
        print(schedule) 
        print(formname)        

        tablename = 'temp'
        if "/" in key:
            tablename=key[key.find("/")+1:-4].split()[0]
        else:
            raise Exception('S3 key not having a / char')
        tablename = tablename.lower() 
        print("tablename:", tablename)  
        s3 = boto3.client('s3')
        obj = s3.get_object(Bucket=bktname, Key=key)
        body = obj['Body']
        csv_string = body.read().decode('utf-8')
        res = ''
        for data in pd.read_csv(StringIO(csv_string), dtype=object,  iterator=True, chunksize=size): #, usecols=['ENTITY TYPE', 'CONTRIBUTOR STREET 1', 'TRANSACTION IDENTIFIER ']): 
            #load_data_from_df_to_db(tablename, data)
            print('read_csv For loop')
            data = data.dropna(axis=[0], how='all')
            #print(data)
            res = validate_dataframe(data, sched)
            if "Validate_Pass" != res:
                #print("load_dataframe_from_s3:",res)
               return res                        
            data = data.sort_values(by=["TRANSACTION IDENTIFIER"], ascending=False)
            print('...............')
            #loop through the data set to pick unique tranid's 
            print('Unique TRANSACTION IDENTIFIERS:',data['TRANSACTION IDENTIFIER'].unique().size)
            cntr = 1
            for tranid in data['TRANSACTION IDENTIFIER'].unique():
                print('.....................................................................................................................')
                print('.............tranid: ',tranid)
                print('***********CNTR:',cntr)
                cntr+=1
                #if tranid == 'TRAN':
                #    print('data',data)
                # build schema based on tranid
                head_schema = build_schemas(formname, schedule, tranid)
                print('After build_schemas')
                headers = head_schema[0]
                schema  = head_schema[1]
                print('....headers....',headers)
                print('....schema....',schema) 
                #pick the data with tranid based schema
                print('11111111111111111111111111')
                #print(data)
                #print(data['MEMO CODE'])
                data_temp = data[headers]
                #pick data with tranid 
                print('11111111111111111111111111')
                data_temp = data_temp.loc[(data['TRANSACTION IDENTIFIER'] == tranid)]
                #Validate data based on Schema and data
                print('11111111111111111111111111')
                schema_validation(data_temp, schema)
                print('After schema_validation')
                #break
                print('........END..............................................................................................')
            print('...............')
            #time.sleep(sleeptime)  
            return 'Validate_Pass'      
    except Exception as error:
        print(error)
        

#main method to call the process 
def validate_transactions(bktname, key):
    try:

        #send_message_to_queue()
        #aws sqs receive-message --queue-url https://queue.amazonaws.com/813218302951/fecfile-importtransactions --attribute-names All --message-attribute-names All --max-number-of-messages 10
        #aws sqs purge-queue --queue-url https://queue.amazonaws.com/813218302951/fecfile-importtransactions
        #bktname: "fecfile-filing-frontend"
        #key: "transactions/F3X_Specs_Import_Transactions_Srini.csv"
        #key = "transactions/F3X_Tempate_Schedule_Specs_Import_Transactions_Schedule_A_Srini.csv"
        
        # sched = 'SA'
        # bktname = "fecfile-filing-frontend"
        # key = "transactions/F3X_Tempate_Schedule_Specs_Import_Transactions_Schedule_A_Srini.csv"
        #key = "transactions/C00029447_SchedA_UI_Identifier.csv"

        print("bktname: ",bktname, ", Key : ", key)
        if bktname:
            res = load_dataframe_from_s3(bktname, key, 100000, 1) #100,000 records and 1s timer is for testing and need to be updated.
            if res != 'Validate_Pass':
                print("Error with data validation:", res)
        else:
            print("Queue is empty!!!")
    except Exception as ex:
        print(ex)
        logging.debug("error in process_transactions method")
        logging.debug(error)

try:
     bktname = "fecfile-filing-frontend"
     #key = "transactions/F3X_Tempate_Schedule_Specs_Import_Transactions_Schedule_A_Srini.csv"
     key = "transactions/F3X_ScheduleF_Import_Transactions_11_25_TEST_Data.csv"
     validate_transactions(bktname, key)

    #move_data_from_excel_to_db('F3X')    
except Exception as ex:
    print(ex)
