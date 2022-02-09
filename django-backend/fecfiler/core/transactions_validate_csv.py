import os
import os.path
from os import path
import psycopg2
import pandas as pd
from pandas_schema import Column, Schema
from pandas_schema.validation import MatchesPatternValidation
import boto3
from botocore.exceptions import ClientError
from io import StringIO
import logging
import time
import re
from sqlalchemy import create_engine
from sqlalchemy.types import Text
from django.conf import settings

PG_PASSWORD = os.getenv("FECFILE_DB_PASSWORD", "postgres")
SQS_QUEUE_NAME = os.getenv("SQS_QUEUE_NAME")

BACKEND_DB_HOST = os.getenv("BACKEND_DB_HOST")
BACKEND_DB_PORT = os.getenv("BACKEND_DB_PORT")
BACKEND_DB_NAME = os.getenv("BACKEND_DB_NAME")
BACKEND_DB_USERNAME = os.getenv("BACKEND_DB_USERNAME")
BACKEND_DB_PASSWORD = os.getenv("BACKEND_DB_PASSWORD")


# Setting the logging level
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.ERROR)


def validate_dataframe(data):
    # check if the column contains only values of a particular schedule
    sched = data["SCHEDULE NAME"][0][0:2]
    if data["SCHEDULE NAME"].str.contains(sched).any():
        print("schedule matches")
        return "Validate_Pass"
    else:
        print("Non schedule matches available")
        return "Multiple_Sched"


def save_data_from_excel_to_db(data):
    postgreSQLTable = "ref_forms_scheds_format_specs"
    try:
        # "postgres://PG_USER:PG_PASSWORD@PG_HOST:PG_PORT/PG_DATABASE"
        connectionstring = settings.DATABASE_URL
        engine = create_engine(connectionstring, pool_recycle=3600)
        postgreSQLConnection = engine.connect()
        data.to_sql(
            postgreSQLTable,
            postgreSQLConnection,
            if_exists="append",
            index=False,
            dtype={"AUTO-GENERATE": Text},
        )
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
        print("File name", filewithpath)
        str = filename.split("_")
        formname = str[0]
        schedname = str[1]
        xls = pd.ExcelFile(filewithpath)
        res = len(xls.sheet_names)
        sheet_to_start = 1
        if res == 1:
            sheet_to_start = 0
        # print(xls.sheet_names)
        for sheet_name in xls.sheet_names[sheet_to_start:]:
            print(sheet_name)
            if sheet_name != "All Receipts":
                df = pd.read_excel(
                    filewithpath,
                    sheet_name=sheet_name,
                    index_col=0,
                    skiprows=range(0, 2),
                    # dtype=String,
                    usecols="A,B,C,D,E,F,G",
                )
                df.dropna(how="all", inplace=True)
                df.rename(
                    columns={
                        "Auto populate ": "AUTO-GENERATE",
                        "Auto populate": "AUTO-GENERATE",
                        "FIELD DESCRIPTION": "FIELD\nDESCRIPTION",
                        "SAMPLE DATA": "SAMPLE\nDATA",
                        "VALUE REFERENCE": "VALUE\nREFERENCE",
                    },
                    inplace=True,
                )
                df.insert(0, "formname", formname)
                df.insert(1, "schedname", schedname)
                df.insert(2, "transaction_type", sheet_name)
                save_data_from_excel_to_db(df)
                # break
    except Exception as ex:
        print("In export_excel_to_db EXCEPTION BLOCK ")
        print(ex)


def rename_files_folder(filelocation):
    with os.scandir(filelocation) as entries:
        for entry in entries:
            if " - " in entry.name:
                res = re.split(" |-|_|!", entry.name)
                filename = (
                    "F3L_Schedule"
                    + res[4]
                    + "_FormatSpecs_Import_Transactions_MAPPED.xlsx"
                )
                os.rename(filelocation + entry.name, filelocation + filename)


def move_data_from_excel_to_db(form):
    try:
        dirname = os.path.dirname
        filelocation = (
            dirname(dirname(os.getcwd())) + "/csv/Final_SPECS/F3L/unique_code_final/"
        )
        if form == "F3X":
            filelocation = (
                dirname(dirname(os.getcwd()))
                + "/csv/Final_SPECS/F3X/unique_code_final/"
            )
        counter = 1
        rename_files_folder(filelocation)
        with os.scandir(filelocation) as entries:
            for entry in entries:
                export_excel_to_db(entry.name, filelocation)
                counter += 1
    except Exception as ex:
        print(ex)


def schema_validation(dataframe, schema, bktname, key, errorfilename):
    try:
        errors = schema.validate(dataframe)
        errdf = []
        for error in errors:
            msg = error.message
            error.message = re.sub('["@*&?].*["@*&?]', "", msg)
            errdf.append(
                {"row_no": error.row, "field_name": error.column, "msg": error.message}
            )

        errors_index_rows = [e.row for e in errors]
        if len(errors_index_rows) > 0:
            if path.exists(errorfilename):
                pd.DataFrame(errdf, columns=["row_no", "field_name", "msg"]).to_csv(
                    errorfilename, mode="a", header=False, index=False
                )
            else:
                pd.DataFrame(errdf, columns=["row_no", "field_name", "msg"]).to_csv(
                    errorfilename, mode="a", header=True, index=False
                )

        data_clean = dataframe.drop(index=errors_index_rows)
        data_dirty = pd.concat([data_clean, dataframe]).drop_duplicates(keep=False)
        data = {"errors": data_dirty, "data_clean": data_clean}
        # print('data_dirty:',data_dirty)
        return data
    except ClientError as e:
        print("ClientError Exception in schema_validation:", e)
        logging.debug("error in schema_validation method")
        logging.debug(e)
        raise
    except Exception as e:
        print("Exception Regular in schema_validation:", e)
        logging.debug("error in schema_validation method")
        logging.debug(e)
        raise


def build_schemas(formname, sched, trans_type):
    try:
        connection = psycopg2.connect(settings.DATABASE_URL)
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT rfsfs.formname, rfsfs.schedname, rfsfs.transaction_type,
            rfsfs.field_description, rfsfs.type, rfsfs.required
            FROM public.ref_forms_scheds_format_specs rfsfs
            WHERE rfsfs.formname  = %s AND rfsfs.schedname = %s
            AND rfsfs.transaction_type = %s and rfsfs.type IS NOT NULL
            """,
            (formname, sched, trans_type),
        )
        format_specs = cursor.fetchall()
        columns = []
        headers = []
        for counter, row in enumerate(format_specs):
            field = row[3]
            type = row[4]
            required = row[5]
            s = type.split("-")
            len = s[1]
            if "A/N" in type:
                if required is None:
                    pattern = r"""^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,' + len + '}$"""
                    mpv = MatchesPatternValidation(pattern)
                    column = Column(field, [mpv], allow_empty=True)
                else:
                    if field in [
                        "REPORT TYPE",
                        "REPORT YEAR",
                        "SCHEDULE NAME",
                        "TRANSACTION IDENTIFIER",
                        "TRANSACTION NUMBER",
                        "ENTITY TYPE",
                    ]:
                        pattern = "^(\\S)+[A-Za-z0-9_-]{1," + len + "}$"
                    else:
                        pattern = (
                            r"""^[-@.\/#&+*%:;=?!=.-^*()\'%!\\w\\s]{1,' + len + '}$"""
                        )
                    mpv = MatchesPatternValidation(pattern)
                    column = Column(field, [mpv], allow_empty=False)
                columns.append(column)
                headers.append(field)
            elif "NUM" in type:
                pattern = r"""^[0-9]\d{0,' + len + '}(\.\d{1,3})?%?$"""
                mpv = MatchesPatternValidation(pattern)
                column = Column(field, [mpv])
                columns.append(column)
                headers.append(field)
            elif "AMT" in type:
                pattern = r"""^[0-9]\d{0,' + len + '}(\.\d{1,3})?%?$"""
                mpv = MatchesPatternValidation(pattern)
                column = Column(field, [mpv])
                columns.append(column)
                headers.append(field)
        schema = Schema(columns)
        head_schema = [headers, schema]
        return head_schema
    except ValueError as vx:
        print("valuerror; ")
        print("Exception in build_schemas:", vx)
    except Exception as ex:
        print("In EXCEPTION BLOCK ")
        print("Exception in build_schemas:", ex)
    finally:
        connection.close()


def check_errkey_exists(bktname, key):
    errkey = key.split("/")
    print()
    errkey = errkey[0] + "/error_files/" + errkey[1]
    s3 = boto3.client("s3")
    result = s3.list_objects(Bucket=bktname, Prefix=errkey)
    if "Contents" not in result:
        s3.put_object(Bucket=bktname, Key=(errkey + "/"))


def create_cmte_error_folder(bktname, key, errfilerelpath):
    s3 = boto3.client("s3")
    result = s3.list_objects(Bucket=bktname, Prefix=errfilerelpath)
    if "Contents" not in result:
        s3.put_object(Bucket=bktname, Key=(errfilerelpath + "/"))


def move_error_files_to_s3(bktname, key, errorfilename, cmteid):
    try:
        keyfolder = key.split("/")[0]
        cmte_err_folder = keyfolder + "/error_files/" + cmteid

        create_cmte_error_folder(bktname, key, cmte_err_folder)
        errfilerelpath = keyfolder + "/error_files/" + cmteid + "/" + errorfilename
        s3 = boto3.resource("s3")
        s3.Bucket(bktname).upload_file(errorfilename, errfilerelpath)
        os.remove(errorfilename)
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
    errorfilename = ""
    try:
        str = key.split("_")
        schedule = str[1]
        formname = (str[0].split("/"))[1]
        tablename = "temp"
        if "/" in key:
            tablename = key[key.find("/") + 1: -4].split()[0]
        else:
            raise Exception("S3 key not having a / char")
        tablename = tablename.lower()
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=bktname, Key=key)
        body = obj["Body"]
        csv_string = body.read().decode("utf-8")
        res = ""
        flag = False
        for data in pd.read_csv(
            StringIO(csv_string),
            dtype=object,
            iterator=True,
            chunksize=size,
            na_filter=False,
        ):
            data = data.dropna(axis=[0], how="all")
            res = validate_dataframe(data)
            if "Validate_Pass" != res:
                return res
            data = data.sort_values(by=["TRANSACTION IDENTIFIER"], ascending=False)
            cntr = 1
            for tranid in data["TRANSACTION IDENTIFIER"].unique():
                if tranid:
                    cntr += 1
                    head_schema = build_schemas(formname, schedule, tranid)
                    headers = head_schema[0]

                    data_temp = data[headers]
                    data_temp = data_temp.loc[
                        (data["TRANSACTION IDENTIFIER"] == tranid)
                    ]
                    errorfilename = (
                        re.match(r"(.*)\.csv", key).group(1).split("/")[1]
                        + "_error.csv"
                    )

            flag = True
        if path.exists(errorfilename):
            errfilerelpath = move_error_files_to_s3(bktname, key, errorfilename, cmteid)
            return errfilerelpath
        elif flag is True:
            return "Validate_Pass"
        else:
            return "Validate_Fail"
    except ClientError as e:
        print("Exception in load_dataframe_from_s3:", e)
        logging.debug("error in load_dataframe_from_s3 method")
        logging.debug(e)
        raise
    except Exception as e:
        print("Exception in load_dataframe_from_s3:", e)
        logging.debug("error in load_dataframe_from_s3 method")
        logging.debug(e)
        raise


# main method to call the process
def validate_transactions(bktname, key, cmteid):
    try:
        # send_message_to_queue()
        # aws sqs receive-message --queue-url $QUEUE_URL --attribute-names All /
        #  --message-attribute-names All --max-number-of-messages 10
        # aws sqs purge-queue --queue-url $QUEUE_URL
        returnstr = "File_not_found"
        check_errkey_exists(bktname, key)
        if check_file_exists(bktname, key):
            if bktname and key:
                res = load_dataframe_from_s3(
                    bktname, key, 100000, 1, cmteid
                )  # 100,000 records and 1s timer is for testing and need to be updated.
                if res != "Validate_Pass":
                    print("Error with data validation:", res)
                    returnstr = res
                else:
                    print(
                        "~~~~~Parsing Success!!! Error Queue is empty!!!~~~~"
                    )

            if returnstr != "File_not_found":
                print(returnstr.split("/"))

            returnstr = {
                "errorfilename": returnstr,
                "bktname": bktname,
                "key": key,
            }

            return returnstr
    except Exception as ex:
        print(ex)
        logging.debug("error in process_transactions method")
        returnstr = {
            "errorfilename": "File_not_found",
            "bktname": bktname,
            "key": key,
        }
        print(returnstr)
        return returnstr


def check_file_exists(bktname, key):
    s3 = boto3.client("s3")
    try:
        s3.head_object(Bucket=bktname, Key=key)
        return True
    except ClientError:
        # Not found
        raise


def check_data_processed(md5, fecfilename):
    conn = None
    try:
        res = ""
        selectsql = """
            SELECT csv_data_processed FROM public.transactions_file_details tfd
            WHERE tfd.fec_file_name = %s
            ORDER BY create_Date DESC   limit 1;
        """
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()
        cur.execute(selectsql, (fecfilename,))
        if cur.rowcount == 1:
            res = cur.fetchone()
        conn.commit()
        cur.close
        if "True" == res[0]:
            return "Success"
        else:
            return "Failure"
    except (Exception, psycopg2.DatabaseError) as error:
        print("database error check_data_processed")
        print(error)
        logging.debug(error)
    except Exception as ex:
        print("error in check_data_processed:", ex)
        logging.debug("error in check_data_processed method")
        logging.debug(ex)
    finally:
        if conn is not None:
            conn.close()


def load_transactions_from_temp_perm_tables(fecfilename):
    conn = None
    try:
        res = ""
        selectsql = """import_schedules"""
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()
        cur.callproc(selectsql, (fecfilename,))
        if cur.rowcount == 1:
            res = cur.fetchone()
        conn.commit()
        cur.close
        print(res[0])
        if 0 == res[0]:
            return "Success"
        else:
            return "Failure"
    except (Exception, psycopg2.DatabaseError) as error:
        print("database error load_transactions_from_temp_perm_tables")
        print(error)
        logging.debug(error)
    except Exception as ex:
        print("error in load_transactions_from_temp_perm_tables:", ex)
        logging.debug("error in load_transactions_from_temp_perm_tables method")
        logging.debug(ex)
    finally:
        if conn is not None:
            conn.close()


def send_message_to_queue(bktname, key):
    returnstr = ""
    try:
        # Get the service resource
        sqs = boto3.resource("sqs")
        # Get the queue. This returns an SQS.Queue instance
        queue = sqs.get_queue_by_name(QueueName=SQS_QUEUE_NAME)
        # You can now access identifiers and attributes
        # print('URL:',queue.url)
        # print(queue.attributes.get('DelaySeconds'))
        returnstr = {
            "sendmessage": "Fail",
            "bktname": bktname,
            "key": key,
        }
        response = queue.send_messages(
            Entries=[
                {
                    "Id": "1",
                    "MessageBody": "ImportTransactions",
                    "MessageAttributes": {
                        "bktname": {
                            "DataType": "String",
                            "StringValue": bktname,  # "fecfile-filing-frontend"
                        },
                        "key": {
                            "DataType": "String",
                            "StringValue": key,  # "transactions/F3X_ScheduleA_Import_Transactions_11_25_TEST_Data.csv"
                        },
                    },
                }
            ]
        )
        if response.get("Successful"):
            if response.get("Successful")[0].get("Id"):
                start_time = time.time()
                seconds = 60 * 3
                while True:
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    if "Success" == check_data_processed("", key.split("/")[1]):
                        temp_to_perm = load_transactions_from_temp_perm_tables(
                            key.split("/")[1]
                        )
                        res = "Fail"
                        if 0 == temp_to_perm:
                            res = "Success"
                            returnstr = {
                                "sendmessage": res,
                                "bktname": bktname,
                                "key": key,
                            }
                        break
                    # time.sleep(5)
                    if elapsed_time > seconds:
                        print(
                            "Finished iterating in: "
                            + str(int(elapsed_time))
                            + " seconds"
                        )
                        break

        return returnstr
    except Exception as ex:
        print(ex)
        logging.debug("error in send_message_to_queue method")
        returnstr = {
            "sendmessage": "Fail",
            "bktname": bktname,
            "key": key,
            "error": ex,
        }
        return returnstr


# cmteid =  "C00011111"
# bktname = "fecfile-filing-frontend"
# # key = "transactions/F3X_ScheduleE_Import_Transactions_11_25_TEST_Data.csv"
# #key =  "transactions/F3X_ScheduleA_Import_Transactions_C00515064.csv"
# if bktname and key:
#     print(validate_transactions(bktname, key, cmteid))
# else:
#     print("No data")

# move_data_from_excel_to_db('F3X')
# move_data_from_excel_to_db('F3L')


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

# code to send and receive mesg from queues
# try:
#     # SQS_QUEUE_NAME = 'fecfile-importtransactions'
#     # SQS_QUEUE_ARN  = 'arn:aws:sqs:us-east-1:813218302951:fecfile-importtransactions'
#     # SQS_QUEUE_URL  = 'https://queue.amazonaws.com/813218302951/fecfile-importtransactions'
#     bktname = "fecfile-filing-frontend"
#     key = "transactions/F3X_ScheduleA_Import_Transactions_11_25_TEST_Data.csv"
#     #if SQS_QUEUE_NAME is None:
#         #SQS_QUEUE_NAME = 'fecfile-importtransactions'
#     #print('SQS_QUEUE_NAME =',SQS_QUEUE_NAME)
#     print('FECFILE QUEUE :',os.environ.get('SQS_QUEUE_NAME'))
#     print(send_message_to_queue(bktname, key))
#     #get_message_from_queue()
# except Exception as ex:
#     print(ex)
