import psycopg2
import requests
import os


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

def get_reports_to_upload():
    """ query data from the vendors table """
    try:

        print("get_reports_to_upload accessing ...")
        # Get API token
        _conn = psycopg2.connect(host=_host,database=_database, user=_user, password=_password)
        data_obj = {
                    'username':'C00000422',
                    'password':'test'
                 }

        # Get the token to access API  
        resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                 "/token/obtain", data=data_obj)
        if resp.ok:
            successresp=resp.json()
            print("token/obtain API call is successfully finished...")  
            print(successresp)
            token=successresp['token']
            print(token)

            headers_obj = {
                        'Authorization':'JWT '+ token,
                        }
            cur = _conn.cursor()

            #Processing F3X reports
            # pick reports with status =Uploaded
            
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
                
                '''
                cur.execute("""UPDATE public.reports 
                            SET status = 'Waiting' 
                            WHERE cmte_id = %s 
                            AND report_id = %s 
                            AND status = 'Uploaded' """, [data_row[0],  data_row[1]])
                '''
                cur.execute("""UPDATE public.reports 
                            SET status = 'Waiting' 
                            WHERE cmte_id = %s 
                            AND report_id = %s 
                            AND status = 'Saved' """, [data_row[0],  data_row[1]])                           
                _conn.commit()

                data_obj = {
                        'cmte_id':data_row[0],
                        'report_id':data_row[1],
                        'call_from':'Submit'
                    }

                # call prepare_json_builders_data API to prepare Data for JSON  
                resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                    "/core/prepare_json_builders_data", data=data_obj, headers=headers_obj)
                if resp.ok:
                    successresp=resp.json()
                    print("prepare_json_builders_data call is successfully finished...")  
                    print(successresp)
                    if successresp['Response'].encode('utf-8')=='Success':
                        # call create_json_builders which internally call Data Reciever API

                        data_obj = {
                                    'committeeId':data_row[0],
                                    'report_id':data_row[1],
                                    'call_from':'Submit'
                                   }

                        resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                    "/core/create_json_builders", data=data_obj, headers=headers_obj)
                        if resp.ok:
                            successresp=resp.json()
                            print("create_json_builders call is successfully finished...")  
                            print(successresp)           
                            if successresp['Response'].encode('utf-8')=='Success':
                            # update submission_id in report table 
                                cur.execute("""UPDATE public.reports 
                                                SET submission_id = %s, 
                                                    last_update_date = %s,
                                                    fec_status = 'Processing'
                                                WHERE cmte_id = %s 
                                                AND report_id = %s 
                                                AND status = 'Waiting' """, [resp['submission_id'], datetime.datetime.now(), data_row[0],  data_row[1]])
                                _conn.commit()   
                                if cursor.rowcount == 0:
                                    raise Exception('Error: updating report update date failed.') 
                        elif not resp.ok:
                            print("create_json_builders throwing error...")  
                            print(resp.json())
                 
                elif not resp.ok:
                    print("prepare_json_builders_data throwing error...")  
                    print(resp.json())                                                        

            #Processing F99 reports 
            '''
            cur.execute("""SELECT committeeid, id FROM public.forms_committeeinfo 
                            WHERE is_submitted
                            AND status is NULL""")
            '''

            cur.execute("""SELECT committeeid, id FROM public.forms_committeeinfo 
                            WHERE id in (1091, 1092, 1087)
                            AND status is NULL""")

            for row in cur.fetchall():
                data_row = list(row)
                data_obj=data_row[0]
                
                cur.execute("""UPDATE public.forms_committeeinfo  
                            SET status = 'Waiting' 
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
                if resp.ok:
                    successresp=resp.json()
                    print("submit_formf99 call is successfully finished...")  
                    print(successresp)           
                    if successresp['Response'].encode('utf-8')=='Success':
                        # update submission_id in report table 
                        cur.execute("""UPDATE public.forms_committeeinfo 
                                                SET submission_id = %s, 
                                                    updated_at = %s,
                                                    fec_status = 'Processing'
                                                WHERE committeeid = %s 
                                                AND id = %s 
                                                AND status = 'Waiting' """, [resp['submission_id'], datetime.datetime.now(), data_row[0],  data_row[1]])
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
        elif not resp.ok:
            print("token/obtain API call is failed...")  
            #notsuccessresp=resp.json()
            print(resp.json())


    #except Exception as e:

        #raise Exception('Error: get_reports_to_upload is throwing an error. {}'.format( str(e)))                                          
        #raise Exception('Invalid Input: The report_id input should be an integer like 18, 24. Input received: {}'.format(report_id))

    finally:
            _conn.close()
        
        
if __name__ == '__main__':
    get_reports_to_upload()
