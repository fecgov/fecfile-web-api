import psycopg2
import requests

#Global Variables
_conn = None
_NEXGEN_DJANGO_API_URL="127.0.0.1:8000/api/v1"
#_NEXGEN_DJANGO_API_URL=settings.DATA_RECEIVE_API_URL  

#replace off 4 DB parameters with environment variables
_host="localhost"
_database="fecfrontend"
_user="postgresqluser1"
_password="postgresqluser1"

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
            cur = _conn.cursor()

            #Processing F3X reports
            # pick reports with status =Uploaded
            '''
            cur.execute("""SELECT cmte_id, report_id, form_type 
                        FROM   public.reports 
                        WHERE  status = 'Uploaded' 
                        ORDER BY last_update_date asc""")
            '''

            cur.execute("""SELECT cmte_id, report_id, form_type 
                        FROM   public.reports 
                        WHERE  status = 'Saved' 
                        AND  report_id in (1401, 1409)
                        ORDER BY last_update_date asc""")

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

                headers_obj = {
                        'Authorization':'JWT '+ token,
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
                                                    last_update_date = %s
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
            cur.execute("""SELECT committeeid, id
                        FROM   public.forms_committeeinfo 
                        WHERE  status = 'Uploaded' 
                        ORDER BY updated_at asc""")

            for row in cur.fetchall():
                data_row = list(row)
                data_obj=data_row[0]
                
                cur.execute("""UPDATE public.forms_committeeinfo  
                            SET status = 'Waiting' 
                            WHERE committeeid = %s 
                            AND id = %s 
                            AND status = 'Uploaded' """, [data_row[0],  data_row[1]])

                _conn.commit()

                data_obj = {
                        'committeeId':data_row[0],
                        'report_id':data_row[1],
                        'call_from':'Submit'
                    }
                # call submit_formf99 API to submi JSON file
                resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                    "/f99/submit_formf99", data=data_obj)
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


