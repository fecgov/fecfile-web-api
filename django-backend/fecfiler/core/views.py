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
from datetime import datetime, date
import boto3
from botocore.exceptions import ClientError
import boto
from boto.s3.key import Key
from django.conf import settings
import re
import csv

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
        print("cmte_id =", cmte_id)
        print("form_type =", form_type)
        print("cvg_start_dt =", cvg_start_dt)
        print("cvg_end_dt =", cvg_end_dt)


        forms_obj = []
        with connection.cursor() as cursor: 
            cursor.execute("SELECT report_id, cvg_start_date, cvg_end_date, report_type FROM public.reports WHERE cmte_id = %s and form_type = %s AND delete_ind is distinct from 'Y' ORDER BY report_id DESC", [cmte_id, form_type])

            if len(args) == 4:
                for row in cursor.fetchall():
                    if not(row[1] is None or row[2] is None):
                        if (row[2] <= cvg_end_dt and row[1] >= cvg_start_dt):
                            forms_obj.append({"report_id":row[0],"cvg_start_date":row[1],"cvg_end_date":row[2],"report_type":row[3]})

            if len(args) == 5:
                report_id = args[4]
                for row in cursor.fetchall():
                    if not(row[1] is None or row[2] is None):
                        if ((row[2] <= cvg_end_dt and row[1] >= cvg_start_dt) and row[0] != int(report_id)):
                            forms_obj.append({"report_id":row[0],"cvg_start_date":row[1],"cvg_end_date":row[2],"report_type":row[3]})

        return forms_obj
    except Exception:
        raise 


def date_format(cvg_date):
    try:
        if cvg_date == None or cvg_date in ["none", "null", " ", ""]:
            return None
        cvg_dt = datetime.strptime(cvg_date, '%m/%d/%Y').date()
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
def post_sql_report(report_id, cmte_id, form_type, amend_ind, report_type, cvg_start_date, cvg_end_date, status, email_1, email_2):

    try:
        with connection.cursor() as cursor:
            # INSERT row into Reports table
            cursor.execute("""INSERT INTO public.reports (report_id, cmte_id, form_type, amend_ind, report_type, cvg_start_date, cvg_end_date, status, email_1, email_2)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",[report_id, cmte_id, form_type, amend_ind, report_type, cvg_start_date, cvg_end_date, status, email_1, email_2])                                          
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
            # GET single row from Reports table
            query_string = """SELECT report_id, cmte_id, form_type, report_type, amend_ind, amend_number, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, email_1, email_2, filed_date, fec_id, fec_accepted_date, fec_status, create_date, last_update_date 
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
        check_mandatory_fields_report(data)
        cmte_id = data.get('cmte_id')
        form_type = data.get('form_type')
        cvg_start_dt = data.get('cvg_start_dt')
        cvg_end_dt = data.get('cvg_end_dt')
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
                post_sql_report(report_id, data.get('cmte_id'), data.get('form_type'), data.get('amend_ind'), data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('status'), data.get('email_1'), data.get('email_2'))
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
                'coh_bop': int(request.data.get('coh_bop')),
                'status': f_status,
                'email_1': email_1,
                'email_2': email_2,
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
        

def check_mandatory_fields_entity(data):
    try:
        list_mandatory_fields_entity = ['entity_type', 'cmte_id', 'entity_name']
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
                                                    FROM public.entity WHERE cmte_id = '""" + cmte_id + """'""" + param_string + """ AND delete_ind is distinct from 'Y' ORDER BY """ + order_string[:-1]
        print(query_string)
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""")
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
************************* *****************************************************************************************************
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
            data_obj['data'] = serializer.data
            k.set_contents_from_string(json.dumps(data_obj))            
            url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")
            tmp_filename = '/tmp/' + comm_info.committeeid + '_f99.json'
            vdata = {}
            vdata['form_type'] = "F99"
            vdata['committeeid'] = comm_info.committeeid
            json.dump(data_obj, open(tmp_filename, 'w'))
            vfiles = {}
            vfiles["json_file"] = open(tmp_filename, 'rb')
            res = requests.post("http://" + settings.DATA_RECEIVE_API_URL + "/v1/send_data" , data=vdata, files=vfiles)
            import ipdb; ipdb.set_trace()
            return Response(res.text, status=status.HTTP_200_OK)
            
        else:
            return Response({"FEC Error 007":"This user does not have a submitted CommInfo object"}, status=status.HTTP_400_BAD_REQUEST)
            
    except CommitteeInfo.DoesNotExist:
        return Response({"FEC Error 009":"An unexpected error occurred while processing your request"}, status=status.HTTP_400_BAD_REQUEST)

"""
******************************************************************************************************************************
GET ALL TRANSACTIONS API - CORE APP - SPRINT 8 - FNE 613 - BY PRAVEEN JINKA
******************************************************************************************************************************
"""
@api_view(['GET'])
def get_all_transactions(request):
    try:
        cmte_id = request.user.username
        param_string = ""
        # if 'order_params' in request.query_params:
        #     order_string = request.query_params.get('order_params')
        # else:
        #     order_string = "transaction_id"
        for key, value in request.query_params.items():
            try:
                check_value = int(value)
                param_string = param_string + " AND " + key + "=" + str(value)
            except Exception as e:
                if key == 'transaction_date':
                    transaction_date = date_format(request.query_params.get('transaction_date'))
                    param_string = param_string + " AND " + key + "='" + str(transaction_date) + "'"
                else:
                    param_string = param_string + " AND LOWER(" + key + ") LIKE LOWER('" + value +"%')"

        query_string = """SELECT count(*) total_transactions,sum((case when memo_code is null then transaction_amount else 0 end))total_transaction_amount from all_transactions_view
                            where cmte_id='""" + cmte_id + """'""" + param_string + """ AND delete_ind is distinct from 'Y'"""
                            # + """ ORDER BY """ + order_string
        # print(query_string)
        with connection.cursor() as cursor:
            cursor.execute(query_string)
            result = cursor.fetchone()
            count = result[0]
            sum_trans = result[1]
            
        trans_query_string = """SELECT transaction_type, transaction_type_desc, transaction_id, name, street_1, street_2, city, state, zip_code, transaction_date, transaction_amount, purpose_description, occupation, employer, memo_code, memo_text from all_transactions_view
                                    where cmte_id='""" + cmte_id + """'""" + param_string + """ AND delete_ind is distinct from 'Y'"""
                                    # + """ ORDER BY """ + order_string
        # print(trans_query_string)
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + trans_query_string + """) t""")
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        status_value = status.HTTP_200_OK
        if forms_obj is None:
            forms_obj =[]
            status_value = status.HTTP_204_NO_CONTENT

        json_result = { 'transactions': forms_obj, 'totalAmount': sum_trans, 'totalTransactionCount': count}
        return Response(json_result, status=status_value)

    except Exception as e:
        return Response("The get_all_transactions API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
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
GET ALL DELETED TRANSACTIONS API - CORE APP - SPRINT 9 - FNE 744 - BY PRAVEEN JINKA
******************************************************************************************************************************
"""
@api_view(['GET'])
def get_all_deleted_transactions(request):
    try:
        cmte_id = request.user.username
        param_string = ""
        for key, value in request.query_params.items():
            try:
                check_value = int(value)
                param_string = param_string + " AND " + key + "=" + str(value)
            except Exception as e:
                if key == 'transaction_date':
                    transaction_date = date_format(request.query_params.get('transaction_date'))
                    param_string = param_string + " AND " + key + "='" + str(transaction_date) + "'"
                else:
                    param_string = param_string + " AND LOWER(" + key + ") LIKE LOWER('" + value +"%')"

        # query_string = """SELECT count(*) total_transactions,sum((case when memo_code is null then transaction_amount else 0 end))total_transaction_amount from all_transactions_view
        #                     where cmte_id='""" + cmte_id + """'""" + param_string + """ AND delete_ind = 'Y'"""
        # with connection.cursor() as cursor:
        #     cursor.execute(query_string)
        #     result = cursor.fetchone()
        #     count = result[0]
        #     sum_trans = result[1]
            
        trans_query_string = """SELECT transaction_type, transaction_type_desc, transaction_id, name, street_1, street_2, city, state, zip_code, transaction_date, transaction_amount, purpose_description, occupation, employer, memo_code, memo_text from all_transactions_view
                                    where cmte_id='""" + cmte_id + """'""" + param_string + """ AND delete_ind = 'Y'"""
        # print(trans_query_string)
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + trans_query_string + """) t""")
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        status_value = status.HTTP_200_OK
        if forms_obj is None:
            forms_obj =[]
            status_value = status.HTTP_204_NO_CONTENT

        # json_result = { 'transactions': forms_obj, 'totalAmount': sum_trans, 'totalTransactionCount': count}
        json_result = { 'transactions': forms_obj}
        return Response(json_result, status=status_value)

    except Exception as e:
        return Response("The get_all_transactions API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
END - GET ALL DELETED TRANSACTIONS API - CORE APP
******************************************************************************************************************************
"""
"""
******************************************************************************************************************************
GET SUMMARY TABLE API - CORE APP - SPRINT 10 - FNE 720 - BY PRAVEEN JINKA
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
            cursor.execute("SELECT line_number, contribution_amount FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            return cursor.fetchall()
    except Exception as e:
        raise Exception('The period_receipts_sql API is throwing an error: ' + str(e))

def calendar_receipts_sql(cmte_id, calendar_start_dt, calendar_end_dt):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT line_number, contribution_amount FROM public.sched_a WHERE cmte_id = %s AND delete_ind is distinct from 'Y' AND contribution_date BETWEEN %s AND %s", [cmte_id, calendar_start_dt, calendar_end_dt])
            return cursor.fetchall()
    except Exception as e:
        raise Exception('The calendar_receipts_sql API is throwing an error: ' + str(e))

def summary_receipts(args):
    try:
        XIAI_amount = 0
        XIAII_amount = 0
        XIAIII_amount = 0
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
        XVIIIC_amount = 0
        XIX_amount = 0
        XX_amount = 0

        if len(args) == 2:
            cmte_id = args[0]
            report_id = args[1]
            sql_output = period_receipts_sql(cmte_id, report_id)
        else:
            cmte_id = args[0]
            calendar_start_dt = args[1]
            calendar_end_dt = args[2]
            sql_output = calendar_receipts_sql(cmte_id, calendar_start_dt, calendar_end_dt)

        for row in sql_output:
            data_row = list(row)
            if data_row[0] == '11AI':
                XIAI_amount = XIAI_amount + data_row[1]
            if data_row[0] == '11AII':
                XIAII_amount = XIAII_amount + data_row[1]
            if data_row[0] == '11B':
                XIB_amount = XIB_amount + data_row[1]
            if data_row[0] == '11C':
                XIC_amount = XIC_amount + data_row[1]
            if data_row[0] == '12':
                XII_amount = XII_amount + data_row[1]
            if data_row[0] == '13':
                XIII_amount = XIII_amount + data_row[1]
            if data_row[0] == '14':
                XIV_amount = XIV_amount + data_row[1]
            if data_row[0] == '15':
                XV_amount = XV_amount + data_row[1]
            if data_row[0] == '16':
                XVI_amount = XVI_amount + data_row[1]
            if data_row[0] == '17':
                XVII_amount = XVII_amount + data_row[1]
            if data_row[0] == '18A':
                XVIIIA_amount = XVIIIA_amount + data_row[1]
            if data_row[0] == '18B':
                XVIIIB_amount = XVIIIB_amount + data_row[1]

        XIAIII_amount = XIAI_amount + XIAII_amount
        XID_amount = XIAIII_amount + XIB_amount + XIC_amount
        XVIIIC_amount = XVIIIA_amount + XVIIIB_amount
        XIX_amount =  XID_amount + XII_amount + XIII_amount + XIV_amount + XV_amount + XVI_amount + XVII_amount + XVIIIC_amount
        XX_amount = XIX_amount - XVIIIC_amount

        summary_receipts = {'11AI': XIAI_amount,
                    '11AII': XIAII_amount,
                    '11AIII': XIAIII_amount,
                    '11B': XIB_amount,
                    '11C': XIC_amount,
                    '11D': XID_amount,
                    '12': XII_amount,
                    '13': XIII_amount,
                    '14': XIV_amount,
                    '15': XV_amount,
                    '16': XVI_amount,
                    '17': XVII_amount,
                    '18A': XVIIIA_amount,
                    '18B': XVIIIB_amount,
                    '18C': XVIIIC_amount,
                    '19': XIX_amount,
                    '20': XX_amount
                        }    
        return summary_receipts
    except Exception as e:
        raise Exception('The summary_receipts API is throwing the error: ' + str(e))

@api_view(['GET'])
def summary_table(request):
    try:
        cmte_id = request.user.username

        if not('report_id' in request.query_params and check_null_value(request.query_params.get('report_id'))):
            raise Exception ('Missing Input: Report_id is mandatory')

        if not('calendar_year' in request.query_params and check_null_value(request.query_params.get('calendar_year'))):
            raise Exception ('Missing Input: calendar_year is mandatory')

        report_id = check_report_id(request.query_params.get('report_id'))
        calendar_year = check_calendar_year(request.query_params.get('calendar_year'))

        period_args = [cmte_id, report_id]
        period_receipt = summary_receipts(period_args)

        calendar_args = [cmte_id, date(int(calendar_year), 1, 1), date(int(calendar_year), 12, 31)]
        calendar_receipt = summary_receipts(calendar_args)

        forms_obj = {'period':{'period_receipts': period_receipt,
                                'period_disbursements': 0,
                                'period_summary': 0},
                    'calendar':{'calendar_receipts': calendar_receipt,
                                'calendar_disbursements': 0,
                                'calendar_summary': 0}}                          
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The summary_table API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
        print("cmte_id", cmte_id)
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
        with connection.cursor() as cursor: 
            cursor.execute("SELECT json_agg(t) FROM (select  distinct form_type from public.ref_form_types order by form_type ) t")

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
