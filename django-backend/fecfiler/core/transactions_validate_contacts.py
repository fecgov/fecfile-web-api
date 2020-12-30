import hashlib
import os
import psycopg2
import pandas as pd 
import boto3
from pandas.util import hash_pandas_object
import numpy
from psycopg2.extensions import register_adapter, AsIs
import logging
import time
from io import StringIO
from django.conf import settings
from fecfiler.settings import AWS_STORAGE_IMPORT_CONTACT_BUCKET_NAME

logger = logging.getLogger(__name__)

# Setting the logging level
logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.ERROR)

#mapping null columns for the contacts API 
def get_columns_to_add(filename):
    columnlist=[]
    filename = filename.lower()
    if 'f3x' in filename:
        if 'schedule_b' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('schedule_b')     
        elif 'schedule_e' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('schedule_e')     
        elif 'schedule_f' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('schedule_f')     
        elif 'schedule_lb' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('schedule_lb')     
        elif 'schedule_h4' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('schedule_h4')     
        elif 'schedule_h6' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('schedule_h6')     
        else:
            print('In F3X get_columns_to_add, Sched type not available!!!')
    elif 'f3l' in filename:
        if 'schedule_a' in filename: 
            columnlist=['OCCUPATION']               
        elif 'schedule_b' in filename: 
            columnlist=['EMPLOYER','OCCUPATION']               
        else:
            print('In F3L get_columns_to_add, Sched type not available!!!')
    return columnlist

#mapping columns for each schedule against the contacts API req.
def get_columns_for_schedules(filename):
    columnlist=[]
    if 'f3x' in filename:
        if 'schedule_a' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16,22,23]
            print('schedule_a')
        elif 'schedule_b' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16]
            print('schedule_b')     
        elif 'schedule_e' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16]
            print('schedule_e')     
        elif 'schedule_f' in filename:
            columnlist=[3,15,16,17,18,19,20,21,22,23,24,25,26]
            print('schedule_f')     
        elif 'schedule_la' in filename:
            columnlist=[3,6,7,8,9,10,11,12,13,14,15,16,17,21,22]
            print('schedule_la')     
        elif 'schedule_lb' in filename:
            columnlist=[3,6,7,8,9,10,11,12,13,14,15,16,17]
            print('schedule_lb')     
        elif 'schedule_h4' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16]
            print('schedule_h4')     
        elif 'schedule_h6' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16]
            print('schedule_h6')     
        else:
            print('In F3X, Sched type not available!!!')
    elif 'f3l' in filename:
        if 'schedule_a' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16,19]
            print('f3l schedule_a')     
        elif 'schedule_b' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16] 
            print('f3l schedule_b')     
        else:
            print('In F3L, Sched type not available!!!')
    return columnlist

def load_dataframe_from_s3(cmteid, bktname, key, size, sleeptime):
    print(bktname, key)
    try:
        filename = 'temp' 
        if "/" in key:
            filename=key[key.find("/")+1:-4].split()[0]
        else:
            raise Exception('S3 key not having a / char')
        filename = filename.lower() 
        s3 = boto3.client('s3')
        s3_resource = boto3.resource('s3')
        obj = s3.get_object(Bucket=bktname, Key=key)
        body = obj['Body']
        csv_string = body.read().decode('utf-8')
        filepath = 'contacts/' + cmteid + '_' + filename +'.csv' 
        col_to_read = get_columns_for_schedules(filename)
        col_to_add  = get_columns_to_add(filename)

        for data in pd.read_csv(StringIO(csv_string), dtype=object,  iterator=True, chunksize=size, usecols=col_to_read): 
            data['COMMITTEE_ID'] = cmteid
            if col_to_add:
                for x in col_to_add:
                    data[x] = ''
            csv_buffer = StringIO()
            data.to_csv(csv_buffer,index=False)
            s3_resource.Object(bktname, filepath).put(Body=csv_buffer.getvalue())
            time.sleep(sleeptime)        
    except Exception as e:
        logging.debug(e)

#main method to call the process 
def get_contact_details_from_transactions(cmteid, filename):
    try:
        cmteid = cmteid[0:8]        
        client = boto3.client('s3',
                                settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY
                                )
        bucket = AWS_STORAGE_IMPORT_CONTACT_BUCKET_NAME
        file_name = filename
        if '.csv' in filename:
            #cmte_id C00111476mkancherla.ctr@fec.gov , bucket:  fecfile-filing-frontend , file_name :  Disbursements_1q2020.csv
            if bucket:
                print(bucket)
                key = "transactions/" + file_name
                load_dataframe_from_s3(cmteid,bucket, key , 100000, 1) #100,000 records and 1s timer is for testing and need to be updated.
            else:
                print("Queue is empty!!!")
        else:
            logging.debug('Not a CSV file!!!')
            return 'Not a CSV file!!!'
    except Exception as e:
        logging.debug(e)
        return e
