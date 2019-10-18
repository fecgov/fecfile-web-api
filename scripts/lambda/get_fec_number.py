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
_database = os.environ.get("DB_NAME", "postgres")
_user = os.environ.get("DB_USER", "postgres")
_password = os.environ.get("DB_PASSWD", "postgresqluser1")

def get_fec_number():
    """ query data from the vendors table """
    try:
        print("get_reports_to_upload accessing ...")

        _conn = psycopg2._connect(host=_host,database=_database, user=_user, password=_password)
        cur = _conn.cursor()

        #Processing F3X reports
        cur.execute("""SELECT cmte_id, report_id, submission_id, form_type 
                       FROM   public.reports 
                       WHERE  status = 'Waiting' 
                       ORDER BY last_update_date asc""")

        for row in cur.fetchall():
            data_row = list(row)
            data_obj=data_row[0]
            
            cur.execute("""UPDATE public.reports 
                           SET status = 'Getting_FEC_Number' 
                           WHERE cmte_id = %s 
                           AND report_id = %s 
                           AND status = 'Waiting' """, [data_row[0],  data_row[1]])
            _conn.commit()

            data_obj = {
                    'committeeId':data_row[0],
                    'report_id':data_row[1],
                    'submission_id': data_row[2]
                }
            # call prepare_json_builders_data API to prepare Data for JSON  
            resp = requests.post("http://" + _NEXGEN_DJANGO_API_URL +
                                 "/core/prepare_json_builders_data", data=data_obj)

            if resp['Response']=='Success':
                    # update fec_id in report table 
                cur.execute("""UPDATE public.reports 
                                    SET fec_id = %s, 
                                        last_update_date = %s
                                        status = 'Submitted'
                                    WHERE cmte_id = %s 
                                    AND report_id = %s 
                                    AND status = 'Getting_FEC_Number' """, [resp['fec_id'], datetime.datetime.now(), data_row[0],  data_row[1]])
            elif resp['Response']=='Failed':
                cur.execute("""UPDATE public.reports 
                                    SET last_update_date = %s
                                        status = 'Failed'
                                    WHERE cmte_id = %s 
                                    AND report_id = %s 
                                    AND status = 'Getting_FEC_Number' """, [datetime.datetime.now(), data_row[0],  data_row[1]])
            elif resp['Response']=='Waiting':
                cur.execute("""UPDATE public.reports 
                                    SET last_update_date = %s
                                        status = 'Waiting'
                                    WHERE cmte_id = %s 
                                    AND report_id = %s 
                                    AND status = 'Getting_FEC_Number' """, [datetime.datetime.now(), data_row[0],  data_row[1]])
            else:
                cur.execute("""UPDATE public.reports 
                                    SET last_update_date = %s
                                        status = 'Waiting'
                                    WHERE cmte_id = %s 
                                    AND report_id = %s 
                                    AND status = 'Getting_FEC_Number' """, [datetime.datetime.now(), data_row[0],  data_row[1]])
 
            _conn.commit()       

            if cursor.rowcount == 0:
                raise Exception('Error: updating fec_id failed.')                                          

        #cur.close()

        #Processing F99 reports 
        cur.execute("""SELECT committeeid, id, submission_id
                       FROM   public.forms_committeeinfo 
                       WHERE  status = 'Waiting' 
                       ORDER BY updated_at asc""")

        for row in cur.fetchall():
            data_row = list(row)
            data_obj=data_row[0]
            
            cur.execute("""UPDATE public.forms_committeeinfo 
                           SET status = 'Getting_FEC_Number' 
                           WHERE committeeid = %s 
                           AND id = %s 
                           AND status = 'Waiting' """, [data_row[0],  data_row[1]])
            _conn.commit()

            data_obj = {
                    'committeeId':data_row[0],
                    'report_id':data_row[1],
                    'submission_id': data_row[2]
                }
            # call prepare_json_builders_data API to prepare Data for JSON  
            resp = requests.post("http://" + settings.DATA_RECEIVE_API_URL +
                                 "/core/prepare_json_builders_data", data=data_obj)

            if res['Response']=='Success':
                  # update submission_id in forms_committeeinfo table 
                cur.execute("""UPDATE public.forms_committeeinfo 
                                SET submission_id = %s, 
                                    updated_at = %s,
                                    status = 'Submitted'
                                WHERE committeeId = %s 
                                AND id = %s 
                                AND status = 'Getting_FEC_Number' """, [resp['submission_id'], datetime.datetime.now(), data_row[0],  data_row[1]])
            elif res['Response']=='Failed':
                cur.execute("""UPDATE public.forms_committeeinfo 
                                SET updated_at = %s,
                                    status = 'Failed'
                                WHERE committeeId = %s 
                                AND id = %s 
                                AND status = 'Getting_FEC_Number' """, [datetime.datetime.now(), data_row[0],  data_row[1]])
            elif res['Response']=='Waiting':
                cur.execute("""UPDATE public.forms_committeeinfo 
                                SET updated_at = %s,
                                    status = 'Waiting'
                                WHERE committeeId = %s 
                                AND id = %s 
                                AND status = 'Getting_FEC_Number' """, [datetime.datetime.now(), data_row[0],  data_row[1]])                    
            else:
                cur.execute("""UPDATE public.forms_committeeinfo 
                                SET updated_at = %s,
                                    status = 'Waiting'
                                WHERE committeeId = %s 
                                AND id = %s 
                                AND status = 'Getting_FEC_Number' """, [datetime.datetime.now(), data_row[0],  data_row[1]])                    
            _conn.commit()       

            if cursor.rowcount == 0:
                raise Exception('Error: updating submission_id failed.')                                          

    except Exception as e:
        raise Exception('Error: get_fec_number is throwing an error.')    

    finally:
            _conn.close()
            
    if __name__ == '__main__':
        get_fec_number()

