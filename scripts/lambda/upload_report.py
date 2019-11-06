import psycopg2
import requests
import os
import datetime
from collections import OrderedDict
import json

# Global Variables
_conn = None
_NEXGEN_DJANGO_API_URL = os.environ.get("NEXGEN_DJANGO_API_URL", "127.0.0.1:8000")
_NEXGEN_DJANGO_API_URL = _NEXGEN_DJANGO_API_URL + "/api/v1"
# _NEXGEN_DJANGO_API_URL=settings.DATA_RECEIVE_API_URL

# replace off 4 DB parameters with environment variables
_host = os.environ.get("DB_HOST", "localhost")
_database = os.environ.get("DB_NAME", "fecfrontend2")
_user = os.environ.get("DB_USER", "fecuser2")
_password = os.environ.get("DB_PASSWD", "postgres")


'''
message_type,
 1-FATAL, 2-ERROR, 3-WARN, 4-INFO, 5-DEBUG, 6-TRACE
'''
def add_log(reportid, 
            cmte_id, 
            message_type, 
            message_text, 
            response_json, 
            error_code, 
            error_json, 
            app_error,
            host_name=os.uname()[1],
            process_name="upload_report"):
                     
    cur = _conn.cursor()
    cur.execute("""INSERT INTO public.upload_logs(
                                    report_id, 
                                    cmte_id, 
                                    process_name, 
                                    message_type, 
                                    message_text, 
                                    response_json, 
                                    error_code, 
                                    error_json, 
                                    app_error, 
                                    host_name)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                    [reportid, cmte_id, process_name, message_type, message_text, response_json, error_code, error_json, app_error, host_name])
    _conn.commit()
    
def get_reports_to_upload():
    """ query data from the vendors table """
    try:

        print("get_reports_to_upload accessing ...")
        # Get API token
        

        #replace username and password from actual user
        cmte_id = 'C00000422'
        data_obj = {
                    'username':cmte_id,
                    'password':'test'
                 }

        # Get the token to access API  
        resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                 "/token/obtain", data=data_obj)
        if resp.ok:
            successresp=resp.json()
            print("token/obtain API call is successfuly finished...")  
            print(successresp)
            token=successresp['token']
            print(token)

            add_log(0,
                cmte_id, 
                4,
                " get_reports_to_upload get token API operation successful", 
                json.dumps(successresp), 
                '',
                '', 
                '' 
                ) 

            headers_obj = {
                        'Authorization':'JWT '+ token,
                        }
            cur = _conn.cursor()

            #Processing F3X reports
            # pick reports with status = Uploaded
            
            cur.execute("""SELECT cmte_id, report_id, form_type 
                        FROM   public.reports 
                        WHERE  status = 'Uploaded' 
                        ORDER BY last_update_date asc""")

            '''
            cur.execute("""SELECT cmte_id, report_id, form_type 
                        FROM   public.reports 
                        WHERE  status = 'Saved' 
                        AND  report_id in (1410, 1414, 1426)    
                        ORDER BY last_update_date asc""")
            '''

            for row in cur.fetchall():
                data_row = list(row)
                data_obj=data_row[0]
               
                cur.execute("""UPDATE public.reports 
                            SET status = 'Upload_Waiting' 
                            WHERE cmte_id = %s 
                            AND report_id = %s 
                            AND status = 'Uploaded' """, [data_row[0],  data_row[1]])
                '''
                cur.execute("""UPDATE public.reports 
                            SET status = 'Upload_Waiting' 
                            WHERE cmte_id = %s 
                            AND report_id = %s 
                            AND status = 'Saved' """, [data_row[0],  data_row[1]])      
                '''                                  
                _conn.commit()

                data_obj = {
                        'cmte_id':data_row[0],
                        'report_id':data_row[1],
                        'call_from':'Submit'
                    }

                add_log(data_row[1],
                    data_row[0],  
                    4,
                    "F3X prepare_json_builders_data call",
                     '', 
                    '',
                    '', 
                    '', 
                    )     
                # call prepare_json_builders_data API to prepare Data for JSON  
                resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                    "/core/prepare_json_builders_data", data=data_obj, headers=headers_obj)

                add_log(data_row[1],
                    data_row[0],  
                    4,
                    "F3X prepare_json_builders_data after the call",
                    json.dumps(resp.json()),
                    '',
                    '', 
                    '', 
                    )     
                successresp=resp.json()
                if successresp["Response"] =='Success':
                    successresp=resp.json()

                    print("prepare_json_builders_data call is successfuly finished...")  

                    add_log(data_row[1],
                                        data_row[0],  
                                        4,
                                        "prepare_json_builders_data call is successfuly finished ", 
                                        '', 
                                        '',
                                        '', 
                                        '', 
                                    )  

                    print(successresp)
                    if successresp["Response"] =='Success':
                        # call create_json_builders which internally call Data Reciever API

                        data_obj = {
                                    'committeeId':data_row[0],
                                    'report_id':data_row[1],
                                    'call_from':'Submit'
                                   }

                        add_log(data_row[1],
                                        data_row[0],  
                                        4,
                                        "F3X create_json_builders call with data_obj ", 
                                        '', 
                                        '',
                                        '', 
                                        '', 
                                    )     

                        resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                    "/core/create_json_builders", data=data_obj, headers=headers_obj)
                        
                        add_log(data_row[1],
                                        data_row[0],  
                                        4,
                                        "F3X create_json_builders call with data_obj ", 
                                        resp.json(),
                                        '',
                                        '', 
                                        '', 
                                    ) 

                        if resp.ok:
                            successresp=resp.json()
                            print("create_json_builders call is successfuly finished...")  
                            print(successresp)     

                            add_log(data_row[1],
                                        data_row[0],  
                                        4,
                                        "create_json_builders operation successful ", 
                                        json.dumps(successresp),
                                        '',
                                        '', 
                                        '', 
                                    )  

                            if successresp["result"]["status"].encode('utf-8')=='PROCESSING':
                                # update submission_id in report table 
                                cur.execute("""UPDATE public.reports 
                                                SET submission_id = %s, 
                                                    last_update_date = %s,
                                                    fec_status = 'Processing'
                                                WHERE cmte_id = %s 
                                                AND report_id = %s 
                                                AND status = 'Upload_Waiting' """, [resp['result']['submissionId'], datetime.datetime.now(), data_row[0],  data_row[1]])
                                _conn.commit()   

                                add_log(data_row[1],
                                        data_row[0],  
                                        4,
                                        "create_json_builders operation successful with submission_id ", 
                                        json.dumps(successresp), 
                                        '',
                                        '', 
                                        '' 
                                    )  
                                      

                                if cursor.rowcount == 0:
                                    raise Exception('Error: updating report update date failed.') 

                        elif not resp.ok:
                            add_log(data_row[1],
                                data_row[0], 
                                4,
                                "create_json_builders operation failed with submission_id ",
                                resp.json(),
                                '',
                                '', 
                                ''
                                )

                            print("create_json_builders throwing error...")  
                            print(resp.json())
                 
                elif not resp.ok:
                    add_log(data_row[1],
                                        data_row[0],  
                                        4,
                                        "create_json_builders operation failed with submission_id ", 
                                        resp.json(), 
                                        '',
                                        '', 
                                        '' )

                    print("prepare_json_builders_data throwing error...")  
                    print(resp.json())                                                        

            #Processing F99 reports 
            
            cur.execute("""SELECT committeeid, id FROM public.forms_committeeinfo 
                            WHERE is_submitted
                            AND status is NULL """)

            '''
            cur.execute("""SELECT committeeid, id FROM public.forms_committeeinfo 
                            WHERE id in (1091, 1092, 1087)
                            AND status is NULL""")
            '''
            
            for row in cur.fetchall():
                data_row = list(row)
                data_obj=data_row[0]
                
                cur.execute("""UPDATE public.forms_committeeinfo  
                            SET status = 'Upload_Waiting' 
                            WHERE committeeid = %s 
                            AND id = %s  
                            AND status is NULL """, [data_row[0],  data_row[1]])
                            
                _conn.commit()

                data_obj = {
                        'cmte_id':data_row[0],
                        'reportid':data_row[1]                    
                        }
                        
                # call submit_formf99 API to submi JSON file
                resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                    "/f99/submit_formf99", data=data_obj, headers=headers_obj)
                add_log(data_row[1],
                                    data_row[0],  
                                    4,
                                    "F99 create_json_builders operation successful with submission_id "+ resp['result']['submissionId'], 
                                    successresp, 
                                    '',
                                    '', 
                                    '' )     

                if resp.ok:
                    successresp=resp.json()
                    print("submit_formf99 call is successfuly finished...")  
                    print(successresp)           
                    if successresp['result']['status'].encode('utf-8')=='PROCESSING':
                        # update submission_id in report table 
                        cur.execute("""UPDATE public.forms_committeeinfo 
                                                SET submission_id = %s, 
                                                    updated_at = %s,
                                                    fec_status = 'Processing',
                                                    status = 'Processing'
                                                WHERE committeeid = %s 
                                                AND id = %s 
                                                AND status = 'Upload_Waiting' """, [resp['result']['submissionId'], datetime.datetime.now(), data_row[0],  data_row[1]])
                        _conn.commit()   
                        if cursor.rowcount == 0:
                            raise Exception('Error: updating forms_committeeinfo update date failed.') 
                elif not resp.ok:
                    cur.execute("""UPDATE public.forms_committeeinfo 
                                    SET status = NULL
                                    WHERE committeeid = %s 
                                    AND id = %s 
                                    AND status = 'Waiting' """, [data_row[0],  data_row[1]])
                    _conn.commit()   

                    print("submit_formf99 throwing error...")  
                    print(resp.json())   

                    add_log(data_row[1],
                                        data_row[0],  
                                        4,
                                        "F99 create_json_builders operation failed" , 
                                        json.dumps(resp.json()), 
                                        '',
                                        '', 
                                        '' )                   
        elif not resp.ok:
            print("token/obtain API call is failed...")  
            #notsuccessresp=resp.json()
            print(resp.json())
            add_log(data_row[1],
                                ata_row[0],  
                                4,
                                "token/obtain API call is failed" , 
                                json.dumps(resp.json()), 
                                '',
                                '', 
                                '' )  


    #except Exception as e:

        #raise Exception('Error: get_reports_to_upload is throwing an error. {}'.format( str(e)))                                          
        #raise Exception('Invalid Input: The report_id input should be an integer like 18, 24. Input received: {}'.format(report_id))

    finally:
            _conn.close()
        
        
if __name__ == '__main__':
    _conn = psycopg2.connect(host=_host,database=_database, user=_user, password=_password)
    get_reports_to_upload()
