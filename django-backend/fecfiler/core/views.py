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
# from datetime import datetime, date
import boto3
from botocore.exceptions import ClientError
import boto
from boto.s3.key import Key
from django.conf import settings
import re
import csv
from django.core.paginator import Paginator
# from fecfiler.core.jsonbuilder import create_f3x_expenditure_json_file, build_form3x_json_file,create_f3x_json_file, create_f3x_partner_json_file,create_f3x_returned_bounced_json_file,create_f3x_reattribution_json_file,create_inkind_bitcoin_f3x_json_file,get_report_info

# Create your views here.

logger = logging.getLogger(__name__)
# aws s3 bucket connection
conn = boto.connect_s3()

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

def check_form_data(field, data):

    try:
        if field in data:
            if not data.get(field) in [None, "null", '', ""]:
                return data.get(field)
            else:
                return None    
        else:
            return None
    except Exception as e:
        raise

def check_list_cvg_dates(args):

    try:
        cmte_id = args[0]
        form_type = args[1]
        cvg_start_dt = args[2]
        cvg_end_dt = args[3]
    
        forms_obj = []
        with connection.cursor() as cursor: 
            cursor.execute("SELECT report_id, cvg_start_date, cvg_end_date, report_type FROM public.reports WHERE cmte_id = %s and form_type = %s AND delete_ind is distinct from 'Y' ORDER BY report_id DESC", [cmte_id, form_type])

            if len(args) == 4:
                for row in cursor.fetchall():
                    if not(row[1] is None or row[2] is None):
                        if ( cvg_end_dt <= row[2]  and  cvg_start_dt >= row[1] ) :
                            forms_obj.append({"report_id":row[0],"cvg_start_date":row[1],"cvg_end_date":row[2],"report_type":row[3]})

            if len(args) == 5:
                report_id = args[4]
                for row in cursor.fetchall():
                    if not(row[1] is None or row[2] is None):
                        if ((cvg_end_dt <= row[2]  and  cvg_start_dt >= row[1]) and row[0] != int(report_id)):
                            forms_obj.append({"report_id":row[0],"cvg_start_date":row[1],"cvg_end_date":row[2],"report_type":row[3]})

        return forms_obj
    except Exception:
        raise 


def date_format(cvg_date):
    try:
        if cvg_date == None or cvg_date in ["none", "null", " ", ""]:
            return None
        cvg_dt = datetime.datetime.strptime(cvg_date, '%m/%d/%Y').date()
        return cvg_dt
    except:
        raise

def check_null_value(check_value):
    try:
        if check_value in ["none", "null", " ", ""]:
            return None
        else:
            return check_value
    except:
        raise

def check_email(email):
    try:
        pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
        if not check_null_value(email):
            return None
        if re.fullmatch(pattern, email):
            return email
        else:
            raise Exception('Email entered is in an invalid format. Input received is: {}. Expected: abc@def.xyz or abc@def.wxy.xyz'.format(email))
    except:
        raise

def check_mandatory_fields_report(data):
    try:
        list_mandatory_fields_report = ['form_type', 'amend_ind', 'cmte_id']
        error =[]
        for field in list_mandatory_fields_report:
            if not(field in data and check_null_value(data.get(field))):
                error.append(field)
        if len(error) > 0:
            string = ""
            for x in error:
                string = string + x + ", "
            string = string[0:-2]
            raise Exception('The following mandatory fields are required in order to save data to Reports table: {}'.format(string))
    except:
        raise

def check_mandatory_fields_form3x(data):
    try:
        list_mandatory_fields_form3x = ['form_type', 'amend_ind']
        error =[]
        for field in list_mandatory_fields_form3x:
            if not(field in data and check_null_value(data.get(field))):
                error.append(field)
        if len(error) > 0:
            string = ""
            for x in error:
                string = string + x + ", "
            string = string[0:-2]
            raise Exception('The following mandatory fields are required in order to save data to Form3x table: {}'.format(string))
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
        return report_id
    except Exception as e:
        raise Exception('Invalid Input: The report_id input should be an integer like 18, 24. Input received: {}'.format(report_id))

"""
**************************************************** FUNCTIONS - REPORTS *************************************************************
"""
def post_sql_report(report_id, cmte_id, form_type, amend_ind, report_type, cvg_start_date, cvg_end_date, due_date, status, email_1, email_2, additional_email_1, additional_email_2):

    try:
        with connection.cursor() as cursor:
            # INSERT row into Reports table
            cursor.execute("""INSERT INTO public.reports (report_id, cmte_id, form_type, amend_ind, report_type, cvg_start_date, cvg_end_date, status, due_date, email_1, email_2, additional_email_1, additional_email_2)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",[report_id, cmte_id, form_type, amend_ind, report_type, cvg_start_date, cvg_end_date, status, due_date, email_1, email_2, additional_email_1, additional_email_2])                                          
    except Exception:
        raise

def get_list_all_report(cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET all rows from Reports table
            query_string = """SELECT report_id, cmte_id, form_type, report_type, amend_ind, amend_number, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, email_1, email_2, filed_date, fec_id, fec_accepted_date, fec_status, create_date, last_update_date
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
            
            query_string = """SELECT cmte_id as cmteId, report_id as reportId, form_type as formType, '' as electionCode, report_type as reportType,  rt.rpt_type_desc as reportTypeDescription, rt.regular_special_report_ind as regularSpecialReportInd, '' as stateOfElection, '' as electionDate, cvg_start_date as cvgStartDate, cvg_end_date as cvgEndDate, due_date as dueDate, amend_ind as amend_Indicator, 0 as coh_bop, (SELECT CASE WHEN due_date IS NOT NULL THEN to_char(due_date, 'YYYY-MM-DD')::date - to_char(now(), 'YYYY-MM-DD')::date ELSE 0 END ) AS daysUntilDue, email_1 as email1, email_2 as email2, additional_email_1 as additionalEmail1, additional_email_2 as additionalEmail2
                                      FROM public.reports rp, public.ref_rpt_types rt WHERE rp.report_type=rt.rpt_type AND delete_ind is distinct from 'Y' AND cmte_id = %s  AND report_id = %s""" 


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


def put_sql_report(report_type,  cvg_start_dt, cvg_end_dt, due_date,  email_1, email_2, additional_email_1, additional_email_2, status, report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # UPDATE row into Reports table
            # cursor.execute("""UPDATE public.reports SET report_type = %s, cvg_start_date = %s, cvg_end_date = %s, last_update_date = %s WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
            #                     (data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), datetime.now(), data.get('report_id'), cmte_id))

            if status=="Saved":
                cursor.execute("""UPDATE public.reports SET report_type = %s, cvg_start_date = %s, cvg_end_date = %s,  due_date = %s, email_1 = %s,  email_2 = %s,  additional_email_1 = %s,  additional_email_2 = %s, status = %s WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
                                [report_type,  cvg_start_dt, cvg_end_dt, due_date,  email_1, email_2, additional_email_1, additional_email_2, status, report_id, cmte_id])
            elif status=="Submitted":
                cursor.execute("""UPDATE public.reports SET report_type = %s, cvg_start_date = %s, cvg_end_date = %s,  due_date = %s, email_1 = %s,  email_2 = %s,  additional_email_1 = %s,  additional_email_2 = %s, status = %s, filed_date = last_update_date WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
                                [report_type,  cvg_start_dt, cvg_end_dt, due_date,  email_1, email_2, additional_email_1, additional_email_2, status, report_id, cmte_id])

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
        check_mandatory_fields_report(data)
        cmte_id = data.get('cmte_id')
        form_type = data.get('form_type')
        cvg_start_dt = data.get('cvg_start_dt')
        cvg_end_dt = data.get('cvg_end_dt')
        due_dt = data.get('due_dt')
        if cvg_start_dt is None:
            raise Exception('The cvg_start_dt is null.')
        if cvg_end_dt is None:
            raise Exception('The cvg_end_dt is null.')
        check_form_type(form_type)
        args = [cmte_id, form_type, cvg_start_dt, cvg_end_dt]
        forms_obj = []
        if not (cvg_start_dt is None or cvg_end_dt is None):
            forms_obj = check_list_cvg_dates(args)
        if len(forms_obj)== 0:
            report_id = get_next_report_id()
            data['report_id'] = str(report_id)
            try:
                post_sql_report(report_id, data.get('cmte_id'), data.get('form_type'), data.get('amend_ind'), data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('due_dt'), data.get('status'), data.get('email_1'), data.get('email_2'), data.get('additional_email_1'), data.get('additional_email_2'))

            except Exception as e:
                # Resetting Report ID
                get_prev_report_id(report_id)
                raise Exception('The post_sql_report function is throwing an error: ' + str(e))

            try:
                #Insert data into Form 3X table
                if data.get('form_type') == "F3X":
                    check_mandatory_fields_form3x(data)
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
                report_id = check_report_id(data.get('report_id'))
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
        check_mandatory_fields_report(data)
        cmte_id = data.get('cmte_id')  
        check_form_type(data.get('form_type'))
        report_id = check_report_id(data.get('report_id'))
        args = [cmte_id, data.get('form_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('report_id')]
        forms_obj = []
        if data.get('cvg_start_dt') is None:
            raise Exception('The cvg_start_dt is null.')
        if data.get('cvg_end_dt') is None:
            raise Exception('The cvg_end_dt is null.')
        if not (data.get('cvg_start_dt') is None or data.get('cvg_end_dt') is None):                        
            forms_obj = check_list_cvg_dates(args)
        if len(forms_obj)== 0:
            old_list_report = get_list_report(report_id, cmte_id)
            # print("before put_sql_report")
            put_sql_report(data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('due_date'), data.get('email_1'), data.get('email_2'), data.get('additional_email_1'), data.get('additional_email_2'), data.get('status'), data.get('report_id'), cmte_id)
            # print("after put_sql_report")
            old_dict_report = old_list_report[0]
            prev_report_type = old_dict_report.get('report_type')
            prev_cvg_start_dt = old_dict_report.get('cvg_start_date')
            prev_cvg_end_dt = old_dict_report.get('cvg_end_date')
            prev_last_update_date = old_dict_report.get('last_update_date')
                                           
            try:
                if data.get('form_type') == "F3X":
                    put_sql_form3x(data.get('report_type'), data.get('election_code'), data.get('date_of_election'), data.get('state_of_election'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('coh_bop'),  data.get('report_id'), cmte_id)                            
                output = get_reports(data)
            except Exception as e:
                    put_sql_report(prev_report_type, prev_cvg_start_dt, prev_cvg_end_dt, data.get('due_date'), data.get('email_1'), data.get('email_2'), data.get('additional_email_1'), data.get('additional_email_2'), data.get('status'), data.get('report_id'), cmte_id)
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
        report_id = check_report_id(data.get('report_id'))
        check_form_type(form_type)
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
                amend_ind = check_null_value(request.data.get('amend_ind'))
            else:
                amend_ind = "N"

            if 'election_code' in request.data:
                election_code = check_null_value(request.data.get('election_code'))
            else:
                election_code = None

            if 'status' in request.data:
                f_status = check_null_value(request.data.get('status'))
            else:
                f_status = "Saved"

            if 'email_1' in request.data:
                email_1 = check_email(request.data.get('email_1'))
            else:
                email_1 = None

            if 'email_2' in request.data:
                email_2 = check_email(request.data.get('email_2'))
            else:
                email_2 = None

            if 'additional_email_1' in request.data:
                additional_email_1 = check_email(request.data.get('additional_email_1'))
            else:
                additional_email_1 = None                
            
            if 'additional_email_2' in request.data:
                additional_email_2 = check_email(request.data.get('additional_email_2'))
            else:
                additional_email_2 = None
            
            datum = {
                'cmte_id': request.user.username,
                'form_type': check_null_value(request.data.get('form_type')),
                'amend_ind': amend_ind,
                'report_type': check_null_value(request.data.get('report_type')),
                'election_code': election_code,
                'date_of_election': date_format(request.data.get('date_of_election')),
                'state_of_election': check_null_value(request.data.get('state_of_election')),
                'cvg_start_dt': date_format(request.data.get('cvg_start_dt')),
                'cvg_end_dt': date_format(request.data.get('cvg_end_dt')),
                'due_dt': date_format(request.data.get('due_dt')),
                'coh_bop': int(request.data.get('coh_bop')),
                'status': f_status,
                'email_1': email_1,
                'email_2': email_2,
                'additional_email_1': additional_email_1,
                'additional_email_2': additional_email_2,
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
        # print("request.data", request.data)
        try:
            if 'amend_ind' in request.data:
                amend_ind = check_null_value(request.data.get('amend_ind'))
            else:
                amend_ind = "N"

            if 'election_code' in request.data:
                election_code = check_null_value(request.data.get('election_code'))
            else:
                election_code = ""

            if 'status' in request.data:
                f_status = check_null_value(request.data.get('status'))
            else:
                f_status = "Saved"

            if 'email_1' in request.data:
                email_1 = check_email(request.data.get('email_1'))
            else:
                email_1 = ""

            if 'email_2' in request.data:
                email_2 = check_email(request.data.get('email_2'))
            else:
                email_2 = ""

            if 'additional_email_1' in request.data:
                additional_email_1 = check_email(request.data.get('additional_email_1'))
            else:
                additional_email_1 = ""              
            
            if 'additional_email_2' in request.data:
                additional_email_2 = check_email(request.data.get('additional_email_2'))
            else:
                additional_email_2 = ""

            # print("f_status = ", f_status)
            # print("additional_email_1 = ", additional_email_1)
            # print("additional_email_2 = ", additional_email_2)
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
                'status': f_status,
                'email_1': email_1,
                'email_2': email_2,
                'additional_email_1': additional_email_1,
                'additional_email_2': additional_email_2,                
            }
            if 'amend_ind' in request.data:
                datum['amend_ind'] = request.data.get('amend_ind')
            
            if 'election_code' in request.data:
                datum['election_code'] = request.data.get('election_code')

            data = put_reports(datum)
            # print("data = ", data)
            if (f_status == 'Submitted' and data):
                return JsonResponse({'Submitted': True}, status=status.HTTP_201_CREATED, safe=False)    
            elif type(data) is dict:
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
        raise Exception('The Entity Type is not within the specified list: [' + ', '.join(entity_type_list) + ']. Input received: ' + entity_type)

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
        

def check_mandatory_fields_entity(data):
    try:
        list_mandatory_fields_entity = ['entity_type', 'cmte_id']
        error =[]
        for field in list_mandatory_fields_entity:
            if not(field in data and check_null_value(data.get(field))):
                error.append(field)
        if len(error) > 0:
            string = ""
            for x in error:
                string = string + x + ", "
            string = string[0:-2]
            raise Exception('The following mandatory fields are required in order to save data to Entity table: {}'.format(string))
    except:
        raise

def post_sql_entity(entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id):

    try:
        with connection.cursor() as cursor:

            # Insert data into Entity table
            cursor.execute("""INSERT INTO public.entity (entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id, create_date)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",[entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id, datetime.datetime.now()])
    except Exception:
        raise

def get_list_entity(entity_id, cmte_id):

    try:
        query_string = """SELECT entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix as prefix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id
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
        query_string = """SELECT entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix as prefix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id
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
        check_mandatory_fields_entity(data)
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
        check_mandatory_fields_entity(data)
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
                    'preffix': request.data.get('prefix'),
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
                'preffix': request.data.get('prefix'),
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
MODIFIED - CORE APP - SPRINT 15 - FNE 1222 - BY PRAVEEN JINKA
******************************************************************************************************************************
"""
"""
************************************************ FUNCTIONS - ENTITIES **********************************************************
"""
@api_view(['GET'])
############################ PARTIALLY IMPLEMENTED FOR INDIVIDUALS, ORGANIZATIONS, COMMITTEES. NOT IMPLEMENTED FOR CANDIDATES
def autolookup_search_contacts(request):

    try:
        commmitte_id = request.user.username
        param_string = ""
        order_string = ""
        search_string = ""
        query_string = ""

        for key, value in request.query_params.items():
            order_string = str(key)
            if key in ['entity_name', 'first_name', 'last_name']:
                parameters = [commmitte_id]
                param_string = " AND LOWER(" + str(key) + ") LIKE LOWER(%s)"
                query_string = """SELECT json_agg(t) FROM (SELECT entity_id, entity_type, cmte_id, entity_name, first_name, last_name, middle_name, preffix as prefix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id
                                                    FROM public.entity WHERE cmte_id = %s""" + param_string + """ AND delete_ind is distinct from 'Y' ORDER BY """ + order_string + """) t"""
                parameters.append(value + '%')
            elif key in ['cmte_id', 'cmte_name']:
                param_string = " LOWER(" + str(key) + ") LIKE LOWER(%s)"
                query_string = """SELECT json_agg(t) FROM (SELECT cmte_id, cmte_name, street_1, street_2, city, state, zip_code, cmte_email_1, cmte_email_2, phone_number, cmte_type, cmte_dsgn, cmte_filing_freq, cmte_filed_type, treasurer_last_name, treasurer_first_name, treasurer_middle_name, treasurer_prefix, treasurer_suffix
                                                    FROM public.committee_master WHERE""" + param_string + """ ORDER BY """ + order_string + """) t"""
                parameters = [value + '%']
            elif key in ['cand_id', 'cand_last_name', 'cand_first_name']:
                param_string = " LOWER(" + str(key) + ") LIKE LOWER(%s)"
                query_string = """SELECT json_agg(t) FROM (SELECT cand_id, cand_last_name, cand_first_name, cand_middle_name, cand_prefix, cand_suffix, cand_street_1, cand_street_2, cand_city, cand_state, cand_zip, cand_party_affiliation, cand_office, cand_office_state, cand_office_district, cand_election_year
                                                    FROM public.candidate_master WHERE""" + param_string + """ ORDER BY """ + order_string + """) t"""
                parameters = [value + '%']
            else:
                raise Exception("The parameters for this api should be limited to: ['entity_name', 'first_name', 'last_name', 'cmte_id', 'cmte_name', 'cand_id', 'cand_last_name', 'cand_first_name']")

        if query_string == "":
            raise Exception("One parameter has to be passed for this api to display results. The parameters should be limited to: ['entity_name', 'first_name', 'last_name', 'cmte_id', 'cmte_name', 'cand_id', 'cand_last_name', 'cand_first_name']")
        
        with connection.cursor() as cursor:
            cursor.execute(query_string, parameters)
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        status_value = status.HTTP_200_OK
        if forms_obj is None:
            forms_obj =[]
            status_value = status.HTTP_204_NO_CONTENT
        return Response(forms_obj, status=status_value)
    except Exception as e:
        return Response("The autolookup_search_contacts API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
*****************************************************************************************************************************
END - SEARCH ENTITIES API - CORE APP
******************************************************************************************************************************
"""

@api_view(["POST"])
def create_json_file(request):
    #creating a JSON file so that it is handy for all the public API's   
    try:
        # print("request.data['committeeid']= ", request.data['committeeid'])
        # print("request.data['reportid']", request.data['reportid'])

        #comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username, is_submitted=True).last()
        #comm_info = CommitteeInfo.objects.get(committeeid=request.data['committeeid'], id=request.data['reportid'])
        # print(CommitteeInfo)
        comm_info = CommitteeInfo.objects.filter(committeeid=request.data['committeeid'], id=request.data['reportid']).last()

        if comm_info:
            header = {
                "version":"8.3",
                "softwareName":"ABC Inc",
                "softwareVersion":"1.02 Beta",
                "additionalInfomation":"Any other useful information"
            }

            serializer = CommitteeInfoSerializer(comm_info)
            conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
            bucket = conn.get_bucket("dev-efile-repo")
            k = Key(bucket)
            k.content_type = "application/json"
            data_obj = {}
            data_obj['header'] = header

            f99data = {}
            f99data['committeeId'] = comm_info.committeeid
            f99data['committeeName'] = comm_info.committeename
            f99data['street1'] = comm_info.street1
            f99data['street2'] = comm_info.street2
            f99data['city'] = comm_info.city
            f99data['state'] = comm_info.state
            f99data['zipCode'] = str(comm_info.zipcode)
            f99data['treasurerLastName'] = comm_info.treasurerlastname
            f99data['treasurerFirstName'] = comm_info.treasurerfirstname
            f99data['treasurerMiddleName'] = comm_info.treasurermiddlename
            f99data['treasurerPrefix'] = comm_info.treasurerprefix
            f99data['treasurerSuffix'] = comm_info.treasurersuffix
            f99data['reason'] = comm_info.reason
            f99data['text'] = comm_info.text
            f99data['dateSigned'] = datetime.datetime.now().strftime('%m/%d/%Y')
            #f99data['dateSigned'] = '5/15/2019'
            f99data['email1'] = comm_info.email_on_file
            f99data['email2'] = comm_info.email_on_file_1
            f99data['formType'] = comm_info.form_type
            f99data['attachement'] = 'X'
            f99data['password'] = "test"

            #data_obj['data'] = serializer.data
            data_obj['data'] = f99data
            k.set_contents_from_string(json.dumps(data_obj))            
            url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")

            tmp_filename = '/tmp/' + comm_info.committeeid + '_' + str(comm_info.id) + '_f99.json'   
            #tmp_filename = comm_info.committeeid + '_' + str(comm_info.id) + '_f99.json'            
            vdata = {}
            # print ("url= ", url)
            # print ("tmp_filename= ", tmp_filename)


            vdata['wait'] = 'false'
            #print("vdata",vdata)
            json.dump(data_obj, open(tmp_filename, 'w'))

            #with open('data.json', 'w') as outfile:
            #   json.dump(data, outfile, ensure_ascii=False)
            
            #obj = open('data.json', 'w')
            #obj.write(serializer.data)
            #obj.close

            # variables to be sent along the JSON file in form-data
            filing_type='FEC'
            vendor_software_name='FECFILE'

            data_obj = {
                    'filing_type':filing_type,
                    'vendor_software_name':vendor_software_name,
                    'committeeId':comm_info.committeeid,
                    'password':'test',
                    'formType':comm_info.form_type,
                    'newAmendIndicator':'N',
                    'reportSequence':1,
                    'emailAddress1':comm_info.email_on_file,
                    'reportType':comm_info.reason,
                    'coverageStartDate':None,
                    'coverageEndDate':None,
                    'originalFECId':None,
                    'backDoorCode':None,
                    'emailAddress2': comm_info.email_on_file_1,
                    'wait':False
                }

            # print(data_obj)
            
            if not (comm_info.file in [None, '', 'null', ' ',""]):
                filename = comm_info.file.name 
                #print(filename)
                myurl = "https://{}.s3.amazonaws.com/media/".format(settings.AWS_STORAGE_BUCKET_NAME) + filename
                #myurl = "https://fecfile-filing.s3.amazonaws.com/media/" + filename
                #print(myurl)
                myfile = urllib.request.urlopen(myurl)

                #s3 = boto3.client('s3')

                #file_object = s3.get_object(Bucket='settings.AWS_STORAGE_BUCKET_NAME', Key='settings.MEDIAFILES_LOCATION' + "/" + 'comm_info.file')

                #attachment = open(file_object['Body'], 'rb')

        
                file_obj = {
                    'fecDataFile': ('data.json', open(tmp_filename, 'rb'), 'application/json'),
                    'fecAttachment': ('attachment.pdf', myfile, 'application/pdf')
                }
            else:
                file_obj = {
                    'fecDataFile': ('data.json', open(tmp_filename, 'rb'), 'application/json')
                }
    
                """
                    # printresp = requests.post("http://" + settings.NXG_FEC_API_URL + settings.NXG_FEC_API_VERSION + "f99/print_pdf", data=data_obj, files=file_obj)
                    # printresp = requests.post("http://" + settings.NXG_FEC_API_URL + settings.NXG_FEC_API_VERSION + "f99/print_pdf", data=data_obj, files=file_obj, headers={'Authorization': token_use})
                    printresp = requests.post(settings.NXG_FEC_PRINT_API_URL + settings.NXG_FEC_PRINT_API_VERSION, data=data_obj, files=file_obj)
                    if not printresp.ok:
                        return Response(printresp.json(), status=status.HTTP_400_BAD_REQUEST)
                    else:
                        #dictcreate = createresp.json()
                        dictprint = printresp.json()
                        merged_dict = {**update_json_data, **dictprint}
                        #merged_dict = {key: value for (key, value) in (dictcreate.items() + dictprint.items())}
                        return JsonResponse(merged_dict, status=status.HTTP_201_CREATED)
                        #return Response(printresp.json(), status=status.HTTP_201_CREATED)
                else:
                    return Response({"FEC Error 003":"This form Id number does not exist"}, status=status.HTTP_400_BAD_REQUEST)


                """
            # print(file_obj)
            #res = requests.post("http://" + settings.DATA_RECEIVE_API_URL + "/v1/send_data" , data=data_obj, files=file_obj)
            #mahi asked to changed on 05/17/2019
            res = requests.post("https://" +  settings.DATA_RECEIVE_API_URL + "/receiver/v1/upload_filing" , data=data_obj, files=file_obj)

            #import ipdb; ipdb.set_trace()
            # print(res.text)
            return Response(res.text, status=status.HTTP_200_OK)
            #return Response("successful", status=status.HTTP_200_OK)
            if not res.ok:
                return Response(res.json(), status=status.HTTP_400_BAD_REQUEST)
            else:
                #dictcreate = createresp.json()
                dictprint = res.json()
                merged_dict = {**update_json_data, **dictprint}
                #merged_dict = {key: value for (key, value) in (dictcreate.items() + dictprint.items())}
                return JsonResponse(merged_dict, status=status.HTTP_201_CREATED)
                #return Response(printresp.json(), status=status.HTTP_201_CREATED)
        else:
            return Response({"FEC Error 007":"This user does not have a submitted CommInfo object"}, status=status.HTTP_400_BAD_REQUEST)
            
    #except CommitteeInfo.DoesNotExist:
     #   return Response({"FEC Error 009":"An unexpected error occurred while processing your request"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response("The create_json_file API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

"""
******************************************************************************************************************************
END - GET ALL TRANSACTIONS API - CORE APP
******************************************************************************************************************************
"""

"""
**********************************************************************************************************************************************
TRANSACTIONS TABLE ENHANCE- GET ALL TRANSACTIONS API - CORE APP - SPRINT 11 - FNE 875 - BY  Yeswanth Kumar Tella
**********************************************************************************************************************************************
"""
def filter_get_all_trans(request, param_string):
    if request.method == 'GET':
        return param_string
    # import ipdb;ipdb.set_trace()
    filt_dict = request.data.get('filters', {})
    for f_key, value_d in filt_dict.items():
        if not value_d or value_d == 'null':
            continue
        if 'filterCategories' in f_key:
            cat_tuple = "('"+"','".join(value_d)+"')"
            param_string = param_string + " AND transaction_type_desc In " + cat_tuple
        if 'filterDateFrom' in f_key and 'filterDateTo' in filt_dict.keys():
            param_string = param_string + " AND transaction_date >= '" + value_d +"' AND transaction_date <= '" + filt_dict['filterDateTo'] +"'"
        # The below code was added by Praveen. This is added to reuse this function in get_all_trashed_transactions API.
        if 'filterDeletedDateFrom' in f_key and 'filterDeletedDateTo' in filt_dict.keys():
            param_string = param_string + " AND date(last_update_date) >= '" + value_d +"' AND date(last_update_date) <= '" + filt_dict['filterDeletedDateTo'] +"'"
        # End of Addition
        if 'filterAmountMin' in f_key and 'filterAmountMax' in filt_dict.keys():
            param_string = param_string + " AND transaction_amount >= " + str(value_d) +" AND transaction_amount <= " + str(filt_dict['filterAmountMax'])
        if 'filterAggregateAmountMin' in f_key and 'filterAggregateAmountMax' in filt_dict.keys():
            param_string = param_string + " AND aggregate_amt >= " + str(value_d) +" AND aggregate_amt <= " + str(filt_dict['filterAggregateAmountMax'])
        if 'filterStates' in f_key:
            state_tuple = "('"+"','".join(value_d)+"')"
            param_string = param_string + " AND state In " + state_tuple
        if 'filterItemizations' in f_key:
            itemized_tuple = "('"+"','".join(value_d)+"')"
            param_string = param_string + " AND itemized In " + itemized_tuple
    return param_string

# def get_aggregate_amount(transaction_id):
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("""SELECT COALESCE(SUM(contribution_amount),0) FROM public.sched_a WHERE transaction_id = %s AND delete_ind is distinct FROM 'Y'""", [transaction_id])
#             aggregate_amt = cursor.fetchone()[0]
#         return aggregate_amt
#     except Exception as  e:
#         return False
#         raise Exception('The aggregate_amount function is throwing an error: ' + str(e))


@api_view(['PUT'])
def trash_restore_transactions(request):
    """api for trash and resore transactions. 
       we are doing soft-delete only, mark delete_ind to 'Y'
       
       request payload in this format:
{
    "actions": [
        {
            "action": "restore",
            "reportid": "123",
            "transactionId": "SA20190610000000087"
        },
        {
            "action": "trash",
            "reportid": "456",
            "transactionId": "SA20190610000000087"
        }
    ]
}
 
    """
    for _action in request.data.get('actions', []):
        report_id = _action.get('report_id', '')
        transaction_id = _action.get('transaction_id', '')

        action = _action.get('action', '')
        _delete = 'Y' if action == 'trash' else ''
        try:
            trash_restore_sql_transaction( 
                report_id,
                transaction_id, 
                _delete)
        except Exception as e:
            return Response("The trash_restore_transactions API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    return Response({"result":"success"}, status=status.HTTP_200_OK)


def trash_restore_sql_transaction(report_id, transaction_id, _delete='Y'):
    """trash or restore sched_a transaction by updating delete_ind"""
    try:
        with connection.cursor() as cursor:
            # UPDATE delete_ind flag to Y in DB
            _sql = """
            UPDATE public.sched_a 
            SET delete_ind = '{}'
            WHERE report_id = '{}'
            AND transaction_id = '{}'""".format(_delete, report_id, transaction_id)
            cursor.execute(_sql)
            if (cursor.rowcount == 0):
                raise Exception(
                    'The transaction ID: {} is either already deleted or does not exist in Entity table'.format(entity_id))
    except Exception:
        raise

@api_view(['GET', 'POST'])
def get_all_transactions(request):
    try:
        # print("request.data: ", request.data)
        cmte_id = request.user.username
        param_string = ""
        page_num = int(request.data.get('page', 1))
        descending = request.data.get('descending', 'false')
        sortcolumn = request.data.get('sortColumnName')
        itemsperpage = request.data.get('itemsPerPage', 5)
        search_string = request.data.get('search')
        # import ipdb;ipdb.set_trace()
        params = request.data.get('filters', {})
        keywords = params.get('keywords')
        report_id = request.data.get('reportid')
        if str(descending).lower() == 'true':
            descending = 'DESC'
        else:
            descending = 'ASC'
        # if 'order_params' in request.query_params:
        #     order_string = request.query_params.get('order_params')
        # else:
        #     order_string = "transaction_id"
        # import ipdb;ipdb.set_trace()
        keys = ['transaction_type','transaction_type_desc', 'transaction_id', 'name', 
            'street_1', 'street_2', 'city', 'state', 'zip_code','purpose_description', 
            'occupation', 'employer', 'memo_text']
        search_keys = ['transaction_type','transaction_type_desc', 'transaction_id', 'name', 
            'street_1', 'street_2', 'city', 'state', 'zip_code', 'purpose_description', 
            'occupation', 'employer', 'memo_text']
        if search_string:
            for key in search_keys:
                if not param_string:
                    param_string = param_string + " AND (CAST(" + key + " as CHAR(100)) ILIKE '%" + str(search_string) +"%'"
                else:
                    param_string = param_string + " OR CAST(" + key + " as CHAR(100)) ILIKE '%" + str(search_string) +"%'"
            param_string = param_string + " )"
        keywords_string = ''
        if keywords:
            for key in keys:
                for word in keywords:
                    if '"' in word:
                        continue
                    elif "'" in word:
                        if not keywords_string:
                            keywords_string = keywords_string + " AND ( CAST(" + key + " as CHAR(100)) = " + str(word)
                        else:
                            keywords_string = keywords_string + " OR CAST(" + key + " as CHAR(100)) = " + str(word)
                    else:
                        if not keywords_string:
                            keywords_string = keywords_string + " AND ( CAST(" + key + " as CHAR(100)) ILIKE '%" + str(word) +"%'"
                        else:
                            keywords_string = keywords_string + " OR CAST(" + key + " as CHAR(100)) ILIKE '%" + str(word) +"%'"
            keywords_string = keywords_string + " )"
        param_string = param_string + keywords_string
        param_string = filter_get_all_trans(request, param_string)
        
        # for key, value in request.query_params.items():
        #     try:
        #         check_value = int(value)
        #         param_string = param_string + " AND " + key + "=" + str(value)
        #     except Exception as e:
        #         if key == 'transaction_date':
        #             transaction_date = date_format(request.query_params.get('transaction_date'))
        #             param_string = param_string + " AND " + key + "='" + str(transaction_date) + "'"
        #         else:
        #             param_string = param_string + " AND LOWER(" + key + ") LIKE LOWER('" + value +"%')"
        query_string = """SELECT count(*) total_transactions,sum((case when memo_code is null then transaction_amount else 0 end)) total_transaction_amount from all_transactions_view
                           where cmte_id='""" + cmte_id + """' AND report_id=""" + str(report_id)+""" """ + param_string + """ AND delete_ind is distinct from 'Y'"""
                           # + """ ORDER BY """ + order_string
        # print(query_string)
        with connection.cursor() as cursor:
            cursor.execute(query_string)
            result = cursor.fetchone()
            count = result[0]
            sum_trans = result[1]
        filters_post = request.data.get('filters', {})
        memo_code_d = filters_post.get('filterMemoCode', False)
        if str(memo_code_d).lower() == 'true':
            param_string = param_string + " AND memo_code IS NOT NULL AND memo_code != ''"
        
        trans_query_string = """SELECT transaction_type, transaction_type_desc, transaction_id, name, street_1, street_2, city, state, zip_code, transaction_date, transaction_amount, aggregate_amt, purpose_description, occupation, employer, memo_code, memo_text, itemized from all_transactions_view
                                    where cmte_id='""" + cmte_id + """' AND report_id=""" + str(report_id)+""" """ + param_string + """ AND delete_ind is distinct from 'Y'"""
                                    # + """ ORDER BY """ + order_string
        # print("trans_query_string: ",trans_query_string)
        # import ipdb;ipdb.set_trace()
        if sortcolumn and sortcolumn != 'default':
            trans_query_string = trans_query_string + """ ORDER BY """+ sortcolumn + """ """ + descending
        elif sortcolumn == 'default':
            trans_query_string = trans_query_string + """ ORDER BY name ASC, transaction_date  ASC""" 
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + trans_query_string + """) t""")
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
                forms_obj = data_row[0]
                if forms_obj is None:
                    forms_obj =[]
                    status_value = status.HTTP_200_OK
                else:
                    for d in forms_obj:
                        for i in d:
                            if not d[i] and i not in ['transaction_amount', 'aggregate_amt']:
                                d[i] = ''
                            elif not d[i]:
                                d[i] = 0
                        #agg_amount = get_aggregate_amount(d['transaction_id'])
                        #d['aggregate_amount'] =round(agg_amount, 2)   
                    status_value = status.HTTP_200_OK
        
        #import ipdb; ipdb.set_trace()
        total_count = len(forms_obj)
        paginator = Paginator(forms_obj, itemsperpage)
        if paginator.num_pages < page_num:
            page_num = paginator.num_pages
        forms_obj = paginator.page(page_num)
        json_result = {'transactions': list(forms_obj), 'totalAmount': sum_trans, 'totalTransactionCount': count,
                    'itemsPerPage': itemsperpage, 'pageNumber': page_num,'totalPages':paginator.num_pages}
        # json_result = { 'transactions': forms_obj, 'totalAmount': sum_trans, 'totalTransactionCount': count}
        return Response(json_result, status=status_value)
    except Exception as e:
        return Response("The get_all_transactions API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


"""
*****************************************************************************************************************************
END - GET ALL TRANSACTIONS API - CORE APP
******************************************************************************************************************************
"""

"""
********************************************************************************************************************************
STATE API- CORE APP - SPRINT 9 - FNE ??? - BY PRAVEEN JINKA 
********************************************************************************************************************************
"""
@api_view(['GET'])
def state(request):

    try:
        with connection.cursor() as cursor:
            forms_obj= {}
            cursor.execute("SELECT json_agg(t) FROM (SELECT state_code, state_description, st_number FROM public.ref_states order by st_number) t")
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
                
        if forms_obj is None:
            return Response("The ref_states table is empty", status=status.HTTP_400_BAD_REQUEST)                              
        
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The states API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
END - STATE API - CORE APP
******************************************************************************************************************************
"""
"""
******************************************************************************************************************************
GET ALL TRASHED TRANSACTIONS API - CORE APP - SPRINT 9 - FNE 744 - BY PRAVEEN JINKA
REWRITTEN TO MATCH GET ALL TRANSACTIONS API - CORE APP - SPRINT 16 - FNE 744 - BY PRAVEEN JINKA
******************************************************************************************************************************
"""
@api_view(['POST'])
def get_all_trashed_transactions(request):
    try:
        cmte_id = request.user.username
        param_string = ""
        page_num = int(request.data.get('page', 1))
        descending = request.data.get('descending', 'false')
        sortcolumn = request.data.get('sortColumnName')
        itemsperpage = request.data.get('itemsPerPage', 5)
        search_string = request.data.get('search')
        params = request.data.get('filters', {})
        keywords = params.get('keywords')
        report_id = request.data.get('reportid')
        if str(descending).lower() == 'true':
            descending = 'DESC'
        else:
            descending = 'ASC'

        keys = ['transaction_type','transaction_type_desc', 'transaction_id', 'name', 
            'street_1', 'street_2', 'city', 'state', 'zip_code','purpose_description', 
            'occupation', 'employer', 'memo_text']
        search_keys = ['transaction_type','transaction_type_desc', 'transaction_id', 'name', 
            'street_1', 'street_2', 'city', 'state', 'zip_code', 'purpose_description', 
            'occupation', 'employer', 'memo_text']
        if search_string:
            for key in search_keys:
                if not param_string:
                    param_string = param_string + " AND ( CAST(" + key + " as CHAR(100)) ILIKE '%" + str(search_string) +"%'"
                else:
                    param_string = param_string + " OR CAST(" + key + " as CHAR(100)) ILIKE '%" + str(search_string) +"%'"
            param_string = param_string + " )"
        keywords_string = ''
        if keywords:
            for key in keys:
                for word in keywords:
                    if '"' in word:
                        continue
                    elif "'" in word:
                        if not keywords_string:
                            keywords_string = keywords_string + " AND ( CAST(" + key + " as CHAR(100)) = " + str(word)
                        else:
                            keywords_string = keywords_string + " OR CAST(" + key + " as CHAR(100)) = " + str(word)
                    else:
                        if not keywords_string:
                            keywords_string = keywords_string + " AND ( CAST(" + key + " as CHAR(100)) ILIKE '%" + str(word) +"%'"
                        else:
                            keywords_string = keywords_string + " OR CAST(" + key + " as CHAR(100)) ILIKE '%" + str(word) +"%'"
            keywords_string = keywords_string + " )"
        param_string = param_string + keywords_string
        param_string = filter_get_all_trans(request, param_string)

        filters_post = request.data.get('filters', {})
        memo_code_d = filters_post.get('filterMemoCode', False)
        if str(memo_code_d).lower() == 'true':
            param_string = param_string + " AND memo_code IS NOT NULL"

        trans_query_string = """SELECT transaction_type as "transactionTypeId", transaction_type_desc as "type", transaction_id as "transactionId", name, street_1 as "street", street_2 as "street2", city, state, zip_code as "zip", transaction_date as "date", date(last_update_date) as "deletedDate", COALESCE(transaction_amount,0) as "amount", COALESCE(aggregate_amt,0) as "aggregate", purpose_description as "purposeDescription", occupation as "contributorOccupation", employer as "contributorEmployer", memo_code as "memoCode", memo_text as "memoText", itemized from all_transactions_view
                                    where cmte_id='""" + cmte_id + """' AND report_id=""" + str(report_id)+""" """ + param_string + """ AND delete_ind = 'Y'"""

        if sortcolumn and sortcolumn != 'default':
            sortcolumn_dict = {'transactionTypeId': 'transaction_type',
                                'type': 'transaction_type_desc',
                                'transactionId': 'transaction_id',
                                'name': 'name',
                                'street': 'street_1',
                                'street2': 'street_2',
                                'city': 'city',
                                'state': 'state',
                                'zip': 'zip_code',
                                'date': 'transaction_date',
                                'deletedDate': 'last_update_date',
                                'amount': 'COALESCE(transaction_amount,0)',
                                'aggregate': 'COALESCE(aggregate_amt,0)',
                                'purposeDescription': 'purpose_description',
                                'contributorOccupation': 'occupation',
                                'contributorEmployer': 'employer',
                                'memoCode': 'memo_code',
                                'memoText': 'memo_text',
                                'itemized': 'itemized'}
            if sortcolumn in sortcolumn_dict:
                sorttablecolumn = sortcolumn_dict[sortcolumn]
            else:
                sorttablecolumn = 'name ASC, transaction_date'
            trans_query_string = trans_query_string + """ ORDER BY """+ sorttablecolumn + """ """ + descending
        elif sortcolumn == 'default':
            trans_query_string = trans_query_string + """ ORDER BY name ASC, transaction_date ASC"""
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + trans_query_string + """) t""")
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
                if forms_obj is None:
                    forms_obj =[]
                    status_value = status.HTTP_200_OK
                else:
                    for d in forms_obj:
                        for i in d:
                            if d[i] in [None, '', ""]:
                                d[i] = ''
                    status_value = status.HTTP_200_OK

        total_count = len(forms_obj)
        paginator = Paginator(forms_obj, itemsperpage)
        if paginator.num_pages < page_num:
            page_num = paginator.num_pages
        forms_obj = paginator.page(page_num)
        json_result = {'transactions': list(forms_obj), 'totalTransactionCount': total_count,
                    'itemsPerPage': itemsperpage, 'pageNumber': page_num,'totalPages':paginator.num_pages}
        return Response(json_result, status=status_value)
    except Exception as e:
        return Response("The get_all_trashed_transactions API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

"""
******************************************************************************************************************************
END - GET ALL TRASHED TRANSACTIONS API - CORE APP
******************************************************************************************************************************
"""
"""
******************************************************************************************************************************
GET ALL DELETE TRANSACTIONS API-- CORE APP- SPRINT-17 -BY YESWANTH KUMAR TELLA 
******************************************************************************************************************************
"""
def get_SA_from_transaction_data(trans_id):
    try:
        query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, (CASE WHEN aggregate_amt IS NULL THEN 0.0 ELSE aggregate_amt END) AS aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, transaction_type_identifier, donor_cmte_id, donor_cmte_name
                     FROM public.sched_a WHERE transaction_id = %s """
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [trans_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            pass
   
        return forms_obj
    except Exception:
        raise

def get_list_report_data(report_id, cmte_id):
    try:
        query_string = """SELECT report_id, form_type, amend_ind, status, amend_number, cmte_id, report_type
                     FROM public.reports WHERE report_id = %s AND cmte_id = %s """
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [report_id, cmte_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            raise NoOPError('The report ID: {} does not exist or is deleted'.format(report_id))   
        return forms_obj
    except Exception:
        raise

@api_view(['POST'])
def delete_trashed_transactions(request):
    try:
    #import ipdb;ipdb.set_trace()
        trans_id = request.data.get('transaction_id',[])
        committeeid = request.user.username
        message='Transaction deleted successfully' 
        sched_a_obj = get_SA_from_transaction_data(trans_id)[0]
        print(sched_a_obj)
        if sched_a_obj:
           
            report_info = get_list_report_data(sched_a_obj['report_id'], committeeid)[0]
            #print(report_info)
            if report_info and report_info['status'] == 'Submitted':
               message = 'The transaction report is submitted.'
            elif report_info and report_info['status'] == None:
                message = 'The transaction report is None.'
            else:
                try:

                    with connection.cursor() as cursor:
                        cursor.execute("""Delete FROM public.sched_a where transaction_id IN %s;""",[trans_id])
                        #message = 'Transaction deleted successfully'
                except Exception as e:
                    print(e)
                    message = 'Error in deleting the transaction'

        json_result = {'message':message}
        return Response(json_result, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response('The delete_trashed_transactions API is throwing an error: ' + str(e), status=status.HTTP_400_BAD_REQUEST)


"""
******************************************************************************************************************************
END - GET ALL TRASHED TRANSACTIONS API - CORE APP
******************************************************************************************************************************
"""
"""
******************************************************************************************************************************
GET SUMMARY TABLE API - CORE APP - SPRINT 10 - FNE 720 - BY PRAVEEN JINKA
DISBURSEMENT FUNCTIONALITY ADDED - SPRINT 13 - FNE 1094 - BY PRAVEEN JINKA
******************************************************************************************************************************
"""
def check_calendar_year(calendar_year):

    try:
        if not(len(calendar_year) == 4 and calendar_year.isdigit()):
            raise Exception('Invalid Input: The calendar_year input should be a 4 digit integer like 2018, 1927. Input received: {}'.format(calendar_year))
        return calendar_year
    except Exception as e:
        raise

def period_receipts_sql(cmte_id, report_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT line_number, COALESCE(contribution_amount,0) FROM public.sched_a WHERE memo_code IS NULL AND cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            return cursor.fetchall()
    except Exception as e:
        raise Exception('The period_receipts_sql function is throwing an error: ' + str(e))

def period_receipts_for_summary_table_sql(calendar_start_dt, calendar_end_dt, cmte_id, report_id ):
    try:
        with connection.cursor() as cursor:
            #cursor.execute("SELECT line_number, contribution_amount FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            cursor.execute("SELECT line_number, COALESCE(contribution_amount,0), ( select COALESCE(sum(contribution_amount),0) as contribution_amount_ytd FROM public.sched_a t2 WHERE t2.memo_code IS NULL AND t2.line_number = t1.line_number AND T2.cmte_id = T1.cmte_id AND t2.contribution_date BETWEEN %s AND %s )  FROM public.sched_a t1 WHERE t1.memo_code IS NULL AND t1.cmte_id = %s AND t1.report_id = %s AND t1.delete_ind is distinct from 'Y'", [calendar_start_dt, calendar_end_dt, cmte_id, report_id])
            return cursor.fetchall()
    except Exception as e:
        raise Exception('The period_receipts_for_summary_table_sql function is throwing an error: ' + str(e))


def calendar_receipts_sql(cmte_id, calendar_start_dt, calendar_end_dt):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT line_number, COALESCE(contribution_amount,0) FROM public.sched_a WHERE memo_code IS NULL AND cmte_id = %s AND delete_ind is distinct from 'Y' AND contribution_date BETWEEN %s AND %s", [cmte_id, calendar_start_dt, calendar_end_dt])
            return cursor.fetchall()
    except Exception as e:
        raise Exception('The calendar_receipts_sql function is throwing an error: ' + str(e))

def period_disbursements_sql(cmte_id, report_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT line_number, COALESCE(expenditure_amount,0) FROM public.sched_b WHERE memo_code IS NULL AND cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            return cursor.fetchall()
    except Exception as e:
        raise Exception('The period_disbursements_sql function is throwing an error: ' + str(e))

def period_disbursements_for_summary_table_sql(calendar_start_dt, calendar_end_dt, cmte_id, report_id):
    try:
        with connection.cursor() as cursor:
            #cursor.execute("SELECT line_number, expenditure_amount FROM public.sched_b WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            cursor.execute("SELECT line_number, COALESCE(expenditure_amount,0), ( select COALESCE(sum(expenditure_amount),0) as expenditure_amount_ytd FROM public.sched_b t2 WHERE t2.memo_code IS NULL AND t2.line_number = t1.line_number AND T2.cmte_id = T1.cmte_id AND t2.expenditure_date BETWEEN %s AND %s ) FROM public.sched_b t1 WHERE t1.memo_code IS NULL AND t1.cmte_id = %s AND t1.report_id = %s AND t1.delete_ind is distinct from 'Y'", [calendar_start_dt, calendar_end_dt, cmte_id, report_id])
            return cursor.fetchall()
    except Exception as e:
        raise Exception('The period_disbursements_for_summary_table_sql function is throwing an error: ' + str(e))

# def summary_disbursements(args):
#     try:
        
#         XXIAI_amount = 0
#         XXIAII_amount = 0
#         XXIB_amount = 0
#         XXI_amount = 0
#         XXII_amount = 0
#         XXIII_amount = 0
#         XXIV_amount = 0
#         XXV_amount = 0
#         XXVI_amount = 0
#         XXVII_amount = 0
#         XXVIIIA_amount = 0
#         XXVIIIB_amount = 0
#         XXVIIIC_amount = 0
#         XXVIII_amount = 0
#         XXIX_amount = 0
#         XXXAI_amount = 0
#         XXXAII_amount = 0
#         XXXB_amount = 0
#         XXX_amount = 0
#         XXXI_amount = 0
#         XXXII_amount = 0       

#         if len(args) == 2:
#             cmte_id = args[0]
#             report_id = args[1]
#             sql_output = period_disbursements_sql(cmte_id, report_id)
#         else:
#             cmte_id = args[0]
#             calendar_start_dt = args[1]
#             calendar_end_dt = args[2]
#             sql_output = calendar_disbursements_sql(cmte_id, calendar_start_dt, calendar_end_dt)

#         for row in sql_output:
#             data_row = list(row)
#             if data_row[0] == '21AI':
#                 XXIAI_amount = XXIAI_amount + data_row[1]
#             if data_row[0] == '21AII':
#                 XXIAII_amount = XXIAII_amount + data_row[1]
#             if data_row[0] == '21B':
#                 XXIB_amount = XXIB_amount + data_row[1]
#             if data_row[0] == '22':
#                 XXII_amount = XXII_amount + data_row[1]
#             if data_row[0] == '23':
#                 XXIII_amount = XXIII_amount + data_row[1]
#             if data_row[0] == '24':
#                 XXIV_amount = XXIV_amount + data_row[1]
#             if data_row[0] == '25':
#                 XXV_amount = XXV_amount + data_row[1]
#             if data_row[0] == '26':
#                 XXVI_amount = XXVI_amount + data_row[1]
#             if data_row[0] == '27':
#                 XXVII_amount = XXVII_amount + data_row[1]
#             if data_row[0] == '28A':
#                 XXVIIIA_amount = XXVIIIA_amount + data_row[1]
#             if data_row[0] == '28B':
#                 XXVIIIB_amount = XXVIIIB_amount + data_row[1]
#             if data_row[0] == '28C':
#                 XXVIIIC_amount = XXVIIIC_amount + data_row[1]
#             if data_row[0] == '29':
#                 XXIX_amount = XXIX_amount + data_row[1]
#             if data_row[0] == '30AI':
#                 XXXAI_amount = XXXAI_amount + data_row[1]
#             if data_row[0] == '30AII':
#                 XXXAII_amount = XXXAII_amount + data_row[1]
#             if data_row[0] == '30B':
#                 XXXB_amount = XXXB_amount + data_row[1]

#         XXI_amount = XXIAI_amount + XXIAII_amount + XXIB_amount
#         XXVIII_amount = XXVIIIA_amount + XXVIIIB_amount + XXVIIIC_amount
#         XXX_amount = XXXAI_amount + XXXAII_amount + XXXB_amount
#         XXXI_amount = XXI_amount + XXII_amount + XXIII_amount + XXIV_amount + XXV_amount + XXVI_amount + XXVII_amount + XXVIII_amount + XXIX_amount + XXX_amount
#         XXXII_amount = XXXI_amount - XXIAII_amount - XXXAII_amount

#         summary_disbursement_list = [ {'line_item':'31', 'level':1, 'description':'Total Disbursements', 'amt':XXXI_amount},
#                                 {'line_item':'21', 'level':1, 'description':'Operating Expenditures', 'amt':XXI_amount},
#                                 {'line_item':'21AI', 'level':2, 'description':'Total Individual Contributions', 'amt':XXIAI_amount},
#                                 {'line_item':'21AII', 'level':2, 'description':'Itemized Individual Contributions', 'amt':XXIAII_amount},
#                                 {'line_item':'21B', 'level':2, 'description':'Unitemized Individual Contributions', 'amt':XXIB_amount},
#                                 {'line_item':'22', 'level':1, 'description':'Party Committee Contributions', 'amt':XXII_amount},
#                                 {'line_item':'23', 'level':1, 'description':'Other Committee Contributions', 'amt':XXIII_amount},
#                                 {'line_item':'24', 'level':1, 'description':'Transfers From Affiliated Committees', 'amt':XXIV_amount},
#                                 {'line_item':'25', 'level':1, 'description':'All Loans Received', 'amt':XXV_amount},
#                                 {'line_item':'27', 'level':1, 'description':'Loan Repayments Received', 'amt':XXVII_amount},
#                                 {'line_item':'26', 'level':1, 'description':'Offsets to Operating Expenditures', 'amt':XXVI_amount},
#                                 {'line_item':'28', 'level':1, 'description':'Candidate Refunds', 'amt':XXVIII_amount},
#                                 {'line_item':'28A', 'level':2, 'description':'Other Receipts', 'amt':XXVIIIA_amount},
#                                 {'line_item':'28B', 'level':2, 'description':'Total Transfers', 'amt':XXVIIIB_amount},
#                                 {'line_item':'28C', 'level':2, 'description':'Non-Federal Transfers', 'amt':XXVIIIC_amount},
#                                 {'line_item':'29', 'level':1, 'description':'Levin Funds', 'amt':XXIX_amount},
#                                 {'line_item':'30', 'level':1, 'description':'Total Federal Receipts', 'amt':XXX_amount},
#                                 {'line_item':'30AI', 'level':2, 'description':'Total Federal Receipts', 'amt':XXXAI_amount},
#                                 {'line_item':'30AII', 'level':2, 'description':'Total Federal Receipts', 'amt':XXXAII_amount},
#                                 {'line_item':'30B', 'level':2, 'description':'Total Federal Receipts', 'amt':XXXB_amount},
#                                 {'line_item':'32', 'level':1, 'description':'Total Federal Receipts', 'amt':XXXII_amount},
#                                 ]
   
#         return summary_disbursement_list
#     except Exception as e:
#         raise Exception('The summary_receipts API is throwing the error: ' + str(e))

# def summary_receipts(args):
#     try:
#         XIAI_amount = 0
#         XIAII_amount = 0
#         XIA_amount = 0
#         XIB_amount = 0
#         XIC_amount = 0
#         XID_amount = 0
#         XII_amount = 0
#         XIII_amount = 0
#         XIV_amount = 0
#         XV_amount = 0
#         XVI_amount = 0
#         XVII_amount = 0
#         XVIIIA_amount = 0
#         XVIIIB_amount = 0
#         XVIII_amount = 0
#         XIX_amount = 0
#         XX_amount = 0

#         if len(args) == 2:
#             cmte_id = args[0]
#             report_id = args[1]
#             sql_output = period_receipts_sql(cmte_id, report_id)
#         else:
#             cmte_id = args[0]
#             calendar_start_dt = args[1]
#             calendar_end_dt = args[2]
#             sql_output = calendar_receipts_sql(cmte_id, calendar_start_dt, calendar_end_dt)

#         for row in sql_output:
#             data_row = list(row)
#             if data_row[0] == '11AI':
#                 XIAI_amount = XIAI_amount + data_row[1]
#             if data_row[0] == '11AII':
#                 XIAII_amount = XIAII_amount + data_row[1]
#             if data_row[0] == '11B':
#                 XIB_amount = XIB_amount + data_row[1]
#             if data_row[0] == '11C':
#                 XIC_amount = XIC_amount + data_row[1]
#             if data_row[0] == '12':
#                 XII_amount = XII_amount + data_row[1]
#             if data_row[0] == '13':
#                 XIII_amount = XIII_amount + data_row[1]
#             if data_row[0] == '14':
#                 XIV_amount = XIV_amount + data_row[1]
#             if data_row[0] == '15':
#                 XV_amount = XV_amount + data_row[1]
#             if data_row[0] == '16':
#                 XVI_amount = XVI_amount + data_row[1]
#             if data_row[0] == '17':
#                 XVII_amount = XVII_amount + data_row[1]
#             if data_row[0] == '18A':
#                 XVIIIA_amount = XVIIIA_amount + data_row[1]
#             if data_row[0] == '18B':
#                 XVIIIB_amount = XVIIIB_amount + data_row[1]

#         XIA_amount = XIAI_amount + XIAII_amount
#         XID_amount = XIA_amount + XIB_amount + XIC_amount
#         XVIII_amount = XVIIIA_amount + XVIIIB_amount
#         XIX_amount =  XID_amount + XII_amount + XIII_amount + XIV_amount + XV_amount + XVI_amount + XVII_amount + XVIII_amount
#         XX_amount = XIX_amount - XVIII_amount

#         summary_receipt_list = [ {'line_item':'19', 'level':1, 'description':'Total Receipts', 'amt':XIX_amount},
#                                 {'line_item':'11D', 'level':1, 'description':'Total Contributions', 'amt':XID_amount},
#                                 {'line_item':'11A', 'level':2, 'description':'Total Individual Contributions', 'amt':XIA_amount},
#                                 {'line_item':'11AI', 'level':3, 'description':'Itemized Individual Contributions', 'amt':XIAI_amount},
#                                 {'line_item':'11AII', 'level':3, 'description':'Unitemized Individual Contributions', 'amt':XIAII_amount},
#                                 {'line_item':'11B', 'level':2, 'description':'Party Committee Contributions', 'amt':XIB_amount},
#                                 {'line_item':'11C', 'level':2, 'description':'Other Committee Contributions', 'amt':XIC_amount},
#                                 {'line_item':'12', 'level':1, 'description':'Transfers From Affiliated Committees', 'amt':XII_amount},
#                                 {'line_item':'13', 'level':1, 'description':'All Loans Received', 'amt':XIII_amount},
#                                 {'line_item':'14', 'level':1, 'description':'Loan Repayments Received', 'amt':XIV_amount},
#                                 {'line_item':'15', 'level':1, 'description':'Offsets to Operating Expenditures', 'amt':XV_amount},
#                                 {'line_item':'16', 'level':1, 'description':'Candidate Refunds', 'amt':XVI_amount},
#                                 {'line_item':'17', 'level':1, 'description':'Other Receipts', 'amt':XVII_amount},
#                                 {'line_item':'18', 'level':1, 'description':'Total Transfers', 'amt':XVIII_amount},
#                                 {'line_item':'18A', 'level':2, 'description':'Non-Federal Transfers', 'amt':XVIIIA_amount},
#                                 {'line_item':'18B', 'level':2, 'description':'Levin Funds', 'amt':XVIIIB_amount},
#                                 {'line_item':'20', 'level':1, 'description':'Total Federal Receipts', 'amt':XX_amount},
#                                 ]
#         
#         return summary_receipt_list
#     except Exception as e:
#         raise Exception('The summary_receipts API is throwing the error: ' + str(e))

def summary_disbursements_for_sumamry_table(args):
    try:
        
        XXIAI_amount = 0
        XXIAII_amount = 0
        XXIB_amount = 0
        XXI_amount = 0
        XXII_amount = 0
        XXIII_amount = 0
        XXIV_amount = 0
        XXV_amount = 0
        XXVI_amount = 0
        XXVII_amount = 0
        XXVIIIA_amount = 0
        XXVIIIB_amount = 0
        XXVIIIC_amount = 0
        XXVIII_amount = 0
        XXIX_amount = 0
        XXXAI_amount = 0
        XXXAII_amount = 0
        XXXB_amount = 0
        XXX_amount = 0
        XXXI_amount = 0
        XXXII_amount = 0       

        XXIAI_amount_ytd = 0
        XXIAII_amount_ytd = 0
        XXIB_amount_ytd = 0
        XXI_amount_ytd = 0
        XXII_amount_ytd = 0
        XXIII_amount_ytd = 0
        XXIV_amount_ytd = 0
        XXV_amount_ytd = 0
        XXVI_amount_ytd = 0
        XXVII_amount_ytd = 0
        XXVIIIA_amount_ytd = 0
        XXVIIIB_amount_ytd = 0
        XXVIIIC_amount_ytd = 0
        XXVIII_amount_ytd = 0
        XXIX_amount_ytd = 0
        XXXAI_amount_ytd = 0
        XXXAII_amount_ytd = 0
        XXXB_amount_ytd = 0
        XXX_amount_ytd = 0
        XXXI_amount_ytd = 0
        XXXII_amount_ytd = 0               

        '''
        if len(args) == 2:
            cmte_id = args[0]
            report_id = args[1]
            sql_output = period_disbursements_sql(cmte_id, report_id)
        else:
            cmte_id = args[0]
            calendar_start_dt = args[1]
            calendar_end_dt = args[2]
            sql_output = calendar_disbursements_sql(cmte_id, calendar_start_dt, calendar_end_dt)
        '''
        calendar_start_dt = args[0]
        calendar_end_dt = args[1]
        cmte_id = args[2]
        report_id = args[3]

        sql_output = period_disbursements_for_summary_table_sql(calendar_start_dt, calendar_end_dt, cmte_id, report_id )
        for row in sql_output:
            data_row = list(row)
            if data_row[0] == '21AI':
                XXIAI_amount = XXIAI_amount + data_row[1]
                XXIAI_amount_ytd = data_row[2]
            if data_row[0] == '21AII':
                XXIAII_amount = XXIAII_amount + data_row[1]
                XXIAII_amount_ytd = data_row[2]
            if data_row[0] == '21B':
                XXIB_amount = XXIB_amount + data_row[1]
                XXIB_amount_ytd = data_row[2]
            if data_row[0] == '22':
                XXII_amount = XXII_amount + data_row[1]
                XXII_amount_ytd = data_row[2]
            if data_row[0] == '23':
                XXIII_amount = XXIII_amount + data_row[1]
                XXIII_amount_ytd = XXIV_amount
            if data_row[0] == '24':
                XXIV_amount = XXIV_amount + data_row[1]
                XXIV_amount_ytd = XXIV_amount
            if data_row[0] == '25':
                XXV_amount = XXV_amount + data_row[1]
                XXV_amount_ytd = data_row[2]
            if data_row[0] == '26':
                XXVI_amount = XXVI_amount + data_row[1]
                XXVI_amount_ytd = data_row[2]
            if data_row[0] == '27':
                XXVII_amount = XXVII_amount + data_row[1]
                XXVII_amount_ytd = data_row[2]
            if data_row[0] == '28A':
                XXVIIIA_amount = XXVIIIA_amount + data_row[1]
                XXVIIIA_amount_ytd = data_row[2]
            if data_row[0] == '28B':
                XXVIIIB_amount = XXVIIIB_amount + data_row[1]
                XXVIIIB_amount_ytd = data_row[2]
            if data_row[0] == '28C':
                XXVIIIC_amount = XXVIIIC_amount + data_row[1]
                XXVIIIC_amount_ytd = data_row[2]
            if data_row[0] == '29':
                XXIX_amount = XXIX_amount + data_row[1]
                XXIX_amount_ytd = data_row[2]
            if data_row[0] == '30AI':
                XXXAI_amount = XXXAI_amount + data_row[1]
                XXXAI_amount_ytd = data_row[2]
            if data_row[0] == '30AII':
                XXXAII_amount = XXXAII_amount + data_row[1]
                XXXAII_amount_ytd = data_row[2]
            if data_row[0] == '30B':
                XXXB_amount = XXXB_amount + data_row[1]
                XXXB_amount_ytd = data_row[2]

        XXI_amount = XXIAI_amount + XXIAII_amount + XXIB_amount
        XXI_amount_ytd = XXIAI_amount_ytd + XXIAII_amount_ytd + XXIB_amount_ytd

        XXVIII_amount = XXVIIIA_amount + XXVIIIB_amount + XXVIIIC_amount
        XXVIII_amount_ytd = XXVIIIA_amount_ytd + XXVIIIB_amount_ytd + XXVIIIC_amount_ytd
        
        XXX_amount = XXXAI_amount + XXXAII_amount + XXXB_amount
        XXX_amount_ytd = XXXAI_amount_ytd + XXXAII_amount_ytd + XXXB_amount_ytd

        XXXI_amount = XXI_amount + XXII_amount + XXIII_amount + XXIV_amount + XXV_amount + XXVI_amount + XXVII_amount + XXVIII_amount + XXIX_amount + XXX_amount
        XXXI_amount_ytd = XXI_amount_ytd + XXII_amount_ytd + XXIII_amount_ytd + XXIV_amount_ytd + XXV_amount_ytd + XXVI_amount_ytd + XXVII_amount_ytd + XXVIII_amount_ytd + XXIX_amount_ytd + XXX_amount_ytd

        XXXII_amount = XXXI_amount - XXIAII_amount - XXXAII_amount
        XXXII_amount_ytd = XXXI_amount_ytd - XXIAII_amount_ytd - XXXAII_amount_ytd

        summary_disbursement_list = [ {'line_item':'31', 'level':1, 'description':'TOTAL DISBURSEMENTS', 'amt':XXXI_amount, 'amt_ytd':XXXI_amount_ytd},
                                {'line_item':'21', 'level':2, 'description':'OPERATING EXPENDITURES', 'amt':XXI_amount, 'amt_ytd':XXI_amount_ytd},
                                {'line_item':'21AI', 'level':3, 'description':'Allocated operating expenditures - federal', 'amt':XXIAI_amount, 'amt_ytd':XXIAI_amount_ytd},
                                {'line_item':'21AII', 'level':3, 'description':'Allocated operating expenditures - non-federal', 'amt':XXIAII_amount, 'amt_ytd':XXIAII_amount_ytd},
                                {'line_item':'21B', 'level':3, 'description':'Other federal operating expenditures', 'amt':XXIB_amount, 'amt_ytd':XXIB_amount_ytd},
                                {'line_item':'22', 'level':2, 'description':'TRANSFERS FROM AFFILIATED COMMITTEES', 'amt':XXII_amount, 'amt_ytd':XXII_amount_ytd},
                                {'line_item':'23', 'level':2, 'description':'CONTRIBUTIONS TO OTHER COMMITTEES', 'amt':XXIII_amount, 'amt_ytd':XXIII_amount_ytd},
                                {'line_item':'24', 'level':2, 'description':'INDEPENDENT EXPENDITURES', 'amt':XXIV_amount, 'amt_ytd':XXIV_amount_ytd},
                                {'line_item':'25', 'level':2, 'description':'PARTY COORDINATED EXPENDITURES', 'amt':XXV_amount, 'amt_ytd':XXV_amount_ytd},
                                {'line_item':'27', 'level':2, 'description':'LOANS MADE', 'amt':XXVII_amount, 'amt_ytd':XXVII_amount_ytd},
                                {'line_item':'26', 'level':2, 'description':'LOAN REPAYMENTS MADE', 'amt':XXVI_amount, 'amt_ytd':XXVI_amount_ytd},
                                {'line_item':'28', 'level':2, 'description':'TOTAL CONTRIBUTION REFUNDS', 'amt':XXVIII_amount, 'amt_ytd':XXVIII_amount_ytd},
                                {'line_item':'28A', 'level':3, 'description':'Individual refunds', 'amt':XXVIIIA_amount, 'amt_ytd':XXVIIIA_amount_ytd},
                                {'line_item':'28B', 'level':3, 'description':'Political party refunds', 'amt':XXVIIIB_amount, 'amt_ytd':XXVIIIB_amount_ytd},
                                {'line_item':'28C', 'level':3, 'description':'Other committee refunds', 'amt':XXVIIIC_amount, 'amt_ytd':XXVIIIC_amount_ytd},
                                {'line_item':'29', 'level':2, 'description':'OTHER DISBURSEMENTS', 'amt':XXIX_amount, 'amt_ytd':XXIX_amount_ytd},
                                {'line_item':'30', 'level':2, 'description':'TOTAL FEDERAL ELECTION ACTIVITY', 'amt':XXX_amount, 'amt_ytd':XXX_amount_ytd},
                                {'line_item':'30AI', 'level':3, 'description':'Allocated federal election activity - federal share', 'amt':XXXAI_amount, 'amt_ytd':XXXAI_amount_ytd},
                                {'line_item':'30AII', 'level':3, 'description':'Allocated federal election activity - Levin share', 'amt':XXXAII_amount, 'amt_ytd':XXXAII_amount_ytd},
                                {'line_item':'30B', 'level':3, 'description':'Federal election activity - federal only', 'amt':XXXB_amount, 'amt_ytd':XXXB_amount_ytd},
                                {'line_item':'32', 'level':2, 'description':'TOTAL FEDERAL DISBURSEMENTS', 'amt':XXXII_amount, 'amt_ytd':XXXII_amount_ytd},
                                ]

        # summary_disbursement = {'21AI': XXIAI_amount,
        #             '21AII': XXIAII_amount,
        #             '21B': XXIB_amount,
        #             '21': XXI_amount,
        #             '22': XXII_amount,
        #             '23': XXIII_amount,
        #             '24': XXIV_amount,
        #             '25': XXV_amount,
        #             '26': XXVI_amount,
        #             '27': XXVII_amount,
        #             '28A': XXVIIIA_amount,
        #             '28B': XXVIIIB_amount,
        #             '28C': XXVIIIC_amount,
        #             '28': XXVIII_amount,
        #             '29': XXIX_amount,
        #             '30AI': XXXAI_amount,
        #             '30AII': XXXAII_amount,
        #             '30B': XXXB_amount,
        #             '30': XXX_amount,
        #             '31': XXXI_amount,
        #             '32': XXXII_amount
        #                 }    
        return summary_disbursement_list
    except Exception as e:
        raise Exception('The summary_receipts API is throwing the error: ' + str(e))

def summary_receipts_for_sumamry_table(args):
    try:
        XIAI_amount = 0
        XIAII_amount = 0
        XIA_amount = 0
        XIB_amount = 0
        XIC_amount = 0
        XID_amount = 0
        XII_amount = 0
        XIII_amount = 0
        XIV_amount = 0
        XV_amount = 0
        XVI_amount = 0
        XVII_amount = 0
        XVIIIA_amount = 0
        XVIIIB_amount = 0
        XVIII_amount = 0
        XIX_amount = 0
        XX_amount = 0
        
        XIAI_amount_ytd = 0
        XIAII_amount_ytd = 0
        XIA_amount_ytd = 0
        XIB_amount_ytd = 0
        XIC_amount_ytd = 0
        XID_amount_ytd = 0
        XII_amount_ytd = 0
        XIII_amount_ytd = 0
        XIV_amount_ytd = 0
        XV_amount_ytd = 0
        XVI_amount_ytd = 0
        XVII_amount_ytd = 0
        XVIIIA_amount_ytd = 0
        XVIIIB_amount_ytd = 0
        XVIII_amount_ytd = 0
        XIX_amount_ytd = 0
        XX_amount_ytd = 0

        '''
        if len(args) == 2:
            cmte_id = args[0]
            report_id = args[1]
            sql_output = period_receipts_sql(cmte_id, report_id)
        else:
            cmte_id = args[0]
            calendar_start_dt = args[1]
            calendar_end_dt = args[2]
            sql_output = calendar_receipts_sql(cmte_id, calendar_start_dt, calendar_end_dt)
        '''    
        # print("args = ", args)
        calendar_start_dt = args[0]
        calendar_end_dt = args[1]
        # print("calendar_start_dt =", calendar_start_dt)
        cmte_id = args[2]
        report_id = args[3]

        sql_output = period_receipts_for_summary_table_sql(calendar_start_dt, calendar_end_dt, cmte_id, report_id )
        for row in sql_output:
            data_row = list(row)
            if data_row[0] == '11AI':
                XIAI_amount = XIAI_amount + data_row[1]
                XIAI_amount_ytd = data_row[2]
            if data_row[0] == '11AII':
                XIAII_amount = XIAII_amount + data_row[1]
                XIAII_amount_ytd = data_row[2]
            if data_row[0] == '11B':
                XIB_amount = XIB_amount + data_row[1]
                XIB_amount_ytd = data_row[2]
            if data_row[0] == '11C':
                XIC_amount = XIC_amount + data_row[1]
                XIC_amount_ytd = data_row[2]
            if data_row[0] == '12':
                XII_amount = XII_amount + data_row[1]
                XII_amount_ytd = data_row[2]
            if data_row[0] == '13':
                XIII_amount = XIII_amount + data_row[1]
                XIII_amount_ytd = data_row[2]
            if data_row[0] == '14':
                XIV_amount = XIV_amount + data_row[1]
                XIV_amount_ytd = data_row[2]
            if data_row[0] == '15':
                XV_amount = XV_amount + data_row[1]
                XV_amount_ytd = data_row[2]
            if data_row[0] == '16':
                XVI_amount = XVI_amount + data_row[1]
                XVI_amount_ytd = data_row[2]
            if data_row[0] == '17':
                XVII_amount = XVII_amount + data_row[1]
                XVII_amount_ytd = data_row[2]
            if data_row[0] == '18A':
                XVIIIA_amount = XVIIIA_amount + data_row[1]
                XVIIIA_amount_ytd = data_row[2]
            if data_row[0] == '18B':
                XVIIIB_amount = XVIIIB_amount + data_row[1]
                XVIIIB_amount_ytd = data_row[2]

        XIA_amount = XIAI_amount + XIAII_amount
        XIA_amount_ytd = XIAI_amount_ytd + XIAII_amount_ytd

        XID_amount = XIA_amount + XIB_amount + XIC_amount
        XID_amount_ytd = XIA_amount_ytd + XIB_amount_ytd + XIC_amount_ytd

        XVIII_amount = XVIIIA_amount + XVIIIB_amount
        VIII_amount_ytd = XVIIIA_amount_ytd + XVIIIB_amount_ytd

        XIX_amount =  XID_amount + XII_amount + XIII_amount + XIV_amount + XV_amount + XVI_amount + XVII_amount + XVIII_amount
        XIX_amount_ytd =  XID_amount_ytd + XII_amount_ytd + XIII_amount_ytd + XIV_amount_ytd + XV_amount_ytd + XVI_amount_ytd + XVII_amount_ytd + XVIII_amount_ytd

        XX_amount = XIX_amount - XVIII_amount
        XX_amount_ytd = XIX_amount_ytd - XVIII_amount_ytd

        summary_receipt_list = [ {'line_item':'19', 'level':1, 'description':'TOTAL RECIEPTS', 'amt':XIX_amount, 'amt_ytd':XIX_amount_ytd},
                                {'line_item':'11D', 'level':2, 'description':'TOTAL CONTRIBUTIONS', 'amt':XID_amount, 'amt_ytd':XID_amount_ytd},
                                {'line_item':'11A', 'level':3, 'description':'Total individual contributions', 'amt':XIA_amount, 'amt_ytd':XIA_amount_ytd},
                                {'line_item':'11AI', 'level':4, 'description':'Itemized individual contributions', 'amt':XIAI_amount, 'amt_ytd':XIAI_amount_ytd},
                                {'line_item':'11AII', 'level':4, 'description':'Unitemized individual contributions', 'amt':XIAII_amount, 'amt_ytd':XIAII_amount_ytd},
                                {'line_item':'11B', 'level':3, 'description':'Party committee contributions', 'amt':XIB_amount, 'amt_ytd':XIB_amount_ytd},
                                {'line_item':'11C', 'level':3, 'description':'Other committee contributions', 'amt':XIC_amount, 'amt_ytd':XIC_amount_ytd},
                                {'line_item':'12', 'level':2, 'description':'TRANSFERS FROM AFFILIATED COMMITTEES', 'amt':XII_amount, 'amt_ytd':XII_amount_ytd},
                                {'line_item':'13', 'level':2, 'description':'ALL LOANS RECEIVED', 'amt':XIII_amount,  'amt_ytd':XIII_amount_ytd},
                                {'line_item':'14', 'level':2, 'description':'LOAN REPAYMENTS RECEIVED', 'amt':XIV_amount, 'amt_ytd':XIV_amount_ytd},
                                {'line_item':'15', 'level':2, 'description':'OFFSETS TO OPERATING EXPENDITURES', 'amt':XV_amount,  'amt_ytd':XV_amount_ytd},
                                {'line_item':'16', 'level':2, 'description':'CANDIDATE REFUNDS', 'amt':XVI_amount, 'amt_ytd':XVI_amount_ytd},
                                {'line_item':'17', 'level':2, 'description':'OTHER RECEIPTS', 'amt':XVII_amount, 'amt_ytd':XVII_amount_ytd},
                                {'line_item':'18', 'level':2, 'description':'TOTAL TRANSFERS', 'amt':XVIII_amount, 'amt_ytd':XVIII_amount_ytd},
                                {'line_item':'18A', 'level':3, 'description':'Non-federal transfers', 'amt':XVIIIA_amount, 'amt_ytd':XVIIIA_amount_ytd},
                                {'line_item':'18B', 'level':3, 'description':'Levin funds', 'amt':XVIIIB_amount, 'amt_ytd':XVIIIB_amount_ytd},
                                {'line_item':'20', 'level':2, 'description':'TOTAL FEDERAL RECEIPTS', 'amt':XX_amount, 'amt_ytd':XX_amount_ytd},
                                ]
        # summary_receipt = {'11AI': XIAI_amount,
        #             '11AII': XIAII_amount,
        #             '11A': XIA_amount,
        #             '11B': XIB_amount,
        #             '11C': XIC_amount,
        #             '11D': XID_amount,
        #             '12': XII_amount,
        #             '13': XIII_amount,
        #             '14': XIV_amount,
        #             '15': XV_amount,
        #             '16': XVI_amount,
        #             '17': XVII_amount,
        #             '18A': XVIIIA_amount,
        #             '18B': XVIIIB_amount,
        #             '18': XVIII_amount,
        #             '19': XIX_amount,
        #             '20': XX_amount
        #                 }    
        return summary_receipt_list
    except Exception as e:
        raise Exception('The summary_receipts API is throwing the error: ' + str(e))

@api_view(['GET'])
def get_summary_table(request):
    try:
        cmte_id = request.user.username

        if not('report_id' in request.query_params and check_null_value(request.query_params.get('report_id'))):
            raise Exception ('Missing Input: report_id is mandatory')

        if not('calendar_year' in request.query_params and check_null_value(request.query_params.get('calendar_year'))):
            raise Exception ('Missing Input: calendar_year is mandatory')

        report_id = check_report_id(request.query_params.get('report_id'))
        calendar_year = check_calendar_year(request.query_params.get('calendar_year'))

        period_args = [datetime.date(int(calendar_year), 1, 1), datetime.date(int(calendar_year), 12, 31),  cmte_id, report_id]
        period_receipt = summary_receipts_for_sumamry_table(period_args)
        period_disbursement = summary_disbursements_for_sumamry_table(period_args)
        
        '''
        calendar_args = [cmte_id, date(int(calendar_year), 1, 1), date(int(calendar_year), 12, 31)]
        calendar_receipt = summary_receipts(calendar_args)
        calendar_disbursement = summary_disbursements(calendar_args)
        '''
        coh_bop_ytd = prev_cash_on_hand_cop(report_id, cmte_id, True)
        coh_bop = prev_cash_on_hand_cop(report_id, cmte_id, False)
        coh_cop = COH_cop(coh_bop, period_receipt, period_disbursement)

        cash_summary = {'COH AS OF JANUARY 1': coh_bop_ytd,
                        'BEGINNING CASH ON HAND': coh_bop,
                        'ENDING CASH ON HAND': coh_cop,
                        'DEBTS/LOANS OWED TO COMMITTEE': 0,
                        'DEBTS/LOANS OWED BY COMMITTEE': 0}

        forms_obj = {'Total Raised': {'period_receipts': period_receipt},
                    'Total Spent': {'period_disbursements': period_disbursement},
                    'Cash summary': cash_summary}
                        
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response('The get_summary_table API is throwing an error: ' + str(e), status=status.HTTP_400_BAD_REQUEST)

"""
******************************************************************************************************************************
END - GET SUMMARY TABLE API - CORE APP
******************************************************************************************************************************
"""
def COH_cop(coh_bop, period_receipt, period_disbursement):
    try:
        total_receipts = 0
        total_disbursements = 0
        for line_item in period_receipt:
            if line_item['line_item'] in ['11AI', '11AII', '11B', '11C', '12', '13', '14', '15', '16', '17', '18A', '18B']:
                total_receipts += line_item['amt']
        for line_item in period_disbursement:
            if line_item['line_item'] in ['21AI', '21AII', '21B', '22', '28A', '28B', '28C', '29']:
                total_disbursements += line_item['amt']
            elif line_item['line_item'] in ['27']:
                total_disbursements -= line_item['amt']
        coh_cop = coh_bop + total_receipts - total_disbursements
        return coh_cop
    except Exception as e:
        raise Exception('The COH_cop function is throwing an error: ' + str(e))

def get_cvg_dates(report_id, cmte_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT cvg_start_date, cvg_end_date from public.reports where cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            if (cursor.rowcount == 0):
                raise Exception('The Report ID: {} is either deleted or does not exist in Reports table'.format(report_id))
            result = cursor.fetchone()
            cvg_start_date,cvg_end_date = result
        return cvg_start_date, cvg_end_date
    except Exception as e:
        raise Exception('The get_cvg_dates function is throwing an error: ' + str(e))

def prev_cash_on_hand_cop(report_id, cmte_id, prev_yr):
    try:
        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)
        if prev_yr:
            prev_cvg_year = cvg_start_date.year - 1
            prev_cvg_end_dt = datetime.date(prev_cvg_year, 12, 31)
        else:
            prev_cvg_end_dt = cvg_start_date - datetime.timedelta(days=1)
        with connection.cursor() as cursor:
            cursor.execute("SELECT COALESCE(coh_cop, 0) from public.form_3x where cmte_id = %s AND cvg_end_dt = %s AND delete_ind is distinct from 'Y'", [cmte_id, prev_cvg_end_dt])
            if (cursor.rowcount == 0):
                coh_cop = 0
            else:
                result = cursor.fetchone()
                coh_cop = result[0]
        return coh_cop
    except Exception as e:
        raise Exception('The prev_cash_on_hand_cop function is throwing an error: ' + str(e))


# @api_view(['GET'])
# def get_thirdNavigationCOH(request):
#     try:
#         cmte_id = request.user.username

#         if not('report_id' in request.query_params and check_null_value(request.query_params.get('report_id'))):
#             raise Exception ('Missing Input: report_id is mandatory')

#         report_id = check_report_id(request.query_params.get('report_id'))

#         period_args = [date(2019, 1, 1), date(2019, 12, 31), cmte_id, report_id]
#         period_receipt = summary_receipts_for_summary_table(period_args)
#         period_disbursement = summary_disbursements_for_summary_table(period_args)

#         coh_bop = prev_cash_on_hand_cop(report_id, cmte_id, False)
#         coh_cop = COH_cop(coh_bop, period_receipt, period_disbursement)

#         forms_obj = {'COH': coh_cop}
#         return Response(forms_obj, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response("The get_thirdNavigationCOH API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
GET THIRD NAVIGATION TRANSACTION TYPES VALUES API - CORE APP - SPRINT 13 - FNE 1093 - BY PRAVEEN JINKA
******************************************************************************************************************************
"""
@api_view(['GET'])
def get_thirdNavigationTransactionTypes(request):
    try:
        cmte_id = request.user.username

        if not('report_id' in request.query_params and check_null_value(request.query_params.get('report_id'))):
            raise Exception ('Missing Input: Report_id is mandatory')
        report_id = check_report_id(request.query_params.get('report_id'))

        # period_args = [cmte_id, report_id]
        # period_receipt = summary_receipts(period_args)
        # period_disbursement = summary_disbursements(period_args)

        period_args = [datetime.date(2019, 1, 1), datetime.date(2019, 12, 31), cmte_id, report_id]
        period_receipt = summary_receipts_for_sumamry_table(period_args)
        period_disbursement = summary_disbursements_for_sumamry_table(period_args)

        coh_bop = prev_cash_on_hand_cop(report_id, cmte_id, False)
        coh_cop = COH_cop(coh_bop, period_receipt, period_disbursement)

        forms_obj = { 'Receipts': period_receipt[0].get('amt'),
                        'Disbursements': period_disbursement[0].get('amt'),
                        'Loans/Debts': 0,
                        'Others': 0,
                        'COH': coh_cop}
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_thirdNavigationTransactionTypes API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
END - GET SUMMARY TABLE API - CORE APP
******************************************************************************************************************************
"""
@api_view(['GET'])
def get_ReportTypes(request):
    """
    Fields for identifying the committee type and committee design and filter the forms category 
    """
    try:
        cmte_id = request.user.username
        forms_obj = []
        with connection.cursor() as cursor: 
            cursor.execute("SELECT json_agg(t) FROM (select rpt_type, rpt_type_desc from public.ref_rpt_types order by rpt_type_desc) t")
            for row in cursor.fetchall():
                data_row = list(row)
            forms_obj=data_row[0]
                
        if not bool(forms_obj):
            return Response("No entries were found for the get_ReportTypes API for this committee", status=status.HTTP_400_BAD_REQUEST)                              
        
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_ReportTypes API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_FormTypes(request):
    try:
        forms_obj = []
        cmte_id = request.user.username
        with connection.cursor() as cursor: 
            cursor.execute("SELECT json_agg(t) FROM (select  distinct form_type from my_forms_view where cmte_id = %s order by form_type ) t", [cmte_id])

            for row in cursor.fetchall():
                data_row = list(row)
            forms_obj=data_row[0]
                
        if not bool(forms_obj):
            return Response("No entries were found for the get_FormTypes API for this committee", status=status.HTTP_400_BAD_REQUEST)                              
        
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_FormTypes API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_Statuss(request):
    try:
        cmte_id = request.user.username

        data = """{
                    "data": [{
                            "status_cd": "S",
                            "status_desc": "Saved"
                        },
                        {
                            "status_cd": "F",
                            "status_desc": "Filed"
                        },
                       {
                            "status_cd": "X",
                            "status_desc": "Failed"
                        }]
                    }
                """

        '''
        forms_obj = []
        print("cmte_id", cmte_id)
        with connection.cursor() as cursor: 
            cursor.execute("SELECT json_agg(t) FROM (select  distinct form_type from public.cmte_report_types_view where cmte_id= %s order by form_type ) t",[cmte_id])

            for row in cursor.fetchall():
                data_row = list(row)
            forms_obj=data_row[0]
                
        if not bool(forms_obj):
            return Response("No entries were found for the get_FormTypes API for this committee", status=status.HTTP_400_BAD_REQUEST)                              
        '''
        forms_obj = json.loads(data)
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_Statuss API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_AmendmentIndicators(request):
    try:
        cmte_id = request.user.username
      
        data = """{
                    "data":  [{
                            "amend_ind": "N",
                            "amendment_desc": "New"
                        },
                       {
                            "amend_ind": "A",
                            "amendment_desc": "Amendment"
                        },    
                        {
                            "amend_ind": "T",
                            "amendment_desc": "Termination"
                        }]
                  }
                """
        '''                
        forms_obj = []
        print("cmte_id", cmte_id)
        with connection.cursor() as cursor: 
            cursor.execute("SELECT json_agg(t) FROM (select  distinct form_type from public.cmte_report_types_view where cmte_id= %s order by form_type ) t",[cmte_id])

            for row in cursor.fetchall():
                data_row = list(row)
            forms_obj=data_row[0]
                
        if not bool(forms_obj):
            return Response("No entries were found for the get_FormTypes API for this committee", status=status.HTTP_400_BAD_REQUEST)                              
        '''
        forms_obj = json.loads(data)
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_AmendmentIndicators API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_ItemizationIndicators(request):
    try:
        cmte_id = request.user.username
      
        data = """{
                    "data":  [{
                            "itemized": "I",
                            "itemization_desc": "Itemized"
                        },
                       {
                            "itemized": "U",
                            "itemization_desc": "UnItemized"
                        }]
                  }
                """
        forms_obj = json.loads(data)
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_ItemizationIndicators API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    
def get_f3x_SA_data(cmte_id, report_id):
    try:
        query_string = """SELECT * FROM public.sched_a WHERE cmte_id = %s AND report_id = %s"""
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id], [report_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            pass
   
        return forms_obj
    except Exception:
        raise

def get_amendmentNumber(cmte_id, report_id):
    try:
        query_string = """SELECT amend_number FROM public.reports WHERE cmte_id = %s AND report_id = %s"""
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id], [report_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            pass

        return forms_obj
    except Exception:
        raise

"""
*****************************************************************************************************************************
END - GET ALL TRANSACTIONS API - CORE APP
******************************************************************************************************************************
"""
"""

*****************************************************************************************************************************
GET Report info API - CORE APP
******************************************************************************************************************************
"""
@api_view(['GET'])
def get_report_info(request):
    """
    Get report details
    """
    cmte_id = request.user.username
    report_id = request.query_params.get('reportid')
    # print("cmte_id", cmte_id)
    # print("report_id", report_id)
    try:
        if ('reportid' in request.query_params and (not request.query_params.get('reportid') =='')):
            # print("you are here1")
            if int(request.query_params.get('reportid'))>=1:
                # print("you are here2")
                with connection.cursor() as cursor:
                    # GET all rows from Reports table
                    
                    query_string = """SELECT cmte_id as cmteId, report_id as reportId, form_type as formType, '' as electionCode, report_type as reportType,  rt.rpt_type_desc as reportTypeDescription, rt.regular_special_report_ind as regularSpecialReportInd, '' as stateOfElection, '' as electionDate, cvg_start_date as cvgStartDate, cvg_end_date as cvgEndDate, due_date as dueDate, amend_ind as amend_Indicator, 0 as coh_bop, (SELECT CASE WHEN due_date IS NOT NULL THEN to_char(due_date, 'YYYY-MM-DD')::date - to_char(now(), 'YYYY-MM-DD')::date ELSE 0 END ) AS daysUntilDue, email_1 as email1, email_2 as email2, additional_email_1 as additionalEmail1, additional_email_2 as additionalEmail2
                                      FROM public.reports rp, public.ref_rpt_types rt WHERE rp.report_type=rt.rpt_type AND delete_ind is distinct from 'Y' AND cmte_id = %s  AND report_id = %s""" 

                    # print("query_string", query_string)

                    cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id, report_id])
                
                    for row in cursor.fetchall():
                        data_row = list(row)
                        forms_obj=data_row[0]
                        
            if forms_obj is None:
                raise NoOPError('The Committee: {} does not have any reports listed'.format(cmte_id))

            return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception:
        raise

"""
*****************************************************************************************************************************
END - Report info api - CORE APP
******************************************************************************************************************************
"""

@api_view(['GET'])
def print_preview_pdf(request):
    cmte_id = request.user.username
    report_id = request.data.get('reportid')

    try:
        data_obj = {
                'report_id':report_id,
        }

        json_builder_resp = requests.post(settings.JSON_BUILDER_URL, data=data_obj)
        print("json_builder_resp = ", json_builder_resp)

        bucket_name = 'dev-efile-repo'
        client = boto3.client('s3')
        transfer = S3Transfer(client)
        #s3.download_file(bucket_name , s3_file_path, save_as)
        transfer.download_file(bucket_name , json_builder_resp, json_builder_resp)
        with open(save_as) as f:
            print(json_builder_resp.read())

        printresp = requests.post(settings.NXG_FEC_PRINT_API_URL + settings.NXG_FEC_PRINT_API_VERSION, data=data_obj, files=file_obj)

        if not printresp.ok:
            return Response(printresp.json(), status=status.HTTP_400_BAD_REQUEST)
        else:
            dictprint = printresp.json()
            merged_dict = {**create_json_data, **dictprint}
            return JsonResponse(merged_dict, status=status.HTTP_201_CREATED)
    except Exception:
        raise
"""
*********************************************************************************************************************************************
end print priview api
*********************************************************************************************************************************************
"""
"""
**********************************************************************************************************************************************
Create Contacts API - CORE APP - SPRINT 16 - FNE 1248 - BY  Yeswanth Kumar Tella
**********************************************************************************************************************************************
"""

@api_view(['GET', 'POST'])
def create_contacts_view(request):
    try:
        # print("request.data: ", request.data)
        cmte_id = request.user.username
        param_string = ""
        page_num = int(request.data.get('page', 1))
        descending = request.data.get('descending', 'false')
        sortcolumn = request.data.get('sortColumnName')
        itemsperpage = request.data.get('itemsPerPage', 5)
        search_string = request.data.get('search')
        #import ipdb;ipdb.set_trace()
        params = request.data.get('filters', {})
        keywords = params.get('keywords')
        if str(descending).lower() == 'true':
            descending = 'DESC'
        else:
            descending = 'ASC'

        keys = ['id', 'type', 'name', 'occupation', 'employer' ]
        search_keys = ['id', 'type', 'name', 'occupation', 'employer']
        if search_string:
            for key in search_keys:
                if not param_string:
                    param_string = param_string + " AND (CAST(" + key + " as CHAR(100)) ILIKE '%" + str(search_string) +"%'"
                else:
                    param_string = param_string + " OR CAST(" + key + " as CHAR(100)) ILIKE '%" + str(search_string) +"%'"
            param_string = param_string + " )"
        keywords_string = ''
        if keywords:
            for key in keys:
                for word in keywords:
                    if '"' in word:
                        continue
                    elif "'" in word:
                        if not keywords_string:
                            keywords_string = keywords_string + " AND ( CAST(" + key + " as CHAR(100)) = " + str(word)
                        else:
                            keywords_string = keywords_string + " OR CAST(" + key + " as CHAR(100)) = " + str(word)
                    else:
                        if not keywords_string:
                            keywords_string = keywords_string + " AND ( CAST(" + key + " as CHAR(100)) ILIKE '%" + str(word) +"%'"
                        else:
                            keywords_string = keywords_string + " OR CAST(" + key + " as CHAR(100)) ILIKE '%" + str(word) +"%'"
            keywords_string = keywords_string + " )"
        param_string = param_string + keywords_string
        
        
        trans_query_string = """SELECT id, type, name, occupation, employer from all_contacts_view
                                    where cmte_id='""" + cmte_id + """' """ + param_string 
        # print("trans_query_string: ",trans_query_string)
        # import ipdb;ipdb.set_trace()
        if sortcolumn and sortcolumn != 'default':
            trans_query_string = trans_query_string + """ ORDER BY """+ sortcolumn + """ """ + descending
        elif sortcolumn == 'default':
            trans_query_string = trans_query_string + """ ORDER BY name ASC"""
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + trans_query_string + """) t""")
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
                forms_obj = data_row[0]
                if forms_obj is None:
                    forms_obj =[]
                    status_value = status.HTTP_200_OK
                else:
                    for d in forms_obj:
                        for i in d:
                            if not d[i]:
                                d[i] = ''
                      
                    status_value = status.HTTP_200_OK
        
        #import ipdb; ipdb.set_trace()
        total_count = len(forms_obj)
        paginator = Paginator(forms_obj, itemsperpage)
        if paginator.num_pages < page_num:
            page_num = paginator.num_pages
        forms_obj = paginator.page(page_num)
        json_result = {'contacts': list(forms_obj), 'totalcontactsCount': total_count,
                    'itemsPerPage': itemsperpage, 'pageNumber': page_num,'totalPages':paginator.num_pages}
        return Response(json_result, status=status_value)
    except Exception as e:
        return Response("The contact_views API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


"""
*****************************************************************************************************************************
END - Contacts API - CORE APP
******************************************************************************************************************************
"""

dict_names = {
    "ColA":["6b_cashOnHandBeginning",
    "6c_totalReceipts",
    "6d_subtotal",
    "7_totalDisbursements",
    "8_cashOnHandAtClose",
    "9_debtsTo",
    "10_debtsBy",
    "11ai_Itemized",
    "11aii_Unitemized",
    "11aiii_Total",
    "11b_politicalPartyCommittees",
    "11c_otherPoliticalCommitteesPACs",
    "11d_totalContributions",
    "12_transfersFromAffiliatedOtherPartyCommittees",
    "13_allLoansReceived",
    "14_loanRepaymentsReceived",
    "15_offsetsToOperatingExpendituresRefunds",
    "16_refundsOfFederalContributions",
    "17_otherFederalReceiptsDividends",
    "18a_transfersFromNonFederalAccount_h3",
    "18b_transfersFromNonFederalLevin_h5",
    "18c_totalNonFederalTransfers",
    "19_totalReceipts",
    "20_totalFederalReceipts",
    "21ai_federalShare",
    "21aii_nonFederalShare",
    "21b_otherFederalOperatingExpenditures",
    "21c_totalOperatingExpenditures",
    "22_transfersToAffiliatedOtherPartyCommittees",
    "23_contributionsToFederalCandidatesCommittees",
    "24_independentExpenditures",
    "25_coordinatedExpenditureMadeByPartyCommittees",
    "26_loanRepayments",
    "27_loansMade",
    "28a_individualsPersons",
    "28b_politicalPartyCommittees",
    "28c_otherPoliticalCommittees",
    "28d_totalContributionsRefunds",
    "29_otherDisbursements",
    "30ai_sharedFederalActivity_h6_fedShare",
    "30aii_sharedFederalActivity_h6_nonFed",
    "30b_nonAllocable_100_federalElectionActivity",
    "30c_totalFederalElectionActivity",
    "31_totalDisbursements",
    "32_totalFederalDisbursements",
    "33_totalContributions",
    "34_totalContributionRefunds",
    "35_netContributions",
    "36_totalFederalOperatingExpenditures",
    "37_offsetsToOperatingExpenditures",
    "38_netOperatingExpenditures",],
    "ColB":[  "6a_cashOnHandJan_1",
    "6c_totalReceipts",
    "6d_subtotal",
    "7_totalDisbursements",
    "8_cashOnHandAtClose",
    "11ai_itemized",
    "11aii_unitemized",
    "11aiii_total",
    "11b_politicalPartyCommittees",
    "11c_otherPoliticalCommitteesPACs",
    "11d_totalContributions",
    "12_transfersFromAffiliatedOtherPartyCommittees",
    "13_allLoansReceived",
    "14_loanRepaymentsReceived",
    "15_offsetsToOperatingExpendituresRefunds",
    "16_refundsOfFederalContributions",
    "17_otherFederalReceiptsDividends",
    "18a_transfersFromNonFederalAccount_h3",
    "18b_transfersFromNonFederalLevin_h5",
    "18c_totalNonFederalTransfers",
    "19_totalReceipts",
    "20_totalFederalReceipts",
    "21ai_federalShare",
    "21aii_nonFederalShare",
    "21b_otherFederalOperatingExpenditures",
    "21c_totalOperatingExpenditures",
    "22_transfersToAffiliatedOtherPartyCommittees",
    "23_contributionsToFederalCandidatesCommittees",
    "24_independentExpenditures",
    "25_coordinatedExpendituresMadeByPartyCommittees",
    "26_loanRepayments",
    "27_loansMade",
    "28a_individualPersons",
    "28b_politicalPartyCommittees",
    "28c_otherPoliticalCommittees",
    "28d_totalContributionRefunds",
    "29_otherDisbursements",
    "30ai_sharedFederalActivity_h6_federalShare",
    "30aii_sharedFederalActivity_h6_nonFederal",
    "30b_nonAllocable_100_federalElectionActivity",
    "30c_totalFederalElectionActivity",
    "31_totalDisbursements",
    "32_totalFederalDisbursements",
    "33_totalContributions",
    "34_totalContributionRefunds",
    "35_netContributions",
    "36_totalFederalOperatingExpenditures",
    "37_offsetsToOperatingExpenditures",
    "38_netOperatingExpenditures"]
}

column_names_dict = {'colA': {'coh_bop': '6b', 'ttl_receipts_sum_page_per': '6c', 'subttl_sum_page_per': '6d', 'ttl_disb_sum_page_per': '7', 'coh_cop': '8', 'debts_owed_to_cmte': '9', 'debts_owed_by_cmte': '10', 'indv_item_contb_per': '11ai', 'indv_unitem_contb_per': '11aii', 'ttl_indv_contb': '11aiii', 'pol_pty_cmte_contb_per_i': '11b', 'other_pol_cmte_contb_per_i': '11c', 'ttl_contb_col_ttl_per': '11d', 'tranf_from_affiliated_pty_per': '12', 'all_loans_received_per': '13', 'loan_repymts_received_per': '14', 'offsets_to_op_exp_per_i': '15', 'fed_cand_contb_ref_per': '16', 'other_fed_receipts_per': '17', 'tranf_from_nonfed_acct_per': '18a', 'tranf_from_nonfed_levin_per': '18b', 'ttl_nonfed_tranf_per': '18c', 'ttl_receipts_per': '19', 'ttl_fed_receipts_per': '20', 'shared_fed_op_exp_per': '21ai', 'shared_nonfed_op_exp_per': '21aii', 'other_fed_op_exp_per': '21b', 'ttl_op_exp_per': '21c', 'tranf_to_affliliated_cmte_per': '22', 'fed_cand_cmte_contb_per': '23', 'indt_exp_per': '24', 'coord_exp_by_pty_cmte_per': '25', 'loan_repymts_made_per': '26', 'loans_made_per': '27', 'indv_contb_ref_per': '28a', 'pol_pty_cmte_contb_per_ii': '28b', 'other_pol_cmte_contb_per_ii': '28c', 'ttl_contb_ref_per_i': '28d', 'other_disb_per': '29', 'shared_fed_actvy_fed_shr_per': '30ai', 'shared_fed_actvy_nonfed_per': '30aii', 'non_alloc_fed_elect_actvy_per': '30b', 'ttl_fed_elect_actvy_per': '30c', 'ttl_disb_per': '31', 'ttl_fed_disb_per': '32', 'ttl_contb_per': '33', 'ttl_contb_ref_per_ii': '34', 'net_contb_per': '35', 'ttl_fed_op_exp_per': '36', 'offsets_to_op_exp_per_ii': '37', 'net_op_exp_per': '38'}, 
'colB': {'coh_begin_calendar_yr': '6a', 'ttl_receipts_sum_page_ytd': '6c', 'subttl_sum_ytd': '6d', 'ttl_disb_sum_page_ytd': '7', 'coh_coy': '8', 'indv_item_contb_ytd': '11ai', 'indv_unitem_contb_ytd': '11aii', 'ttl_indv_contb_ytd': '11aiii', 'pol_pty_cmte_contb_ytd_i': '11b', 'other_pol_cmte_contb_ytd_i': '11c', 'ttl_contb_col_ttl_ytd': '11d', 'tranf_from_affiliated_pty_ytd': '12', 'all_loans_received_ytd': '13', 'loan_repymts_received_ytd': '14', 'offsets_to_op_exp_ytd_i': '15', 'fed_cand_cmte_contb_ytd': '16', 'other_fed_receipts_ytd': '17', 'tranf_from_nonfed_acct_ytd': '18a', 'tranf_from_nonfed_levin_ytd': '18b', 'ttl_nonfed_tranf_ytd': '18c', 'ttl_receipts_ytd': '19', 'ttl_fed_receipts_ytd': '20', 'shared_fed_op_exp_ytd': '21ai', 'shared_nonfed_op_exp_ytd': '21aii', 'other_fed_op_exp_ytd': '21b', 'ttl_op_exp_ytd': '21c', 'tranf_to_affilitated_cmte_ytd': '22', 'fed_cand_cmte_contb_ref_ytd': '23', 'indt_exp_ytd': '24_independentExpenditures', 'coord_exp_by_pty_cmte_ytd': '25', 'loan_repymts_made_ytd': '26', 'loans_made_ytd': '27', 'indv_contb_ref_ytd': '28a', 'pol_pty_cmte_contb_ytd_ii': '28b', 'other_pol_cmte_contb_ytd_ii': '28c', 'ttl_contb_ref_ytd_i': '28d', 'other_disb_ytd': '29', 'shared_fed_actvy_fed_shr_ytd': '30ai', 'shared_fed_actvy_nonfed_ytd': '30aii', 'non_alloc_fed_elect_actvy_ytd': '30b', 'ttl_fed_elect_actvy_ytd': '30c', 'ttl_disb_ytd': '31', 'ttl_fed_disb_ytd': '32', 'ttl_contb_ytd': '33', 'ttl_contb_ref_ytd_ii': '34', 'net_contb_ytd': '35', 'ttl_fed_op_exp_ytd': '36', 'offsets_to_op_exp_ytd_ii': '37', 'net_op_exp_ytd': '38'}}

col_a = {
"6b":"cash_on_hand",
"6c":"19",
"6d":"6b + 6c",             
"7":"31",
"8":"6d - 7",
"9":"0",
"10":"0",
"11ai":"",
"11aii":"",
"11aiii":"11ai + 11aii",
"11b":"",   
"11c":"",   
"11d":"11aiii + 11b + 11c",
"12":"",    
"13":"",
"14":"",
"15":"",
"16":"",    
"17":"",
"18a":"0",
"18b":"0",
"18c":"18a+18b",
"19":"11d+12+13+14+15+16+17+18c",
"20":"19 - 18c",
"21ai":"0",
"21aii":"0",
"21b":"",
"21c":"21ai + 21aii + 21b",
"22":"",    
"23":"",    
"24":"",
"25":"0",
"26":"",    
"27":"",    
"28a":"",   
"28b":"",   
"28c":"",   
"28d":"28a + 28b + 28c",
"29":"",
"30ai":"0",
"30aii":"0",
"30b":"",   
"30c":"30ai + 30aii + 30b",
"31":"21c + 22 - 27 + 28d + 29",
"32":"31 - 21aii + 30aii",
"33":"11d",
"34":"28d",
"35":"11d - 28d",
"36":"21ai + 21b",
"37":"15",
"38":"36 - 37",
}
    
col_b = {
"6c":"19",
"6d":"6a + 6c",
"7":"30",
"8":"6d - 7",
"11ai":"",  
"11aii":"", 
"11aiii":"11ai + 11aii",
"11b":"",   
"11c":"",   
"11d":" 11aiii + 11b + 11c",
"12":"",    
"13":"",    
"14":"",    
"15":"",    
"16":"",    
"17":"",    
"18a":"",   
"18b":"",   
"18c":"18a + 18b",
"19":"11d + 12 + 13 + 14 + 15 + 16 + 17 + 18c",
"20":"19 - 18c",
"21ai":"",  
"21aii":"", 
"21b":"",   
"21c":"21ai + 21aii + 21b",
"22":"",    
"23":"",    
"24":"",    
"25":"",    
"26":"",    
"27":"",    
"28a":"",   
"28b":"",   
"28c":"",   
"28d":"28a + 28b + 28c",
"29":"",    
"30ai":"0",
"30aii":"0",
"30b":"",
"30c":"30ai+30aii+30b",
"31":"21c + 22 - 27 + 28d + 29",
"32":"31 - 21aii + 30aii",
"33":"11d",
"34":"28d",
"35":"11d - 28d",
"36":"21ai + 21b",
"37":"15",
"38":"36 - 37"
}

col_name_value_dict = {'colA': {'6b': 'coh_bop', '6c': 'ttl_receipts_sum_page_per', '6d': 'subttl_sum_page_per', '7': 'ttl_disb_sum_page_per', '8': 'coh_cop', '9': 'debts_owed_to_cmte', '10': 'debts_owed_by_cmte', '11ai': 'indv_item_contb_per', '11aii': 'indv_unitem_contb_per', '11aiii': 'ttl_indv_contb', '11b': 'pol_pty_cmte_contb_per_i', '11c': 'other_pol_cmte_contb_per_i', '11d': 'ttl_contb_col_ttl_per', '12': 'tranf_from_affiliated_pty_per', '13': 'all_loans_received_per', '14': 'loan_repymts_received_per', '15': 'offsets_to_op_exp_per_i', '16': 'fed_cand_contb_ref_per', '17': 'other_fed_receipts_per', '18a': 'tranf_from_nonfed_acct_per', '18b': 'tranf_from_nonfed_levin_per', '18c': 'ttl_nonfed_tranf_per', '19': 'ttl_receipts_per', '20': 'ttl_fed_receipts_per', '21ai': 'shared_fed_op_exp_per', '21aii': 'shared_nonfed_op_exp_per', '21b': 'other_fed_op_exp_per', '21c': 'ttl_op_exp_per', '22': 'tranf_to_affliliated_cmte_per', '23': 'fed_cand_cmte_contb_per', '24': 'indt_exp_per', '25': 'coord_exp_by_pty_cmte_per', '26': 'loan_repymts_made_per', '27': 'loans_made_per', '28a': 'indv_contb_ref_per', '28b': 'pol_pty_cmte_contb_per_ii', '28c': 'other_pol_cmte_contb_per_ii', '28d': 'ttl_contb_ref_per_i', '29': 'other_disb_per', '30ai': 'shared_fed_actvy_fed_shr_per', '30aii': 'shared_fed_actvy_nonfed_per', '30b': 'non_alloc_fed_elect_actvy_per', '30c': 'ttl_fed_elect_actvy_per', '31': 'ttl_disb_per', '32': 'ttl_fed_disb_per', '33': 'ttl_contb_per', '34': 'ttl_contb_ref_per_ii', '35': 'net_contb_per', '36': 'ttl_fed_op_exp_per', '37': 'offsets_to_op_exp_per_ii', '38': 'net_op_exp_per'}, 
'colB': {'6a': 'coh_begin_calendar_yr', '6c': 'ttl_receipts_sum_page_ytd', '6d': 'subttl_sum_ytd', '7': 'ttl_disb_sum_page_ytd', '8': 'coh_coy', '11ai': 'indv_item_contb_ytd', '11aii': 'indv_unitem_contb_ytd', '11aiii': 'ttl_indv_contb_ytd', '11b': 'pol_pty_cmte_contb_ytd_i', '11c': 'other_pol_cmte_contb_ytd_i', '11d': 'ttl_contb_col_ttl_ytd', '12': 'tranf_from_affiliated_pty_ytd', '13': 'all_loans_received_ytd', '14': 'loan_repymts_received_ytd', '15': 'offsets_to_op_exp_ytd_i', '16': 'fed_cand_cmte_contb_ytd', '17': 'other_fed_receipts_ytd', '18a': 'tranf_from_nonfed_acct_ytd', '18b': 'tranf_from_nonfed_levin_ytd', '18c': 'ttl_nonfed_tranf_ytd', '19': 'ttl_receipts_ytd', '20': 'ttl_fed_receipts_ytd', '21ai': 'shared_fed_op_exp_ytd', '21aii': 'shared_nonfed_op_exp_ytd', '21b': 'other_fed_op_exp_ytd', '21c': 'ttl_op_exp_ytd', '22': 'tranf_to_affilitated_cmte_ytd', '23': 'fed_cand_cmte_contb_ref_ytd', '24_independentExpenditures': 'indt_exp_ytd', '25': 'coord_exp_by_pty_cmte_ytd', '26': 'loan_repymts_made_ytd', '27': 'loans_made_ytd', '28a': 'indv_contb_ref_ytd', '28b': 'pol_pty_cmte_contb_ytd_ii', '28c': 'other_pol_cmte_contb_ytd_ii', '28d': 'ttl_contb_ref_ytd_i', '29': 'other_disb_ytd', '30ai': 'shared_fed_actvy_fed_shr_ytd', '30aii': 'shared_fed_actvy_nonfed_ytd', '30b': 'non_alloc_fed_elect_actvy_ytd', '30c': 'ttl_fed_elect_actvy_ytd', '31': 'ttl_disb_ytd', '32': 'ttl_fed_disb_ytd', '33': 'ttl_contb_ytd', '34': 'ttl_contb_ref_ytd_ii', '35': 'net_contb_ytd', '36': 'ttl_fed_op_exp_ytd', '37': 'offsets_to_op_exp_ytd_ii', '38': 'net_op_exp_ytd'}}

def get_f3x_report_data(cmte_id, report_id):
    try:
        query_string = """SELECT * FROM public.form_3x WHERE cmte_id = %s AND report_id = %s"""
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id, report_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            pass
            #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))   
        return forms_obj
    except Exception:
        raise


def cash_on_hand_begining_amount(cmte_id, report_id):
    try:
        from datetime import date, timedelta, datetime, time
        from dateutil.relativedelta import relativedelta

        # today = date.today()
        
        #d = today - relativedelta(months=1)

        from_date, to_date = get_cvg_dates(report_id, cmte_id)
        #print(from_date_time,to_date_time,'datetime')
        d = from_date - relativedelta(months=1)
       
        from_date_time = date(d.year, d.month, 1)
        to_date_time = date(from_date.year, from_date.month, 1) - relativedelta(days=1)
        # from_date_time = datetime.combine(fromdate, time(0,0,0))
        # to_date_time = datetime.combine(todate, time(23,59,59))
        print(from_date_time,to_date_time,'datetime')


        with connection.cursor() as cursor:
            cursor.execute("SELECT coh_cop from public.form_3x where cmte_id = %s AND cvg_start_dt = %s AND cvg_end_dt = %s AND delete_ind is distinct from 'Y'", [cmte_id, from_date_time, to_date_time])
            if (cursor.rowcount == 0):
                coh_cop = 0
            else:
                result = cursor.fetchone()
                coh_cop = result[0]
        return coh_cop
    except Exception as e:
        raise Exception('The prev_cash_on_hand_cop function is throwing an error: ' + str(e))


def get_a_sum(cmte_id, report_id, clm_type):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT SUM(contribution_amount)  FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND line_number = %s """,[cmte_id, report_id, clm_type])
            total_sum = cursor.fetchone()[0]
        return total_sum
    except Exception as  e:
         return False
         raise Exception('The aggregate_amount function is throwing an error: ' + str(e))


def get_b_sum(cmte_id, report_id, clm_type):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT SUM(expenditure_amount)  FROM public.sched_b WHERE cmte_id = %s AND report_id = %s AND line_number = %s """,[cmte_id, report_id, clm_type])
            total_sum = cursor.fetchone()[0]
            print(total_sum)
        return total_sum
    except Exception as  e:
         return False
         raise Exception('The aggregate_amount function is throwing an error: ' + str(e))


def get_col_a_value(k, actual_vals, cmte_id=None, report_id=None):
    val = 0
    if col_a[k] == 'cash_on_hand':
        val = cash_on_hand_begining_amount(cmte_id,report_id)
        print('cash_on_hand amttttttttttttttttttttttttttttttttttt',k, val)
        return val

    if not k or k == '0' or k not in col_a or not col_a[k] or col_a[k] == '0':
        #return 0
        total_sum  = get_a_sum(cmte_id, report_id,actual_vals[col_name_value_dict['colA'][k]])
        val += total_sum
    
    elif len(k.replace(' ','').split('+')) == 1:
        if not col_a[k]:
            return get_col_a_value(col_a[k], actual_vals)
        else:
            #val += actual_vals[col_name_value_dict['colA'][k]]
            total_sum  = get_a_sum(cmte_id, report_id,actual_vals[col_name_value_dict['colA'][k]])
            val += total_sum
    else:
        k_l = k.replace(' ','').split('+')
        for cl_n in k_ls:
            if '-' in cl_n:
                val += (get_col_a_value(cl_n.split('-')[0], actual_vals)) - (get_col_a_value(cl_n.split('-')[1], actual_vals))
            else:
                val += get_col_a_value(cl_n, actual_vals)
                #total_sum  = get_a_sum(cmte_id, report_id)
                #val += get_col_a_value(cl_n, actual_vals)
                
    return val


def get_col_b_value(k, actual_vals, cmte_id=None, report_id=None):
    val = 0
    if not k or k == '0' or k not in col_b or not col_b[k] or col_b[k] == '0':
        #return 0
        total_sum  = get_b_sum(cmte_id, report_id,actual_vals[col_name_value_dict['colB'][k]])
        val += total_sum
    
    elif len(k.replace(' ','').split('+')) == 1:
        if not col_b[k]:
            return get_col_b_value(col_b[k], actual_vals, )
        else:
            #val += actual_vals[col_name_value_dict['colB'][k]]
            total_sum  = get_b_sum(cmte_id, report_id,actual_vals[col_name_value_dict['colB'][k]])
            val += total_sum
    else:
        k_l = k.replace(' ','').split('+')
        for cl_n in k_ls:
            if '-' in cl_n:
                val += (get_col_b_value(cl_n.split('-')[0], actual_vals)) - (get_col_b_value(cl_n.split('-')[1], actual_vals))
            else:
                val += get_col_b_value(cl_n, actual_vals)
    return val


@api_view(['POST'])
def prepare_json_builders_data(request):
    try:
        print("request.data: ", request.data)
        cmte_id = request.user.username
        param_string = ""
        report_id = request.data.get('report_id')
        f_3x_list = get_f3x_report_data(cmte_id, report_id)
        summary_d = {i:(k if k else 0) for i, k in f_3x_list[0].items()}
        col_a = column_names_dict['colA']
        col_b = column_names_dict['colB']
        values_dict = {}
        for c_name in col_a:
            values_dict[c_name] = get_col_a_value(col_a[c_name], summary_d, cmte_id, report_id)
        for d_name in col_b:
            print(d_name,'cma')
            values_dict[d_name] = get_col_b_value(col_b[d_name], summary_d, cmte_id, report_id)
        import ipdb;ipdb.set_trace()
        print(values_dict,'dict')
        update_str = str(values_dict)
        update_str = update_str[1:-1].replace(':', '=').replace("'", '')

        with connection.cursor() as cursor:
            query_string = """SELECT * FROM public.form_3x WHERE cmte_id = %s AND report_id = %s"""
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id, report_id])
            update_query = """update public.form_3x set %s WHERE cmte_id = '%s' AND report_id = '%s';"""%(update_str, cmte_id, report_id)
            cursor.execute(update_query)
        status_value = status.HTTP_200_OK
            
        return Response({'Response':'Success'}, status=status_value)
    except Exception as e:
        return Response({'Response':'Failed', 'Message': str(e)}, status=status.HTTP_400_BAD_REQUEST)