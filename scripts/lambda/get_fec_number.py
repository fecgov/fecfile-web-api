import psycopg2
import requests
import os


# Global Variables
_conn = None
_NEXGEN_DJANGO_API_URL = os.environ.get("NEXGEN_DJANGO_API_URL", "127.0.0.1:8000")
_NEXGEN_DJANGO_API_URL = _NEXGEN_DJANGO_API_URL + "/api/v1"
_DATA_RECEIVE_API_URL = os.environ.get('DATA_RECEIVER_URL', '127.0.0.1:8090')

# _NEXGEN_DJANGO_API_URL=settings.DATA_RECEIVE_API_URL

# replace off 4 DB parameters with environment variables
_host = os.environ.get("DB_HOST", "localhost")
_database = os.environ.get("DB_NAME", "fecfrontend2")
_user = os.environ.get("DB_USER", "fecuser2")
_password = os.environ.get("DB_PASSWD", "postgres")

def get_fec_number():
    """ query data from the vendors table """
    try:
        print("get_reports_to_upload accessing ...")
        _conn = psycopg2.connect(host=_host,database=_database, user=_user, password=_password)
        
        #use here one specimen committee username and password
        data_obj = {
                    'username':'C00000422',
                    'password':'test'
                 }

        # Get the token to access API  
        resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                 "/token/obtain", data=data_obj)

        print("get token ...")
        if resp.ok:
            successresp=resp.json()
            print("token/obtain API call is successfully finished...")  
            print(successresp)
            token=successresp['token']
            print(token)

            headers_obj = {
                            'Authorization':'JWT '+ token,
                        }    
            #Processing F3X reports
            cur = _conn.cursor()
            cur.execute("""SELECT cmte_id, 
                                report_id, 
                                submission_id, 
                                form_type, 
                                amend_ind, 
                                report_seq, 
                                email_1, 
                                report_type, 
                                cvg_start_date, 
                                cvg_end_date, 
                                fec_id, 
                                email_2
                            FROM   public.reports 
                            WHERE  status = 'Processing' 
                            ORDER BY last_update_date asc""")

            for row in cur.fetchall():
                data_row = list(row)
                data_obj=data_row[0]
                
                cur.execute("""UPDATE public.reports 
                            SET status = 'Pending' 
                            WHERE cmte_id = %s 
                            AND report_id = %s 
                            AND status = 'Processing' """, [data_row[0],  data_row[1]])
                _conn.commit()
                
                data_obj = {
                        'committeeId':data_row[0],
                        'report_id':data_row[1],
                        'submission_id': data_row[2],
                        'password': 'test',
                        'formType': data_row[3],
                        'newAmendIndicator': data_row[4],
                        'reportSequence': data_row[5],
                        'emailAddress1': data_row[6],
                        'reportType': data_row[7],
                        'coverageStartDate': data_row[8],
                        'coverageEndDate': data_row[9],
                        'originalFECId': data_row[10],
                        'backDoorCode': '', #need to update later
                        'emailAddress2': data_row[11],
                        'wait': 'True'
                        }

                '''
                data_obj = {
                        'committeeId':data_row[0],
                        'report_id':data_row[1],
                        'submission_id': data_row[2],
                        'password': 'test',
                        'wait': 'True'
                        }
         

                # call prepare_json_builders_data API to prepare Data for JSON  
                resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                    "/core/prepare_json_builders_data", data=data_obj, headers_obj)
                '''
                #Passed submissionId and get the status of the report
                print("data_obj", data_obj)
                print("headers_obj", headers_obj)
                resp = requests.post("http://" + _DATA_RECEIVE_API_URL +
                                 "/v1/upload_filing", data=data_obj, headers=headers_obj)                                    
                if resp.ok:
                    successresp=resp.json()
                  
                    beginningImageNumber = successresp['result']['beginningImageNumber']
                    committeeId = successresp['result']['committeeId']
                    message = successresp['result']['message']
                    reportId = successresp['result']['reportId']
                    status = successresp['result']['status']
                    submissionId = successresp['result']['submissionId']
                    uploadTimeStamp = successresp['result']['uploadTimeStamp']

                    if successresp['result']['status'] == 'Accepted':
                        # update fec_id in report table 
                        cur.execute("""UPDATE public.reports 
                                            SET status = 'Submitted',
                                                submission_id = %s, 
                                                image_number = %s, 
                                                begining_image_number = %s, 
                                                message text = %s, 
                                                uploaded_date = %s, 
                                                fec_id = %s, 
                                                fec_accepted_date = %s, 
                                                fec_status = 'Accepted'    
                                            WHERE cmte_id = %s 
                                            AND report_id = %s 
                                            AND status = 'Pending' """, [submissionId,
                                                                            beginningImageNumber,
                                                                            beginningImageNumber,
                                                                            message,
                                                                            uploadTimeStamp,
                                                                            reportId,
                                                                            uploadTimeStamp,
                                                                            data_row[0],  
                                                                            data_row[1]])
                    elif successresp['result']['status'] == 'PROCESSING' or  successresp['result']['status'] == 'Rejected':
                        cur.execute("""UPDATE public.reports 
                                            SET status = %s,
                                                submission_id = %s, 
                                                image_number = %s, 
                                                begining_image_number = %s, 
                                                message text = %s, 
                                                uploaded_date = %s, 
                                                fec_status = %s  
                                            WHERE cmte_id = %s 
                                            AND report_id = %s 
                                            AND status = 'Pending' """, [successresp['result']['status'],
                                                                            submissionId,
                                                                            beginningImageNumber,
                                                                            beginningImageNumber,
                                                                            message,
                                                                            uploadTimeStamp,
                                                                            successresp['result']['status'],
                                                                            data_row[0],  
                                                                            data_row[1]])
    
                    _conn.commit()       

                    if cursor.rowcount == 0:
                        raise Exception('Error: updating fec_id failed.')            

                elif not resp.ok:
                    cur.execute("""UPDATE public.reports 
                                            SET status = 'Processing',
                                                submission_id = %s, 
                                            WHERE cmte_id = %s 
                                            AND report_id = %s 
                                            AND status = 'Pending' """, [submissionId,
                                                                            data_row[0],  
                                                                            data_row[1]])    
                    _conn.commit()       

                    if cursor.rowcount == 0:
                        raise Exception('Error: updating fec_id failed.')                                                           
            #cur.close()

            #Processing F99 reports 
            #Here for F99 NewAmendmedIndicator, ReportSequence and ReportType are blank
            cur.execute("""SELECT committeeid, 
                                id, 
                                submission_id, 
                                form_type, 
                                '', 
                                '', 
                                email_on_file, 
                                '', 
                                coverage_start_date, 
                                coverage_end_date, 
                                fec_id, 
                                email_on_file1
                        FROM   public.forms_committeeinfo 
                        WHERE  status = 'Processing' 
                        ORDER BY updated_at asc""")

            for row in cur.fetchall():
                data_row = list(row)
                data_obj=data_row[0]
                
                cur.execute("""UPDATE public.forms_committeeinfo 
                            SET status = 'Pending' 
                            WHERE committeeid = %s 
                            AND id = %s 
                            AND status = 'Processing' """, [data_row[0],  data_row[1]])
                '''
                data_obj = {
                        'committeeId':data_row[0],
                        'report_id':data_row[1],
                        'submission_id': data_row[2]
                    }
                '''
                _conn.commit() 

                data_obj = {
                        'committeeId':data_row[0],
                        'report_id':data_row[1],
                        'submission_id': data_row[2],
                        'password': 'test',
                        'formType': data_row[3],
                        'newAmendIndicator': data_row[4],
                        'reportSequence': data_row[5],
                        'emailAddress1': data_row[6],
                        'reportType': data_row[7],
                        'coverageStartDate': data_row[8],
                        'coverageEndDate': data_row[9],
                        'originalFECId': data_row[10],
                        'backDoorCode': '',
                        'emailAddress2': data_row[11],
                        'wait': 'True'
                        }    

                # call prepare_json_builders_data API to prepare Data for JSON  
                resp = requests.post("http://" + _DATA_RECEIVE_API_URL +
                                 "/v1/upload_filing", data=data_obj, headers=headers_obj)                                    
                if resp.ok:
                    successresp=resp.json()
                  
                    beginningImageNumber = successresp['result']['beginningImageNumber']
                    committeeId = successresp['result']['committeeId']
                    message = successresp['result']['message']
                    reportId = successresp['result']['reportId']
                    status = successresp['result']['status']
                    submissionId = successresp['result']['submissionId']
                    uploadTimeStamp = successresp['result']['uploadTimeStamp']

                    if successresp['result']['status'] == 'Accepted':
                        # update fec_id in report table 
                        cur.execute("""UPDATE public.forms_committeeinfo 
                                            SET status = 'Submitted',
                                                submission_id = %s, 
                                                image_number = %s, 
                                                begining_image_number = %s, 
                                                message text = %s, 
                                                uploaded_date = %s, 
                                                fec_id = %s, 
                                                fec_accepted_date = %s, 
                                                fec_status = 'Accepted'    
                                            WHERE cmte_id = %s 
                                            AND report_id = %s 
                                            AND status = 'Pending' """, [submissionId,
                                                                            beginningImageNumber,
                                                                            beginningImageNumber,
                                                                            message,
                                                                            uploadTimeStamp,
                                                                            reportId,
                                                                            uploadTimeStamp,
                                                                            data_row[0],  
                                                                            data_row[1]])
                    elif successresp['result']['status'] == 'PROCESSING' or  successresp['result']['status'] == 'Rejected':
                        cur.execute("""UPDATE public.forms_committeeinfo 
                                            SET status = %s,
                                                submission_id = %s, 
                                                image_number = %s, 
                                                begining_image_number = %s, 
                                                message text = %s, 
                                                uploaded_date = %s, 
                                                fec_status = %s,
                                            WHERE committeeid = %s 
                                            AND id = %s 
                                            AND status = 'Pending' """, [successresp['result']['status'],
                                                                            submissionId,
                                                                            beginningImageNumber,
                                                                            beginningImageNumber,
                                                                            message,
                                                                            uploadTimeStamp,
                                                                            successresp['result']['status'],
                                                                            data_row[0],  
                                                                            data_row[1]])
    
                        _conn.commit()       

                        if cursor.rowcount == 0:
                            raise Exception('Error: updating submission_id failed.')

                elif not resp.ok:
                    cur.execute("""UPDATE public.forms_committeeinfo 
                                            SET status = 'Processing',
                                                submission_id = %s, 
                                            WHERE committeeid = %s 
                                            AND id = %s 
                                            AND status = 'Pending' """, [submissionId,
                                                                            data_row[0],  
                                                                            data_row[1]])    
                    _conn.commit()       

                    if cursor.rowcount == 0:
                        raise Exception('Error: updating fec_id failed.')   

        elif not resp.ok:
            raise Exception('Error: Getting token failed...')                   
    except Exception as e:
        raise Exception('Error: get_fec_number is throwing an error.', e)    

    finally:
        _conn.close()

            
if __name__ == '__main__':
    get_fec_number()

