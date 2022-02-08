import os
import psycopg2
import pandas as pd
import boto3
from io import StringIO
from pandas.util import hash_pandas_object
import numpy
from psycopg2.extensions import register_adapter, AsIs
from django.conf import settings


def addapt_numpy_float64(numpy_float64):
    return AsIs(numpy_float64)


def addapt_numpy_int64(numpy_int64):
    return AsIs(numpy_int64)


register_adapter(numpy.float64, addapt_numpy_float64)
register_adapter(numpy.int64, addapt_numpy_int64)

SQS_QUEUE_NAME = os.getenv("SQS_QUEUE_NAME")


"""


CREATE TABLE public.transactions_file_details
(
  cmte_id 	character varying(9) NOT NULL,
  file_name 	character varying(200),
  md5 		character varying(100),
  create_date 	timestamp without time zone DEFAULT now()
)
"""

# check if file is new


def check_for_file_hash_in_db(cmteid, filename, hash, fecfilename):
    conn = None
    try:
        """insert a transactions_file_details"""
        selectsql = """
            SELECT cmte_id, md5, file_name, create_date
            FROM public.transactions_file_details
            WHERE cmte_id = %s AND file_name = %s AND md5 = %s AND fec_file_name = %s;
        """

        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()
        cur.execute(selectsql, (cmteid, filename, hash, fecfilename))
        dbhash = cur.fetchone()
        conn.commit()
        cur.close
        return dbhash
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


# load the filename with hashcode to db
def load_file_hash_to_db(cmteid, filename, hash, fecfilename):
    conn = None
    try:
        print("cmteid :", cmteid)
        print("filename :", filename)
        print("hash :", hash)
        print("fecfilename:", fecfilename)
        """ insert a transactions_file_details """
        insertsql = """INSERT INTO transactions_file_details(cmte_id, file_name, md5, fec_file_name)
                VALUES(%s, %s, %s, %s);"""

        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()
        cur.execute(insertsql, (cmteid, filename, hash, fecfilename))
        conn.commit()
        cur.close
        return "done"
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def generate_md5_hash(filename):
    print("generate_md5_hash")
    try:
        bucket = "fecfile-filing-frontend"
        # key = 'transactions/Disbursements_1q2020.csv'
        key = "transactions/" + filename  # srini_test1.csv
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj["Body"]
        # print(body)
        csv_string = body.read().decode("utf-8")
        # print(csv_string)
        # i=0
        for data in pd.read_csv(
            StringIO(csv_string), dtype=object, iterator=True, chunksize=200000
        ):
            # print(i)
            # i+=1
            filehash = hash_pandas_object(data).sum()
        filehash = str(filehash)
        print(filehash)
        return filehash
    except Exception as ex:
        print(ex)


"""

@api_view(["POST"])
def file_verify_upload(request):
    try:
        if request.method == 'POST':
            cmte_id = get_comittee_id(request.user.username)
            file_name = request.data.get("fileName")

            client = boto3.client('s3',
                                    settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY
                                    )
            bucket = AWS_STORAGE_IMPORT_CONTACT_BUCKET_NAME
            file_name = request.data.get("fileName")
            csv_obj = client.get_object(Bucket=bucket, Key=file_name)
            hashlib.sha1(pd.util.hash_pandas_object(df).values).hexdigest()

            #filepath = dirname(dirname(os.getcwd()))+"/csv/"
            filename = "Disbursements_1q2020.csv"
            hash_value = generate_md5_hash(filepath+filename)
            fileexists = check_for_file_hash_in_db('C00000018', filename, hash_value)
            if fileexists is None:
                load_file_hash_to_db('C00000018', filename, hash_value)
                print('File loaded successfully!!!')
            else:
                print('File exists in DB')

            return JsonResponse(contacts, status=status.HTTP_201_CREATED, safe=False)

    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)


"""


def get_comittee_id(username):
    cmte_id = ""
    if len(username) > 9:
        cmte_id = username[0:9]

    return cmte_id


def chk_csv_uploaded(request):
    try:
        cmte_id = get_comittee_id(request.user.username)
        file_name = request.data.get("file_name")  # request.file_name
        md5 = request.data.get("md5hash")  # request.md5hash
        fec_file_name = request.data.get("fecfilename")
        print(cmte_id, file_name, md5, fec_file_name)
        filename = file_name  # "srini_test1.csv"#"Disbursements_1q2020.csv"
        hash_value = md5  # generate_md5_hash(filename)
        fecfilename = fec_file_name  # "F3X_ScheduleLA_Import_Transactions_C0011147_part1_11_25.csv"
        fileexists = check_for_file_hash_in_db(
            cmte_id, filename, hash_value, fecfilename
        )
        if fileexists is None:
            load_file_hash_to_db(cmte_id, filename, hash_value, fecfilename)

        rcmteid = ""
        rhash = ""
        rfilename = ""
        rcreate_date = ""
        if fileexists is not None:
            rcmteid = fileexists[0]
            rhash = fileexists[1]
            rfilename = fileexists[2]
            rcreate_date = fileexists[3].strftime("%Y-%m-%d %H:%M:%S")
            returnstr = {
                "error_list": [],
                "fileName": filename,
                "duplicate_file_list": [
                    {
                        "fileName": rfilename,
                        "uploadDate": rcreate_date,
                        "checkSum": rhash,
                    }
                ],
                "duplicate_db_count": 0,
            }
        else:
            returnstr = {
                "error_list": [],
                "fileName": filename,
                "duplicate_file_list": [],
                "duplicate_db_count": 0,
            }
        return returnstr
    except Exception as e:
        returnstr = {"message": str(e)}
        print(returnstr)
        raise
