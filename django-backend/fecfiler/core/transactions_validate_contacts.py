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
        if 'schedulea' in filename:
            columnlist=['CAND_OFFICE','CAND_OFFICE_STATE','CAND_OFFICE_DISTRICT']
            print('schedulea')     
        elif 'scheduleb' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('scheduleb')     
        elif 'schedulee' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('schedulee')     
        elif 'schedulef' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('schedulef')     
        elif 'schedulelb' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('schedulelb')     
        elif 'scheduleh4' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('scheduleh4')     
        elif 'scheduleh6' in filename:
            columnlist=['EMPLOYER','OCCUPATION']
            print('scheduleh6')     
        else:
            print('In F3X get_columns_to_add, Sched type not available!!!')
    elif 'f3l' in filename:
        if 'schedulea' in filename: 
            columnlist=['OCCUPATION']               
        elif 'scheduleb' in filename: 
            columnlist=['EMPLOYER','OCCUPATION']               
        else:
            print('In F3L get_columns_to_add, Sched type not available!!!')
    return columnlist
    
#mapping columns for each schedule against the contacts API req.
def get_columns_for_schedules(filename):
    columnlist=[]
    if 'f3x' in filename:

        #SA: COMMITTEE ID', 6,13,14,15,16,17,23,24,7,8,9,10,11,12, 'CAND_OFFICE', 'CAND_OFFICE_STATE','CAND_OFFICE_DISTRICT',25,4

        if 'schedulea' in filename:
            #columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16,22,23]
            columnlist=[6,13,14,15,16,17,23,24,7,8,9,10,11,12,25,4]
            print('schedulea')
        elif 'scheduleb' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16]
            print('scheduleb')     
        elif 'schedulee' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16]
            print('schedulee')     
        elif 'schedulef' in filename:
            columnlist=[3,15,16,17,18,19,20,21,22,23,24,25,26]
            print('schedulef')     
        elif 'schedulela' in filename:
            columnlist=[3,6,7,8,9,10,11,12,13,14,15,16,17,21,22]
            print('schedulela')     
        elif 'schedulelb' in filename:
            columnlist=[3,6,7,8,9,10,11,12,13,14,15,16,17]
            print('schedulelb')     
        elif 'scheduleh4' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16]
            print('scheduleh4')     
        elif 'scheduleh6' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16]
            print('scheduleh6')     
        else:
            print('In F3X, Sched type not available!!!')
    elif 'f3l' in filename:
        if 'schedulea' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16,19]
            print('f3l schedulea')     
        elif 'scheduleb' in filename:
            columnlist=[3,5,6,7,8,9,10,11,12,13,14,15,16] 
            print('f3l scheduleb')     
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
        chkf = False
        for data in pd.read_csv(StringIO(csv_string), dtype=object, index_col=False, iterator=True, chunksize=size, usecols=col_to_read):
            col_names = ['ENTITY TYPE',
                        'CONTRIBUTOR STREET  1',
                        'CONTRIBUTOR STREET  2',
                        'CONTRIBUTOR CITY',
                        'CONTRIBUTOR STATE',
                        'CONTRIBUTOR ZIP',
                        'CONTRIBUTOR EMPLOYER',
                        'CONTRIBUTOR OCCUPATION',
                        'CONTRIBUTOR ORGANIZATION NAME',
                        'CONTRIBUTOR LAST NAME',
                        'CONTRIBUTOR FIRST NAME',
                        'CONTRIBUTOR MIDDLE NAME',
                        'CONTRIBUTOR PREFIX',
                        'CONTRIBUTOR SUFFIX',
                        'DONOR COMMITTEE FEC ID',
                        'TRANSACTION IDENTIFIER']
            data = data.reindex(columns = col_names)            
            #data = data[col_to_read] 
            if col_to_add:
                for x in col_to_add:
                    data[x] = ''
            data['COMMITTEE_ID'] = cmteid
            
            data.columns = [ 'ENTITY_TYPE', 'STREET_1',
                            'STREET_2', 'CITY', 'STATE', 'ZIP_CODE', 'EMPLOYER',
                            'OCCUPATION',
                            'ORGANIZATION_NAME', 'LAST_NAME', 'FIRST_NAME',
                            'MIDDLE_NAME', 'PREFIX', 'SUFFIX', 'REF_CAND_CMTE_ID', 'TRANSACTION_ID',
                            'CAND_OFFICE', 'CAND_OFFICE_STATE','CAND_OFFICE_DISTRICT','COMMITTEE_ID']



            csv_buffer = StringIO()
            data.to_csv(csv_buffer,index=False)
            s3_resource.Object(bktname, filepath).put(Body=csv_buffer.getvalue())
            chkf = True
            #time.sleep(sleeptime)
        if chkf:
            return filepath.split('/')[1]       
    except Exception as e:
        print('error in load_dataframe_from_s3:',e)
        logging.debug(e)

#main method to call the process 
def get_contact_details_from_transactions(cmteid, filename):
    try:
        cmteid = cmteid[0:9]        
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
                return load_dataframe_from_s3(cmteid,bucket, key , 100000, 1) #100,000 records and 1s timer is for testing and need to be updated.
            else:
                print("Queue is empty!!!")
        else:
            logging.debug('Not a CSV file!!!')
            return 'Not a CSV file!!!'
    except Exception as e:
        logging.debug(e)
        return e

# get_contact_details_from_transactions('C00111476', 'F3X_ScheduleA_Import_Transactions_11_25_TEST_Data.csv')