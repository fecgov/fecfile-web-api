from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
import maya
from .models import Cmte_Report_Types_View, My_Forms_View #, GenericDocument
from rest_framework.response import Response
from fecfiler.forms.models import CommitteeInfo
from fecfiler.forms.serializers import CommitteeInfoSerializer
import json
import datetime
import os
import requests
from django.views.decorators.csrf import csrf_exempt
import logging
from django.db import connection
from django.http import JsonResponse
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import boto
from boto.s3.key import Key
from django.conf import settings

# Create your views here.

logger = logging.getLogger(__name__)

class NoOPError(Exception):
    def __init__(self, *args, **kwargs):
        default_message = 'Raising Custom Exception NoOPError: There are no results found for the specified parameters!'
        if not (args or kwargs): args = (default_message,)
        super().__init__(*args, **kwargs)

@api_view(['GET'])
def get_filed_report_types(request):

    
    #Fields for identifying the committee type and committee design and filter the forms category 
    
    try:
        #import ipdb;ipdb.set_trace()
        comm_id = request.user.username
        
        #forms_obj = [obj.__dict__ for obj in Cmte_Report_Types_View.objects.raw("select report_type,rpt_type_desc,regular_special_report_ind,rpt_type_info, cvg_start_date,
        #cvg_end_date,due_date from public.cmte_report_types_view where cmte_id='" + comm_id + "' order by rpt_type_order")]

        forms_obj = []
        with connection.cursor() as cursor:
            cursor.execute("select report_type,rpt_type_desc,regular_special_report_ind,rpt_type_info, cvg_start_date,cvg_end_date,due_date from public.cmte_report_types_view where cmte_id = %s order by rpt_type_order", [comm_id])
            for row in cursor.fetchall():
                #forms_obj.append(data_row)
                data_row = list(row)
                for idx,elem in enumerate(row):
                    if not elem:
                        data_row[idx]=''
                    if type(elem)==datetime.date:
                        data_row[idx] = elem.strftime("%m-%d-%Y")
                forms_obj.append({"report_type":data_row,"rpt_type_desc":data_row[1],"regular_special_report_ind":data_row[2],"rpt_type_info":data_row[3],"cvg_start_date":data_row[4],"cvg_end_date":data_row[5],"due_date":data_row[6]})
                
        if len(forms_obj)== 0:
            return Response("No entries were found for this committee", status=status.HTTP_400_BAD_REQUEST)	                            
        #for form_obj in forms_obj:
        #    if form_obj['due_date']:
        #        form_obj['due_date'] = form_obj['due_date'].strftime("%m-%d-%Y")
            
        #resp_data = [{k:v.strip(" ") for k,v in form_obj.items() if k not in ["_state"] and type(v) == str } for form_obj in forms_obj]
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_filed_report_types API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

"""
********************************************************************************************************************************
GET TRANSACTION CATEGORIES API- CORE APP - SPRINT 6 - FNE 528 - BY PRAVEEN JINKA 
********************************************************************************************************************************
"""
@api_view(['GET'])
def get_transaction_categories(request):

    try:
        with connection.cursor() as cursor:
            forms_obj= {}
            form_type = request.query_params.get('form_type')
            cursor.execute("select transaction_category_json from transaction_category_json_view where form_type = %s", [form_type])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
                
        if not bool(forms_obj):
            return Response("No entries were found for the form_type: {} for this committee".format(form_type), status=status.HTTP_400_BAD_REQUEST)                              
        
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_transaction_categories API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

"""
********************************************************************************************************************************
GET REPORT TYPES API- CORE APP - SPRINT 6 - FNE 471 - BY PRAVEEN JINKA 
********************************************************************************************************************************
"""
@api_view(['GET'])
def get_report_types(request):

    try:
        with connection.cursor() as cursor:

            #report_year = datetime.datetime.now().strftime('%Y')
            forms_obj = {}
            cmte_id = request.user.username
            form_type = request.query_params.get('form_type')            
            cursor.execute("select report_types_json From public.report_type_and_due_dates_view where cmte_id = %s and form_type = %s", [cmte_id, form_type])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj= json.loads(data_row[0])
                
        if not bool(forms_obj):
            return Response("No entries were found for the form type: {} for this committee".format(form_type), status=status.HTTP_400_BAD_REQUEST)                              
        
        return JsonResponse(forms_obj, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return Response("The get_report_types API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_filed_form_types(request):
    """
    Fields for identifying the committee type and committee design and filter the forms category 
    """
    try:
        comm_id = request.user.username

        #forms_obj = [obj.__dict__ for obj in RefFormTypes.objects.raw("select  rctf.category,rft.form_type,rft.form_description,rft.form_tooltip,rft.form_pdf_url from ref_form_types rft join ref_cmte_type_vs_forms rctf on rft.form_type=rctf.form_type where rctf.cmte_type='" + cmte_type + "' and rctf.cmte_dsgn='" + cmte_dsgn +  "'")]
        forms_obj = [obj.__dict__ for obj in My_Forms_View.objects.raw("select * from my_forms_view where cmte_id = %s order by category,form_type", [comm_id])]

        for form_obj in forms_obj:
            if form_obj['due_date']:
                form_obj['due_date'] = form_obj['due_date'].strftime("%m-%d-%Y")

        resp_data = [{k:v.strip(" ") for k,v in form_obj.items() if k not in ["_state"] and type(v) == str } for form_obj in forms_obj]
        return Response(resp_data, status=status.HTTP_200_OK)
    except:
        return Response({}, status=status.HTTP_404_NOT_FOUND)



"""
********************************************************************************************************************************
GET DYNAMIC FORM FIELDS API- CORE APP - SPRINT 7 - FNE 526 - BY PRAVEEN JINKA 
********************************************************************************************************************************
"""
@api_view(['GET'])
def get_dynamic_forms_fields(request):

    try:
        with connection.cursor() as cursor:

            #report_year = datetime.datetime.now().strftime('%Y')
            cmte_id = request.user.username
            form_type = request.query_params.get('form_type')
            transaction_type = request.query_params.get('transaction_type')
            forms_obj = {}            
            cursor.execute("select form_fields from dynamic_forms_view where form_type = %s and transaction_type = %s", [form_type, transaction_type])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
                
        if not bool(forms_obj):
            return Response("No entries were found for the form_type: {} and transaction type: {} for this committee".format(form_type, transaction_type), status=status.HTTP_400_BAD_REQUEST)                              
        
        return JsonResponse(forms_obj, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return Response("The get_dynamic_forms_fields API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

"""
********************************************************************************************************************************
REPORTS API- CORE APP - SPRINT 7 - FNE 555 - BY PRAVEEN JINKA 
********************************************************************************************************************************
"""

def check_form_type(form_type):

    form_list = ["F3X",]

    if not (form_type in form_list):
        raise Exception('Form Type is not correctly specified. Input received is: {}'.format(form_type))

def check_list_cvg_dates(args):

    try:
        cmte_id = args[0]
        form_type = args[1]
        cvg_start_dt = args[2]
        cvg_end_dt = args[3]

        forms_obj = []
        with connection.cursor() as cursor: 
            cursor.execute("SELECT report_id, cvg_start_date, cvg_end_date FROM public.reports WHERE cmte_id = %s and form_type = %s AND delete_ind is distinct from 'Y' ORDER BY report_id DESC", [cmte_id, form_type])

            if len(args) == 4:
                for row in cursor.fetchall():
                    if (row[1] <= cvg_end_dt and row[2] >= cvg_start_dt):
                        forms_obj.append({"report_id":row[0],"cvg_start_date":row[1],"cvg_end_date":row[2]})

            if len(args) == 5:
                report_id = args[4]
                for row in cursor.fetchall():
                    if ((row[1] <= cvg_end_dt and row[2] >= cvg_start_dt) and row[0] != int(report_id)):
                        forms_obj.append({"report_id":row[0],"cvg_start_date":row[1],"cvg_end_date":row[2]})

        return forms_obj
    except Exception:
        raise 

def date_format(cvg_date):
    try:
        cvg_dt = datetime.strptime(cvg_date, '%m/%d/%Y').date()
        return cvg_dt
    except:
        raise

"""
**************************************************** FUNCTIONS - REPORT IDS **********************************************************
"""
def get_next_report_id():

    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT nextval('report_id_seq')""")
            report_ids = cursor.fetchone()
            report_id = report_ids[0]

        return report_id
    except Exception:
        raise 

def get_prev_report_id(report_id):

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval('report_id_seq', %s, false)", [report_id])
    except Exception:
        raise

def check_report_id(report_id):

    try:
        check_report_id = int(report_id)
    except Exception as e:
        raise

"""
**************************************************** FUNCTIONS - REPORTS *************************************************************
"""
def post_sql_report(report_id, cmte_id, form_type, amend_ind, report_type, cvg_start_date, cvg_end_date):

    try:
        with connection.cursor() as cursor:
            # INSERT row into Reports table
            cursor.execute("""INSERT INTO public.reports (report_id, cmte_id, form_type, amend_ind, report_type, cvg_start_date, cvg_end_date)
                                VALUES (%s,%s,%s,%s,%s,%s,%s)""",[report_id, cmte_id, form_type, amend_ind, report_type, cvg_start_date, cvg_end_date])                                          
    except Exception:
        raise

def get_list_all_report(cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET all rows from Reports table
            query_string = """SELECT report_id, cmte_id, form_type, report_type, amend_ind, amend_number, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, create_date, last_update_date
                                                    FROM public.reports WHERE delete_ind is distinct from 'Y' AND cmte_id = %s""" 
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id])
           
            for row in cursor.fetchall():
            #forms_obj.append(data_row)
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            raise NoOPError('The Committee: {} does not have any reports listed'.format(cmte_id))
        return forms_obj
    except Exception:
        raise

def get_list_report(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET single row from Reports table
            query_string = """SELECT report_id, cmte_id, form_type, report_type, amend_ind, amend_number, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, create_date, last_update_date 
                                            FROM public.reports WHERE cmte_id = %s AND delete_ind is distinct from 'Y' AND report_id = %s"""
            
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id, report_id])

            for row in cursor.fetchall():
            #forms_obj.append(data_row)
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            raise NoOPError('The Report ID: {} does not exist or is deleted'.format(report_id))
        return forms_obj
    except Exception:
        raise

def put_sql_report(report_id, cmte_id, report_type, cvg_start_date, cvg_end_date):

    try:
        with connection.cursor() as cursor:
            # UPDATE row into Reports table
            # cursor.execute("""UPDATE public.reports SET report_type = %s, cvg_start_date = %s, cvg_end_date = %s, last_update_date = %s WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
            #                     (data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), datetime.now(), data.get('report_id'), cmte_id))
            cursor.execute("""UPDATE public.reports SET report_type = %s, cvg_start_date = %s, cvg_end_date = %s WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
                                [report_type, cvg_start_date, cvg_end_date, report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Report ID: {} does not exist in Reports table'.format(report_id))
    except Exception:
        raise

def delete_sql_report(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from Reports table
            # cursor.execute("""UPDATE public.reports SET delete_ind = 'Y', last_update_date = %s WHERE report_id = '""" + report_id + """' AND cmte_id = '""" + cmte_id + """'""", (datetime.now()))
            cursor.execute("""UPDATE public.reports SET delete_ind = 'Y' WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Report ID: {} is either deleted or does not exist in Reports table'.format(report_id))
    except Exception:
        raise

def undo_delete_sql_report(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from Reports table
            # cursor.execute("""UPDATE public.reports SET delete_ind = 'Y', last_update_date = %s WHERE report_id = '""" + report_id + """' AND cmte_id = '""" + cmte_id + """'""", (datetime.now()))
            cursor.execute("""UPDATE public.reports SET delete_ind = '' WHERE report_id = %s AND cmte_id = %s AND delete_ind = 'Y'""", [report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Report ID: {} is not deleted or does not exist in Reports table'.format(report_id))
    except Exception:
        raise  

def remove_sql_report(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # DELETE row into Reports table
            cursor.execute("""DELETE FROM public.reports WHERE report_id = %s AND cmte_id = %s""", [report_id, cmte_id])           
    except Exception:
        raise 

"""
********************************************************** FUNCTIONS - FORM 3X *******************************************************************
"""
def post_sql_form3x(report_id, cmte_id, form_type, amend_ind, report_type, election_code, date_of_election, state_of_election, cvg_start_dt, cvg_end_dt, coh_bop):

    try:
        with connection.cursor() as cursor:
            # Insert data into Form 3X table
            cursor.execute("""INSERT INTO public.form_3x (report_id, cmte_id, form_type, amend_ind, report_type, election_code, date_of_election, state_of_election, cvg_start_dt, cvg_end_dt, coh_bop)
                                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",[report_id, cmte_id, form_type, amend_ind, report_type, election_code, date_of_election, state_of_election, cvg_start_dt, cvg_end_dt, coh_bop])           
    except Exception:
        raise

def put_sql_form3x(report_type, election_code, date_of_election, state_of_election, cvg_start_dt, cvg_end_dt, coh_bop, report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # UPDATE row into Form 3X table
            # cursor.execute("""UPDATE public.form_3x SET report_type = %s, election_code = %s, date_of_election = %s, state_of_election = %s, cvg_start_dt = %s, cvg_end_dt = %s, coh_bop = %s, last_update_date = %s WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
            #                     (data.get('report_type'), data.get('election_code'), data.get('date_of_election'), data.get('state_of_election'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('coh_bop'), datetime.now(), data.get('report_id'), cmte_id))
            cursor.execute("""UPDATE public.form_3x SET report_type = %s, election_code = %s, date_of_election = %s, state_of_election = %s, cvg_start_dt = %s, cvg_end_dt = %s, coh_bop = %s WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
                                [report_type, election_code, date_of_election, state_of_election, cvg_start_dt, cvg_end_dt, coh_bop, report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('This Report ID: {} is either already deleted or does not exist in Form 3X table'.format(report_id))              
    except Exception:
        raise

def delete_sql_form3x(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from form3x table
            # cursor.execute("""UPDATE public.form_3x SET delete_ind = 'Y', last_update_date = %s WHERE report_id = '""" + report_id + """' AND cmte_id = '""" + cmte_id + """'AND delete_ind is distinct from 'Y'""", (datetime.now()))
            cursor.execute("""UPDATE public.form_3x SET delete_ind = 'Y' WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('This Report ID: {} is either already deleted or does not exist in Form 3X table'.format(report_id))
    except Exception:
        raise 
"""
********************************************************** API FUNCTIONS - REPORTS *******************************************************************
"""
def post_reports(data):
    try:
        cmte_id = data.get('cmte_id')
        form_type = data.get('form_type')
        cvg_start_dt = data.get('cvg_start_dt')
        cvg_end_dt = data.get('cvg_end_dt')
        check_form_type(form_type)
        args = [cmte_id, form_type, cvg_start_dt, cvg_end_dt]
        forms_obj = []
        if not (cvg_start_dt is None or cvg_end_dt is None):
            forms_obj = check_list_cvg_dates(args)
        if len(forms_obj)== 0:
            report_id = get_next_report_id()
            data['report_id'] = str(report_id)
            try:
                post_sql_report(report_id, data.get('cmte_id'), data.get('form_type'), data.get('amend_ind'), data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'))
            except Exception as e:
                # Resetting Report ID
                get_prev_report_id(report_id)
                raise Exception('The post_sql_report function is throwing an error: ' + str(e))

            try:
                #Insert data into Form 3X table
                if data.get('form_type') == "F3X":
                    post_sql_form3x(report_id, data.get('cmte_id'), data.get('form_type'), data.get('amend_ind'), data.get('report_type'), data.get('election_code'), data.get('date_of_election'), data.get('state_of_election'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('coh_bop'))                                            
                output = get_reports(data)
            except Exception as e:
                # Resetting Report ID
                get_prev_report_id(report_id)
                # Delete report that was earlier created
                remove_sql_report(report_id, cmte_id)
                raise Exception('The post_sql_form3x function is throwing an error: ' + str(e))
            
            return output[0]
        else:
            return forms_obj
    except:
        raise

def get_reports(data):
    try:
        cmte_id = data.get('cmte_id')
        report_flag = False
        if 'report_id' in data:
            try:
                report_id = data.get('report_id')
                check_report_id(report_id)
                report_flag = True
            except Exception:
                report_flag = False

        if report_flag:
            forms_obj = get_list_report(report_id, cmte_id)
        else:
            forms_obj = get_list_all_report(cmte_id)
        return forms_obj
    except:
        raise

def put_reports(data):
    try:
        cmte_id = data.get('cmte_id')  
        check_form_type(data.get('form_type'))
        check_report_id(data.get('report_id'))
        report_id = data.get('report_id')
        args = [cmte_id, data.get('form_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('report_id')]
        forms_obj = []
        if not (data.get('cvg_start_dt') is None or data.get('cvg_end_dt') is None):                        
            forms_obj = check_list_cvg_dates(args)
        if len(forms_obj)== 0:
            old_list_report = get_list_report(report_id, cmte_id)
            put_sql_report(data.get('report_id'), cmte_id, data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'))
            old_dict_report = old_list_report[0]
            prev_report_type = old_dict_report.get('report_type')
            prev_cvg_start_dt = old_dict_report.get('cvg_start_date')
            prev_cvg_end_dt = old_dict_report.get('cvg_end_date')
            prev_last_update_date = old_dict_report.get('last_update_date')
                                           
            try:
                if data.get('form_type') == "F3X":
                    put_sql_form3x(data.get('report_type'), data.get('election_code'), data.get('date_of_election'), data.get('state_of_election'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('coh_bop'), data.get('report_id'), cmte_id)                            
                output = get_reports(data)
            except Exception as e:
                    put_sql_report(data.get('report_id'), cmte_id, prev_report_type, prev_cvg_start_dt, prev_cvg_end_dt)
                    raise Exception('The put_sql_form3x function is throwing an error: ' + str(e))
            
            return output[0]
        else:
            return forms_obj
    except:
        raise

def delete_reports(data):
    try:
        cmte_id = data.get('cmte_id')
        form_type = data.get('form_type')
        report_id = data.get('report_id')
        check_form_type(form_type)
        check_report_id(report_id)
        old_list_report = get_list_report(report_id, cmte_id)
        delete_sql_report(report_id, cmte_id)
        old_dict_report = old_list_report[0]
        prev_last_update_date = old_dict_report.get('last_update_date')            

        if form_type == "F3X":
            with connection.cursor() as cursor:
                try:
                    delete_sql_form3x(report_id, cmte_id)
                except Exception as e:
                    undo_delete_sql_report(report_id, cmte_id)
                    raise Exception ('The delete_sql_form3x function is throwing an error: ' + str(e))
    except:
        raise

"""
***************************************************** REPORTS - POST API CALL STARTS HERE **********************************************************
"""
@api_view(['POST','GET','DELETE','PUT'])
def reports(request):

    if request.method == 'POST':
        try:
            if 'amend_ind' in request.data:
                amend_ind = request.data.get('amend_ind')
            else:
                amend_ind = "N"

            if 'election_code' in request.data:
                election_code = request.data.get('election_code')
            else:
                election_code = None
            
            datum = {
                'cmte_id': request.user.username,
                'form_type': request.data.get('form_type'),
                'amend_ind': amend_ind,
                'report_type': request.data.get('report_type'),
                'election_code': election_code,
                'date_of_election': date_format(request.data.get('date_of_election')),
                'state_of_election': request.data.get('state_of_election'),
                'cvg_start_dt': date_format(request.data.get('cvg_start_dt')),
                'cvg_end_dt': date_format(request.data.get('cvg_end_dt')),
                'coh_bop': int(request.data.get('coh_bop')),
            }    
            data = post_reports(datum)
            if type(data) is dict:
                return JsonResponse(data, status=status.HTTP_201_CREATED, safe=False)
            elif type(data) is list:
                return JsonResponse(data, status=status.HTTP_200_OK, safe=False)
            else:
                raise Exception('The output returned from post_reports function is neither dict nor list')
        except Exception as e:
            logger.debug(e)
            return Response("The reports API - POST is throwing  an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    """
    *********************************************** REPORTS - GET API CALL STARTS HERE **********************************************************
    """
    #Get records from reports table

    if request.method == 'GET':
        try:
            data = {
                'cmte_id': request.user.username,
                }
            if 'report_id' in request.query_params:
                data['report_id'] = request.query_params.get('report_id')
            forms_obj = get_reports(data)   
            return JsonResponse(forms_obj, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The reports API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    """
    ************************************************* REPORTS - PUT API CALL STARTS HERE **********************************************************
    """
    if request.method == 'PUT':

        try:  
            datum = {
                'report_id': request.data.get('report_id'),
                'cmte_id': request.user.username,
                'form_type': request.data.get('form_type'),
                'report_type': request.data.get('report_type'),
                'date_of_election': date_format(request.data.get('date_of_election')),
                'state_of_election': request.data.get('state_of_election'),
                'cvg_start_dt': date_format(request.data.get('cvg_start_dt')),
                'cvg_end_dt': date_format(request.data.get('cvg_end_dt')),
                'coh_bop': int(request.data.get('coh_bop')),
            }
            if 'amend_ind' in request.data:
                datum['amend_ind'] = request.data.get('amend_ind')
            
            if 'election_code' in request.data:
                datum['election_code'] = request.data.get('election_code')

            data = put_reports(datum)
            if type(data) is dict:
                return JsonResponse(data, status=status.HTTP_201_CREATED, safe=False)
            elif type(data) is list:
                return JsonResponse(data, status=status.HTTP_200_OK, safe=False)
            else:
                raise Exception('The output returned from put_reports function is neither dict nor list')
        except Exception as e:
            logger.debug(e)
            return Response("The reports API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST) 

    """
    ************************************************ REPORTS - DELETE API CALL STARTS HERE **********************************************************
    """
    if request.method == 'DELETE':

        try:
            data = {
            'cmte_id': request.user.username,
            'report_id': request.query_params.get('report_id'),
            'form_type': request.query_params.get('form_type') 
            }
            delete_reports(data)
            return Response("The Report ID: {} has been successfully deleted".format(data.get('report_id')),status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The reports API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
END - REPORTS API - CORE APP
******************************************************************************************************************************
"""
"""
******************************************************************************************************************************
ENTITIES API- CORE APP - SPRINT 7 - FNE 553 - BY PRAVEEN JINKA
******************************************************************************************************************************
"""

"""
************************************************ FUNCTIONS - ENTITIES **********************************************************
"""
def check_entity_type(entity_type):

    entity_type_list = ["CAN", "CCM", "COM", "IND", "ORG", "PAC", "PTY",]
    if not (entity_type in entity_type_list):
        raise Exception('The Entity Type is not within the specified list. Input received: ' + entity_type)

def get_next_entity_id(entity_type):

    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT public.get_next_entity_id(%s)""",[entity_type])
            entity_ids = cursor.fetchone()
            entity_id = entity_ids[0]
        return entity_id
    except Exception:
        raise

def check_entity_id(entity_id):

    entity_type = entity_id[0:3]
    try:
        check_entity_type(entity_type)
    except Exception as e:
        raise Exception('The Entity ID is not in the specified format. Input received: ' + entity_id)
        

def post_sql_entity(entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id):

    try:
        with connection.cursor() as cursor:

            # Insert data into Entity table
            cursor.execute("""INSERT INTO public.entity (entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id, create_date)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",[entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id, datetime.now()])
    except Exception:
        raise

def get_list_entity(entity_id, cmte_id):

    try:
        query_string = """SELECT entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id
                                                    FROM public.entity WHERE entity_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'"""
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [entity_id, cmte_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            raise NoOPError('The Entity ID: {} does not exist or is deleted'.format(entity_id))   
        return forms_obj
    except Exception:
        raise

def get_list_all_entity(cmte_id):

    try:
        query_string = """SELECT entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id
                                                    FROM public.entity WHERE cmte_id = %s AND delete_ind is distinct from 'Y'"""
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            raise NoOPError('The Committee: {} does not have any entities listed'.format(cmte_id))
        return forms_obj
    except Exception:
        raise

def put_sql_entity(entity_type, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id, entity_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # Put data into Entity table
            # cursor.execute("""UPDATE public.entity SET entity_type = %s, entity_name = %s, first_name = %s, last_name = %s, middle_name = %s, preffix = %s, suffix = %s, street_1 = %s, street_2 = %s, city = %s, state = %s, zip_code = %s, occupation = %s, employer = %s, ref_cand_cmte_id = %s, last_update_date = %s WHERE entity_id = %s AND cmte_id = %s AND delete_ind is distinct FROM 'Y'""",
            #             (entity_type, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id, last_update_date, entity_id, cmte_id))                       
            cursor.execute("""UPDATE public.entity SET entity_type = %s, entity_name = %s, first_name = %s, last_name = %s, middle_name = %s, preffix = %s, suffix = %s, street_1 = %s, street_2 = %s, city = %s, state = %s, zip_code = %s, occupation = %s, employer = %s, ref_cand_cmte_id = %s WHERE entity_id = %s AND cmte_id = %s AND delete_ind is distinct FROM 'Y'""",
                        [entity_type, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id, entity_id, cmte_id])                       
            if (cursor.rowcount == 0):
                raise Exception('The Entity ID: {} does not exist in Entity table'.format(entity_id))
    except Exception:
        raise

def delete_sql_entity(entity_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # UPDATE delete_ind flag to Y in DB
            # cursor.execute("""UPDATE public.entity SET delete_ind = 'Y', last_update_date = %s WHERE entity_id = '""" + entity_id + """' AND cmte_id = '""" + cmte_id + """' AND delete_ind is distinct from 'Y'""", (datetime.now()))
            cursor.execute("""UPDATE public.entity SET delete_ind = 'Y' WHERE entity_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [entity_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Entity ID: {} is either already deleted or does not exist in Entity table'.format(entity_id))
    except Exception:
        raise

def undo_delete_sql_entity(entity_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # UPDATE delete_ind flag to Y in DB
            # cursor.execute("""UPDATE public.entity SET delete_ind = 'Y', last_update_date = %s WHERE entity_id = '""" + entity_id + """' AND cmte_id = '""" + cmte_id + """' AND delete_ind is distinct from 'Y'""", (datetime.now()))
            cursor.execute("""UPDATE public.entity SET delete_ind = '' WHERE entity_id = %s AND cmte_id = %s AND delete_ind = 'Y'""", [entity_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Entity ID: {} is not deleted or does not exist in Entity table'.format(entity_id))
    except Exception:
        raise

def remove_sql_entity(entity_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # DELETE row from entity table    
            cursor.execute("""DELETE FROM public.entity WHERE entity_id = %s AND cmte_id = %s""", [entity_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Entity ID: {} does not exist in Entity table'.format(entity_id))
    except Exception:
        raise
"""
************************************************ API FUNCTIONS - ENTITIES **********************************************************
"""
def post_entities(data):

    try:
        entity_type = data.get('entity_type')
        check_entity_type(entity_type)
        entity_id = get_next_entity_id(entity_type)
        data['entity_id'] = entity_id
        post_sql_entity(entity_id, data.get('entity_type'), data.get('cmte_id'), data.get('entity_name'), data.get('first_name'), data.get('last_name'), data.get('middle_name'),data.get('preffix'), data.get('suffix'), data.get('street_1'), data.get('street_2'), data.get('city'), data.get('state'), data.get('zip_code'), data.get('occupation'), data.get('employer'), data.get('ref_cand_cmte_id'))
        output = get_entities(data)
        return output[0]
    except:
        raise

def get_entities(data):

    try:
        cmte_id = data.get('cmte_id')
        entity_flag = False
        if 'entity_id' in data:
            try:
                check_entity_id(data.get('entity_id'))
                entity_flag = True
            except Exception as e:
                entity_flag = False

        if entity_flag:
            forms_obj = get_list_entity(data.get('entity_id'), cmte_id)
        else:
            forms_obj = get_list_all_entity(cmte_id)
        return forms_obj
    except:
        raise

def put_entities(data):

    try:
        cmte_id = data.get('cmte_id')
        entity_type = data.get('entity_type')
        check_entity_type(entity_type)
        entity_id = data.get('entity_id')
        check_entity_id(entity_id)
        put_sql_entity(data.get('entity_type'), data.get('entity_name'), data.get('first_name'), data.get('last_name'), data.get('middle_name'), data.get('preffix'), data.get('suffix'), data.get('street_1'), data.get('street_2'), data.get('city'), data.get('state'), data.get('zip_code'), data.get('occupation'), data.get('employer'), data.get('ref_cand_cmte_id'), data.get('entity_id'), cmte_id)
        output = get_entities(data)
        return output[0]
    except:
        raise

def delete_entities(data):

    try:
        cmte_id = data.get('cmte_id')
        entity_id = data.get('entity_id')
        check_entity_id(entity_id)
        delete_sql_entity(entity_id, cmte_id)
        
    except:
        raise

def undo_delete_entities(data):

    try:
        cmte_id = data.get('cmte_id')
        entity_id = data.get('entity_id')
        check_entity_id(entity_id)
        undo_delete_sql_entity(entity_id, cmte_id)
        
    except:
        raise

def remove_entities(data):

    try:
        cmte_id = data.get('cmte_id')
        entity_id = data.get('entity_id')
        check_entity_id(entity_id)
        remove_sql_entity(entity_id, cmte_id)
        
    except:
        raise
        
"""
************************************************ ENTITIES - POST API CALL STARTS HERE **********************************************************
"""
@api_view(['POST','GET','DELETE','PUT'])
def entities(request):

    #insert a new record for reports table
    if request.method == 'POST':
        try:
            datum = {
                    'entity_type': request.data.get('entity_type'),
                    'cmte_id': request.user.username,
                    'entity_name': request.data.get('entity_name'),
                    'first_name': request.data.get('first_name'),
                    'last_name': request.data.get('last_name'),
                    'middle_name': request.data.get('middle_name'),
                    'preffix': request.data.get('preffix'),
                    'suffix': request.data.get('suffix'),
                    'street_1': request.data.get('street_1'),
                    'street_2': request.data.get('street_2'),
                    'city': request.data.get('city'),
                    'state': request.data.get('state'),
                    'zip_code': request.data.get('zip_code'),
                    'occupation': request.data.get('occupation'),
                    'employer': request.data.get('employer'),
                    'ref_cand_cmte_id': request.data.get('ref_cand_cmte_id'),
                }     
            data = post_entities(datum)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The entity-POST API is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    """
    ************************************************ ENTITIES - GET API CALL STARTS HERE **********************************************************
    """
    if request.method == 'GET':

        try:
            data = {
            'cmte_id': request.user.username,
            }
            if 'entity_id' in request.query_params:
                data['entity_id'] = request.query_params.get('entity_id')
            
            forms_obj = get_entities(data)
            return JsonResponse(forms_obj, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The entity-GET API is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    """
    ************************************************ ENTITIES - PUT API CALL STARTS HERE **********************************************************
    """
    if request.method == 'PUT':

        try:
            datum = {
                'entity_id': request.data.get('entity_id'),
                'entity_type': request.data.get('entity_type'),
                'cmte_id': request.user.username,
                'entity_name': request.data.get('entity_name'),
                'first_name': request.data.get('first_name'),
                'last_name': request.data.get('last_name'),
                'middle_name': request.data.get('middle_name'),
                'preffix': request.data.get('preffix'),
                'suffix': request.data.get('suffix'),
                'street_1': request.data.get('street_1'),
                'street_2': request.data.get('street_2'),
                'city': request.data.get('city'),
                'state': request.data.get('state'),
                'zip_code': request.data.get('zip_code'),
                'occupation': request.data.get('occupation'),
                'employer': request.data.get('employer'),
                'ref_cand_cmte_id': request.data.get('ref_cand_cmte_id'),
            }      
            data = put_entities(datum)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The entity-PUT call is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    """
    ************************************************ ENTITIES - DELETE API CALL STARTS HERE **********************************************************
    """
    if request.method == 'DELETE':

        try:
            data = {
            'entity_id': request.query_params.get('entity_id'),
            'cmte_id': request.user.username
            }
            delete_entities(data)
            return Response("The Entity ID: {} has been successfully deleted".format(data.get('entity_id')),status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The entity-DELETE call is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
END - ENTITIES API - CORE APP
******************************************************************************************************************************
"""
"""
******************************************************************************************************************************
SEARCH ENTITY API- CORE APP - SPRINT 7 - FNE 588 - BY PRAVEEN JINKA
******************************************************************************************************************************
"""
"""
************************************************ FUNCTIONS - ENTITIES **********************************************************
"""
@api_view(['GET'])
def search_entities(request):
    try:
        cmte_id = request.user.username
        param_string = ""
        order_string = ""
        for key, value in request.query_params.items(): 
            param_string = param_string + " AND LOWER(" + key + ") LIKE LOWER('" + value +"%')"
            order_string = key + ","

        query_string = """SELECT entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id
                                                    FROM public.entity WHERE cmte_id = %s """ + param_string +""" AND delete_ind is distinct from 'Y' ORDER BY """ + order_string[:-1]
        print(query_string)
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        status_value = status.HTTP_200_OK
        if forms_obj is None:
            forms_obj =[]
            status_value = status.HTTP_204_NO_CONTENT
        return Response(forms_obj, status=status_value)
    except Exception as e:
        return Response("The search_entities API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
END - SEARCH ENTITIES API - CORE APP
******************************************************************************************************************************
"""

@api_view(["POST"])
def create_json_file(request):
    #creating a JSON file so that it is handy for all the public API's

        
        try:
            #comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username, is_submitted=True).last()
            comm_info = CommitteeInfo.objects.get(committeeid=request.user.username, id=request.data['id'])

            if comm_info:
                serializer = CommitteeInfoSerializer(comm_info)
                #import ipdb; ipdb.set_trace()
                conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
                bucket = conn.get_bucket("dev-efile-repo")
                k = Key(bucket)
                k.content_type = "application/json"
                k.set_contents_from_string(json.dumps(serializer.data))
                url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")
                return Response(url, status=status.HTTP_200_OK)
            
            else:
                return Response({"FEC Error 007":"This user does not have a submitted CommInfo object"}, status=status.HTTP_400_BAD_REQUEST)
            
        except CommitteeInfo.DoesNotExist:
            return Response({"FEC Error 009":"An unexpected error occurred while processing your request"}, status=status.HTTP_400_BAD_REQUEST)
            
            



