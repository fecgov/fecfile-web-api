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
import psycopg2
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
from datetime import date, timedelta, time
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from xml.etree import ElementTree
from fuzzywuzzy import fuzz
import pandas
import numpy

from fecfiler.core.email_helper import email

from fecfiler.core.carryover_helper import (
    do_h1_carryover,
    do_h2_carryover,
    do_loan_carryover,
    do_debt_carryover,
)

# from fecfiler.core.jsonbuilder import create_f3x_expenditure_json_file, build_form3x_json_file,create_f3x_json_file, create_f3x_partner_json_file,create_f3x_returned_bounced_json_file,create_f3x_reattribution_json_file,create_inkind_bitcoin_f3x_json_file,get_report_info

# Create your views here.

"""
CREATE OR replace VIEW PUBLIC.dynamic_forms_view AS 
                       WITH dy_forms_by_section  AS 
                       ( 
                                SELECT   dynamic_form_fields.form_type, 
                                         dynamic_form_fields.transaction_type, 
                                         dynamic_form_fields.field_section, 
                                         dynamic_form_fields.field_section_order, 
                                         dynamic_form_fields.class_name, 
                                         dynamic_form_fields.seperator, 
                                         dynamic_form_fields.child_form, 
                                         dynamic_form_fields.form_sub_title, 
                                         CASE 
                                                  WHEN dynamic_form_fields.child_form = false THEN json_agg(json_build_object('preText',
                                                           CASE 
                                                                    WHEN dynamic_form_fields.field_db_name::text ~~ '%purpose%'::text THEN dynamic_form_fields.field_value
                                                                    ELSE NULL::character VARYING
                                                           END, 'setEntityIdTo', dynamic_form_fields.entity_id_mapping, 'isReadonly', dynamic_form_fields.field_is_readonly, 'entityGroup', dynamic_form_fields.entity_group, 'toggle', dynamic_form_fields.toggle, 'inputGroup', dynamic_form_fields.field_input_group, 'inputIcon', dynamic_form_fields.field_input_icon, 'text', dynamic_form_fields.field_label, 'infoIcon', dynamic_form_fields.field_infoicon, 'infoText', dynamic_form_fields.field_info, 'name', dynamic_form_fields.field_db_name, 'type', dynamic_form_fields.field_type, 'value',
                                                           CASE 
                                                                    WHEN dynamic_form_fields.field_db_name::text ~~ '%purpose%'::text
                                                                    AND      dynamic_form_fields.field_input_group = true THEN NULL::character VARYING
                                                                    ELSE dynamic_form_fields.field_value
                                                           END, 'scroll', dynamic_form_fields.scroll, 'height', dynamic_form_fields.height, 'width', dynamic_form_fields.width, 'validation', json_build_object('required', dynamic_form_fields.field_is_required, 'max', dynamic_form_fields.field_size, dynamic_form_fields.field_validation, true)) ORDER BY dynamic_form_fields.field_order)
                                                  ELSE NULL::json 
                                         END AS json_by_section 
                                FROM     dynamic_form_fields 
                                WHERE    dynamic_form_fields.field_type::text <> 'hidden'::text 
                                GROUP BY dynamic_form_fields.form_type, 
                                         dynamic_form_fields.transaction_type, 
                                         dynamic_form_fields.field_section, 
                                         dynamic_form_fields.field_section_order, 
                                         dynamic_form_fields.class_name, 
                                         dynamic_form_fields.seperator, 
                                         dynamic_form_fields.child_form, 
                                         dynamic_form_fields.form_sub_title 
                                ORDER BY dynamic_form_fields.field_section_order 
                       )SELECT   dfbs.form_type, 
                       dfbs.transaction_type, 
                       json_build_object('data', json_build_object('formFields', json_agg(Json_build_object('childForm', dfbs.child_form, 'childFormTitle', dfbs.form_sub_title, 'colClassName', dfbs.class_name, 'seperator', dfbs.seperator, 'cols', dfbs.json_by_section) order BY dfbs.field_section_order), 'hiddenFields',
                       ( 
                              SELECT json_agg(json_build_object('type', h.field_type, 'name', replace(h.field_db_name::text, ' '::text, ''::text), 'value', h.field_value)) AS json_agg
                              FROM   dynamic_form_fields h 
                              WHERE  h.field_type::text = 'hidden'::text 
                              AND    h.form_type::text = dfbs.form_type::text 
                              AND    h.transaction_type::text = dfbs.transaction_type::text), 'states',
                       ( 
                                SELECT   json_agg(json_build_object('name', ref_states.state_description, 'code', ref_states.state_code) ORDER BY ref_states.st_number) AS json_agg
                                FROM     ref_states), 'titles', 
                       ( 
                              SELECT json_agg(json_build_object('fieldset', dft.fieldset, 'colClassName', dft.class_name, 'label', dft.tran_type_forms_title)) AS json_agg
                              FROM   df_tran_type_identifier dft 
                              WHERE  dft.form_type::text = dfbs.form_type::text 
                              AND    dft.tran_type_identifier::text = dfbs.transaction_type::text), 'entityTypes',
                       ( 
                              SELECT json_agg(json_build_object('entityType', dfe.entity_type, 'entityTypeDescription', dfe.entity_type_description, 'group', dfe.entity_group, 'selected', dfe.selected)) AS json_agg
                              FROM   df_entity_types_view dfe 
                              WHERE  dfe.form_type::text = dfbs.form_type::text 
                              AND    dfe.transaction_type::text = dfbs.transaction_type::text), 'electionTypes',
                       ( 
                              SELECT json_agg(json_build_object('electionType', ref_election_type.election_type, 'electionTypeDescription', ref_election_type.election_type_desc)) AS json_agg
                              FROM   ref_election_type), 'activityEventTypes', 
                       ( 
                              SELECT json_agg(json_build_object('activityEventType', ref_event_types.event_type, 'activityEventTypeDescription', ref_event_types.event_type_desc)) AS                                                                                     json_agg
                              FROM   ref_event_types), 'subTransactions', get_sub_transaction_json(dfbs.form_type, dfbs.transaction_type::text::character VARYING), 'jfMemoTypes', get_jf_memo_types(dfbs.form_type, dfbs.transaction_type::text::character VARYING))) AS form_fields
              FROM     dy_forms_by_section dfbs 
              GROUP BY dfbs.form_type, 
                       dfbs.transaction_type;
"""

SCHEDULE_TO_TABLE_DICT = { 'SA': ['sched_a'],
    'SB': ['sched_b'],
    'SC': ['sched_c', 'sched_c1', 'sched_c2'],
    'SD': ['sched_d'],
    'SE': ['sched_e'],
    'SF': ['sched_f'],
    'SH': ['sched_h1', 'sched_h2', 'sched_h3', 'sched_h4', 'sched_h5', 'sched_h6'],
    'SL': ['sched_l']
}

# NOT_DELETE_TRANSACTION_TYPE_IDENTIFIER = ['LOAN_FROM_IND', 'LOAN_FROM_BANK', 'LOAN_OWN_TO_CMTE_OUT', 'IK_OUT', 'IK_BC_OUT', 
#     'PARTY_IK_OUT', 'PARTY_IK_BC_OUT', 'PAC_IK_OUT', 'PAC_IK_BC_OUT', 'IK_TRAN_OUT', 'IK_TRAN_FEA_OUT']

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

            if 'cmte_type_category' in request.query_params and request.query_params.get('cmte_type_category'):
                cmte_type_category = request.query_params.get('cmte_type_category')
            else:
                cmte_type_category = 'PAC'
            cursor.execute("select transaction_category_json from transaction_category_json_view where form_type = %s AND cmte_type_category = %s", [form_type, cmte_type_category])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
                
        if not bool(forms_obj):
            return Response("No entries were found for the form_type: {} for this committee".format(form_type), status=status.HTTP_400_BAD_REQUEST)                              
        
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_transaction_categories API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


def cmte_type(cmte_id):
    """
    to know if the cmte is PAC or PTY and determine the flag values for administrative, generic_voter_drive, public_communications
    """
    try:
        with connection.cursor() as cursor:
            # Insert data into schedH3 table
            cursor.execute(
                """SELECT cmte_type_category FROM public.committee_master WHERE cmte_id=%s""",
                [cmte_id],
            )
            cmte_type_tuple = cursor.fetchone()
            if cmte_type_tuple:
                return cmte_type_tuple[0]
            else:
                raise Exception(
                    "The cmte_id: {} does not exist in committee master table.".format(
                        cmte_id
                    )
                )
    except Exception as err:
        raise Exception(f"cmte_type function is throwing an error: {err}")

"""
********************************************************************************************************************************
GET TRANSACTION TYPES API- CORE APP - FNE 1477, FNE1497 - BY ZOBAIR SALEEM
********************************************************************************************************************************
"""
@api_view(['GET'])
def get_transaction_types(request):

    try:
        with connection.cursor() as cursor:
            forms_obj= {}
            form_type = request.query_params.get('form_type')

            cursor.execute("select tran_identifier,tran_desc,category_type  from ref_transaction_types where form_type = %s", [form_type])
            rows = cursor.fetchall()

            transaction_types_dict=[]
            for row in rows:
                transaction_type = {
                    'name': row[0],
                    'text': row[1],
                    'categoryType': row[2]
                    }
                transaction_types_dict.append(transaction_type)
            response = transaction_types_dict
                
        if not bool(response):
            return Response("No entries were found for the form_type: {}".format(form_type), status=status.HTTP_400_BAD_REQUEST)                              
        
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_transaction_types API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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

        with connection.cursor() as cursor:
            cursor.execute("SELECT cmte_filing_freq FROM public.committee_master WHERE cmte_id=%s", [cmte_id])
            cmte_filing_freq = cursor.fetchone()
            if cmte_filing_freq:
                cmte_filing_freq = cmte_filing_freq[0]

        if cmte_filing_freq == 'Q':
            reports = forms_obj.get('report_type')
            for report in reports:
                if report.get('report_type') == 'YE':
                    report['election_state'][0]['dates'][0]['cvg_start_date'] = "2019-10-01"

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
    # try:
        cmte_id = request.user.username
        form_type = request.query_params.get('form_type')
        transaction_type = request.query_params.get('transaction_type')
        if 'reportId' in request.query_params and request.query_params.get('reportId') not in ('',"", None, " ", "None", "null"):
            report_id = request.query_params.get('reportId')
        else:
            report_id = 0
        forms_obj = {}
        with connection.cursor() as cursor:
            cursor.execute("select form_fields from dynamic_forms_view where form_type = %s and transaction_type = %s", [form_type, transaction_type])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        with connection.cursor() as cursor:
            cursor.execute("SELECT cmte_type_category FROM public.committee_master WHERE cmte_id = %s", [cmte_id])
            cmte_type_categories = cursor.fetchone()
            if cmte_type_categories:
                cmte_type_category = cmte_type_categories[0]
        # print(forms_obj)
        if bool(forms_obj):
            if transaction_type in ['ALLOC_EXP','ALLOC_EXP_VOID','ALLOC_EXP_CC_PAY','ALLOC_EXP_STAF_REIM','ALLOC_EXP_PMT_TO_PROL', 'ALLOC_EXP_DEBT',
                                    'ALLOC_EXP_CC_PAY_MEMO', 'ALLOC_EXP_STAF_REIM_MEMO', 'ALLOC_EXP_PMT_TO_PROL_MEMO', 'ALLOC_FEA_DISB',
                                    'ALLOC_FEA_CC_PAY','ALLOC_FEA_STAF_REIM','ALLOC_FEA_CC_PAY_MEMO','ALLOC_FEA_STAF_REIM_MEMO','ALLOC_FEA_VOID','ALLOC_FEA_DISB_DEBT']:
                if cmte_type_category:
                    for events in forms_obj['data']['committeeTypeEvents']:
                        for eventTypes in events['eventTypes']:
                            if eventTypes['eventType'] in ['PC', 'AD', 'GV']:
                                query_string = """
                                SELECT count(*) 
                                FROM public.sched_h1 
                                WHERE cmte_id = %s 
                                AND election_year = (select extract(year from cvg_start_date) from public.reports where report_id = %s) 
                                AND delete_ind IS DISTINCT FROM 'Y'
                                """
                                if eventTypes['eventType'] == 'PC':
                                    query_string += " AND public_communications = true"
                                elif eventTypes['eventType'] == 'AD':
                                    query_string += " AND administrative = true"
                                elif eventTypes['eventType'] == 'GV':
                                    query_string += " AND generic_voter_drive = true"
                                with connection.cursor() as cursor:
                                    cursor.execute(query_string, [cmte_id,report_id])
                                    count = cursor.fetchone()
                                    print(cursor.query)
                                print(eventTypes['eventType'] + " count: "+str(count[0]))
                                if count[0] == 0:
                                    eventTypes['hasValue'] = False
                                else:
                                    eventTypes['hasValue'] = True
                            elif eventTypes['eventType'] in ['DF', 'DC']:
                                query_string = """SELECT json_agg(t) FROM (SELECT activity_event_name AS "activityEventType", transaction_id AS "transactionId", activity_event_name AS "activityEventDescription" 
                                        FROM public.sched_h2 WHERE cmte_id = %s AND report_id = %s AND {} AND delete_ind IS DISTINCT FROM 'Y') AS t"""
                                if eventTypes['eventType'] == 'DF':
                                    query_string = query_string.format("fundraising = true")
                                elif eventTypes['eventType'] == 'DC':
                                    query_string = query_string.format("direct_cand_support = true")
                                with connection.cursor() as cursor:
                                    cursor.execute(query_string, [cmte_id, report_id])
                                    print(cursor.query)
                                    activityEventTypes = cursor.fetchone()
                                # print(eventTypes['eventType'] + 'activityEventTypes: '+ str(activityEventTypes[0]))
                                if activityEventTypes and activityEventTypes[0]:
                                    eventTypes['activityEventTypes'] = activityEventTypes[0]
                                    eventTypes['hasValue'] = True
                                else:
                                    eventTypes['hasValue'] = False
                            elif eventTypes['eventType'] in ['VR', 'VI', 'GO', 'GC', 'EA']:
                                query_string = """
                                SELECT count(*) 
                                FROM public.sched_h1 
                                WHERE cmte_id = %s 
                                AND election_year = (select extract(year from cvg_start_date) from public.reports where report_id = %s)
                                AND delete_ind IS DISTINCT FROM 'Y'
                                """
                                with connection.cursor() as cursor:
                                    cursor.execute(query_string, [cmte_id,report_id])
                                    count = cursor.fetchone()
                                    print(cursor.query)
                                print(eventTypes['eventType'] + "count: "+str(count[0]))
                                if count[0] == 0:
                                    eventTypes['hasValue'] = False
                                else:
                                    eventTypes['hasValue'] = True
            elif transaction_type == 'DEBT_TO_VENDOR':
                if cmte_type_category and cmte_type_category == 'PAC':
                    del forms_obj['data']['subTransactions'][1]
                    del forms_obj['data']['subTransactions'][4]
                    del forms_obj['data']['subTransactions'][4]
        else:
            return Response("No entries were found for the form_type: {} and transaction type: {} for this committee".format(form_type, transaction_type), status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse(forms_obj, status=status.HTTP_200_OK, safe=False)
    # except Exception as e:
    #     return Response("The get_dynamic_forms_fields API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
            cursor.execute("SELECT report_id, cvg_start_date, cvg_end_date, report_type FROM public.reports WHERE cmte_id = %s and form_type = %s AND delete_ind is distinct from 'Y' AND superceded_report_id is NULL ORDER BY report_id DESC", [cmte_id, form_type])

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
    if check_value in ["none", "null", " ", ""]:
        #return None
        return False
    # else:
    return True




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
def post_sql_report(report_id, cmte_id, form_type, amend_ind, amend_number, report_type, cvg_start_date, cvg_end_date, due_date, status, email_1, email_2, additional_email_1, additional_email_2):

    try:
        with connection.cursor() as cursor:
            # INSERT row into Reports table
            cursor.execute("""INSERT INTO public.reports (report_id, cmte_id, form_type, amend_ind, amend_number, report_type, cvg_start_date, cvg_end_date, status, due_date, email_1, email_2, additional_email_1, additional_email_2)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",[report_id, cmte_id, form_type, amend_ind, amend_number, report_type, cvg_start_date, cvg_end_date, status, due_date, email_1, email_2, additional_email_1, additional_email_2])                                          
    except Exception:
        raise

def get_list_all_report(cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET all rows from Reports table
            query_string = """
            SELECT report_id, 
            cmte_id, 
            form_type, 
            report_type, 
            amend_ind, 
            amend_number, 
            cvg_start_date, 
            cvg_end_date, 
            due_date, 
            superceded_report_id, 
            previous_report_id, 
            status, 
            email_1, 
            email_2, 
            filed_date, 
            fec_id, 
            fec_accepted_date, 
            fec_status, 
            create_date, 
            last_update_date
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
                # print(cvg_start_dt)
                # print(cvg_end_dt)
                # print(status)
                # print(report_type)
                cursor.execute("""UPDATE public.reports SET report_type = %s, cvg_start_date = %s, cvg_end_date = %s,  due_date = %s, email_1 = %s,  email_2 = %s,  additional_email_1 = %s,  additional_email_2 = %s, status = %s, filed_date = last_update_date WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
                                [report_type,  cvg_start_dt, cvg_end_dt, due_date,  email_1, email_2, additional_email_1, additional_email_2, status, report_id, cmte_id])
                # print(cursor.query)

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
def post_reports(data, reportid=None):
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
        if reportid:
            args.append(reportid)
        if not (cvg_start_dt is None or cvg_end_dt is None):
            forms_obj = check_list_cvg_dates(args)
        # print(forms_obj)
        # print('just in post_reports')
        if len(forms_obj)== 0:
            report_id = get_next_report_id()
            data['report_id'] = str(report_id)
            try:
                post_sql_report(report_id, data.get('cmte_id'), data.get('form_type'), data.get('amend_ind'), data.get('amend_number'), data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('due_dt'), data.get('status'), data.get('email_1'), data.get('email_2'), data.get('additional_email_1'), data.get('additional_email_2'))

            except Exception as e:
                # Resetting Report ID
                get_prev_report_id(report_id)
                raise Exception('The post_sql_report function is throwing an error: ' + str(e))

            try:
                #Insert data into Form 3X table
                if data.get('form_type') == "F3X":
                    # print('here1')
                    check_mandatory_fields_form3x(data)
                    # print('here2')
                    post_sql_form3x(report_id, data.get('cmte_id'), data.get('form_type'), data.get('amend_ind'), data.get('report_type'), data.get('election_code'), data.get('date_of_election'), data.get('state_of_election'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('coh_bop'))
                    # print('here3')
                # print('here3.5')
                output = get_reports(data)
                # print('here4')
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
            # print(old_list_report)
            # print(data.get('status'))
            put_sql_report(data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('due_date'), data.get('email_1'), data.get('email_2'), data.get('additional_email_1'), data.get('additional_email_2'), data.get('status'), data.get('report_id'), cmte_id)
            old_dict_report = old_list_report[0]
            prev_report_type = old_dict_report.get('reporttype')
            prev_cvg_start_dt = old_dict_report.get('cvgstartdate')
            prev_cvg_end_dt = old_dict_report.get('cvgenddate')
            prev_last_update_date = datetime.datetime.now()
                                           
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

def reposit_f3x_data(cmte_id, report_id):
    """
    helper funcrtion to move current F3X report data from efiling front db to backend db
    """
    # logger.debug('request for cloning a transaction:{}'.format(request.data))
    logger.debug('reposit f3x data with cmte_id {} and report_id {}'.format(cmte_id, report_id))
    # transaction_tables = ['sched_a']
    transaction_tables = [
        'reports',
        'sched_a', 
        'sched_b', 
        'sched_c', 
        'sched_c1',
        'sched_c2',
        'sched_d', 
        'sched_e', 
        'sched_f', 
        'sched_h1',
        'sched_h2',
        'sched_h3',
        'sched_h4',
        'sched_h5',
        'sched_h6',
        'sched_l',
        'form_3x',
        ]
    # transaction_tables = ['sched_b']
    backend_connection = psycopg2.connect(
            'dbname={} user={} host={} password={} connect_timeout=3000'.
            format(
                os.environ.get('BACKEND_DB_NAME'),
                os.environ.get('BACKEND_DB_USER'),
                os.environ.get('BACKEND_DB_HOST'),
                os.environ.get('BACKEND_DB_PASSWORD')))
        # conn.close()
    back_cursor = backend_connection.cursor()
    # cmte_id = 'C00326835'
    # report_id = '110915'
    for transaction_table in transaction_tables:
        table_schema_sql = """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = '{}'
        """.format(transaction_table)
        
        with connection.cursor() as cursor:
            logger.debug("fetching transaction table column names...")
            # cursor.execute(table_schema_sql, (transaction_table))
            cursor.execute(table_schema_sql)
            rows = cursor.fetchall()  
            columns = []
            for row in rows:
                # exclude report_seq from reports
                if row[0] != 'report_seq':
                    columns.append(row[0])
            logger.debug('table columns: {}'.format(list(columns)))



            insert_str = ','.join(columns)
            select_str = ','.join(columns)
            clone_sql = """
                SELECT {_select}
                FROM public.{table_name}
            """.format(table_name=transaction_table, _select=select_str)
            clone_sql = clone_sql + """ WHERE cmte_id = %s and report_id = %s and delete_ind is distinct from 'Y';"""
            logger.debug('clone transaction with sql:{}'.format(clone_sql))

            cursor.execute(clone_sql, (cmte_id, report_id))

            if not cursor.rowcount:
                logger.debug('no transaction data found for {}'.format(transaction_table))
                continue
            rows = cursor.fetchall()
            for row in rows:
                # print('...')
                # print(row)
                insert_sql = """
                INSERT INTO public.{table_name}({_insert}) VALUES
                """.format(table_name=transaction_table, _insert=insert_str)
                # print(insert_sql)
                back_cursor.execute(insert_sql+' %s', (row,))
                backend_connection.commit()
                logger.debug('row data {} inserted'.format(row))

    back_cursor.close()
    backend_connection.close()

def reposit_f99_data(cmte_id, report_id):
    """
    helper funcrtion to move current F99 report data from efiling front db to backend db
    """
    # logger.debug('request for cloning a transaction:{}'.format(request.data))
    logger.debug('reposit f99 data with cmte_id {} and report_id {}'.format(cmte_id, report_id))
    # transaction_tables = ['sched_a']
    transaction_tables = [
        'forms_committeeinfo',
        # 'forms_f99attachment',
        ]
    # transaction_tables = ['sched_b']
    backend_connection = psycopg2.connect(
            'dbname={} user={} host={} password={} connect_timeout=3000'.
            format(
                os.environ.get('BACKEND_DB_NAME'),
                os.environ.get('BACKEND_DB_USER'),
                os.environ.get('BACKEND_DB_HOST'),
                os.environ.get('BACKEND_DB_PASSWORD')))
        # conn.close()
    back_cursor = backend_connection.cursor()
    # cmte_id = 'C00326835'
    # report_id = '110915'
    for transaction_table in transaction_tables:
        table_schema_sql = """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = '{}'
        """.format(transaction_table)
        
        with connection.cursor() as cursor:
            logger.debug("fetching transaction table column names...")
            # cursor.execute(table_schema_sql, (transaction_table))
            cursor.execute(table_schema_sql)
            rows = cursor.fetchall()  
            columns = []
            for row in rows:
                # exclude report_seq from reports
                # if row[0] != 'report_seq':
                columns.append(row[0])
            logger.debug('table columns: {}'.format(list(columns)))



            insert_str = ','.join(columns)
            select_str = ','.join(columns)
            clone_sql = """
                SELECT {_select}
                FROM public.{table_name}
            """.format(table_name=transaction_table, _select=select_str)
            clone_sql = clone_sql + """ WHERE committeeid = %s and id = %s;"""
            logger.debug('clone transaction with sql:{}'.format(clone_sql))

            cursor.execute(clone_sql, (cmte_id, report_id))

            if not cursor.rowcount:
                logger.debug('no transaction data found for {}'.format(transaction_table))
                continue
            rows = cursor.fetchall()
            for row in rows:
                # print('...')
                # print(row)
                insert_sql = """
                INSERT INTO public.{table_name}({_insert}) VALUES
                """.format(table_name=transaction_table, _insert=insert_str)
                # print(insert_sql)
                back_cursor.execute(insert_sql+' %s', (row,))
                backend_connection.commit()
                logger.debug('row data {} inserted'.format(row))

    back_cursor.close()
    backend_connection.close()

@api_view(['PUT'])
def submit_report(request):
    """
    an update api used for submitting a report

    1) We need to change report status from Saved to Submitted.
    2) Update report_seq value into fec_id column.
    3) Append "FEC-" to fec_id in return value.
    3) Return JSON response: "fec_id", "status","message"
    4) use email template from "https://github.com/SalientCRGT-FEC/nxg_fec/tree/develop/django-backend/templates/email_ack.html" and replace @parameters with report values.
    5) Send confirmation email, please refer to email function in below file.
    https://github.com/SalientCRGT-FEC/nxg_fec/blob/develop/django-backend/fecfiler/forms/views.py
    """
    # print(request.data)
    # print(request.query_params)
    SUBMIT_STATUS = 'Submitted'
    cmte_id = request.user.username
    if 'report_id' in request.query_params:
        report_id = request.query_params.get('report_id')
        form_tp = request.query_params.get('form_type') 
    else:
        report_id = request.data.get('report_id')
        form_tp = request.data.get('form_type') 
    if not report_id:
        raise Exception()
    fec_id = report_id
    if form_tp == 'F3X':
        update_tbl = 'public.reports'
        f_id = 'report_id'
    elif form_tp == 'F99':
        update_tbl = 'public.forms_committeeinfo'
        f_id = 'id'
    else:
        raise Exception('Error: invalid form type.')


    if form_tp == 'F3X':
        _sql_update = """
            UPDATE {}""".format(update_tbl) + """
            SET status = %s, fec_id = %s""" + """
            WHERE {} = %s
            """.format(f_id)
    elif form_tp == 'F99':
        _sql_update = """
            UPDATE {}""".format(update_tbl) + """
            SET is_submitted = true, status = %s, fec_id = %s""" + """
            WHERE {} = %s
            """.format(f_id)
    else:
        raise Exception('Error: invalid form type.') 

    with connection.cursor() as cursor:
        cursor.execute(_sql_update, [SUBMIT_STATUS, fec_id, report_id])
        if cursor.rowcount == 0:
            raise Exception('report {} update failed'.format(report_id))

    
    if form_tp == 'F3X':
        reposit_f3x_data(cmte_id, report_id)
    elif form_tp == 'F99':
        reposit_f99_data(cmte_id, report_id)
    else:
        raise Exception('Error: invalid form type.')
    
    logger.debug('sending email with data')
    email_data = request.data.copy()
    email_data.update(request.query_params.copy())
    email_data['id'] = 'FEC-'+email_data['report_id']
    email_data['committeeid'] = cmte_id
    if 'report_type' in email_data:
        email_data['report_desc'] = email_data.get('report_type')
    if 'cvg_start_dt' in email_data:
        email_data['coverage_start_date'] = email_data.get('cvg_start_dt')
    if 'cvg_end_dt' in email_data:
        email_data['coverage_end_date'] = email_data.get('cvg_end_dt')

    logger.debug('sending email with data {}'.format(email_data))
    email(True, email_data)
    logger.debug('email success.')

    if form_tp == 'F3X':
        _sql_response = """
        SELECT json_agg(t) FROM (
            SELECT 'FEC-' || fec_id as fec_id, status, filed_date, message, cmte_id as committee_id, submission_id as submissionId, uploaded_date as upload_timestamp
            FROM public.reports
            WHERE report_id = %s)t
        """
    elif form_tp == 'F99':
        _sql_response = """
        SELECT json_agg(t) FROM (
            SELECT 'FEC-' || fec_id as fec_id, 
            status, 
            CASE
            WHEN is_submitted = true THEN updated_at
            ELSE NULL::timestamp with time zone
            END AS filed_date,
            message, committeeid as committee_id, submission_id as submissionId, uploaded_date as upload_timestamp
            FROM public.forms_committeeinfo
            WHERE id = %s)t
        """ 
    else:
        raise Exception('Error: invalid form type')

    with connection.cursor() as cursor:
        cursor.execute(_sql_response, [report_id])
        if cursor.rowcount == 0:
            raise Exception('report {} update failed'.format(report_id))
        rep_json = cursor.fetchone()[0]
    
    return JsonResponse(rep_json[0], status=status.HTTP_200_OK, safe=False)



@api_view(['POST','GET','DELETE','PUT'])
def reports(request):

    if request.method == 'POST':
        try:
            if 'amend_ind' in request.data and check_null_value(request.data.get('amend_ind')):
                amend_ind = request.data.get('amend_ind')
            else:
                amend_ind = "N"

            if 'election_code' in request.data and check_null_value(request.data.get('election_code')):
                election_code = request.data.get('election_code')
            else:
                election_code = None

            if 'status' in request.data and check_null_value(request.data.get('status')):
                f_status = request.data.get('status')
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
                'form_type': request.data.get('form_type', None),
                'amend_ind': amend_ind,
                'report_type': request.data.get('report_type', None),
                'election_code': election_code,
                'date_of_election': date_format(request.data.get('date_of_election')),
                'state_of_election': request.data.get('state_of_election', None),
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
                # print(data)
                # do h1 carryover if new report created
                do_h1_carryover(data.get('cmteid'), data.get('reportid'))
                do_h2_carryover(data.get('cmteid'), data.get('reportid'))
                do_loan_carryover(data.get('cmteid'), data.get('reportid'))
                do_debt_carryover(data.get('cmteid'), data.get('reportid'))

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
            if 'amend_ind' in request.data:
                amend_ind = request.data.get('amend_ind')
            else:
                amend_ind = "N"

            if 'election_code' in request.data:
                election_code = request.data.get('election_code')
            else:
                election_code = ""

            if 'status' in request.data:
                f_status = request.data.get('status')
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

    entity_type_list = ["CAN", "CCM", "COM", "IND", "ORG", "PAC", "PTY", "FEC"]
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
        

def save_cand_entity(data, new=False):
    """
    save a candiate entity
    """
    logger.debug('saving cand_entity with data:{}'.format(data))
    entity_fields_with_cand = [
        "cand_office",
        "cand_office_state",
        "cand_office_district",
        "cand_election_year",
    ]
    cand_data = {k: v for k, v in data.items() if k in entity_fields_with_cand}
    cand_data.update(
        {
            k.replace("cand_", ""): v
            for k, v in data.items()
            if k.startswith('cand_') and k not in entity_fields_with_cand
        }
    )
    if not new:
        cand_data["entity_id"] = data.get("beneficiary_cand_entity_id")
    else:
        cand_data['entity_id'] = get_next_entity_id('CAN')
    cand_data["cmte_id"] = data.get("cmte_id")
    cand_data["entity_type"] = "CAN"
    logger.debug("cand_data to be saved:{}".format(cand_data))
    return put_entities(cand_data)

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

def post_sql_entity(
    entity_id, 
    entity_type, 
    cmte_id, 
    entity_name, 
    first_name, 
    last_name, 
    middle_name, 
    preffix, 
    suffix, 
    street_1, 
    street_2, 
    city, 
    state, 
    zip_code, 
    occupation, 
    employer, 
    ref_cand_cmte_id,
    cand_office,
    cand_office_state,
    cand_office_district,
    cand_election_year,
    phone_number):

    try:
        with connection.cursor() as cursor:

            # Insert data into Entity table
            cursor.execute(
                """INSERT INTO public.entity 
                    (entity_id, 
                    entity_type, 
                    cmte_id, 
                    entity_name, 
                    first_name, 
                    last_name, 
                    middle_name, 
                    preffix, 
                    suffix, 
                    street_1, 
                    street_2, 
                    city, 
                    state, 
                    zip_code, 
                    occupation, 
                    employer, 
                    ref_cand_cmte_id, 
                    cand_office,
                    cand_office_state,
                    cand_office_district,
                    cand_election_year,
                    phone_number,
                    create_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
                [
                    entity_id, 
                    entity_type, 
                    cmte_id, 
                    entity_name, 
                    first_name, 
                    last_name, 
                    middle_name, 
                    preffix, 
                    suffix, 
                    street_1, 
                    street_2, 
                    city, 
                    state, 
                    zip_code, 
                    occupation, 
                    employer, 
                    ref_cand_cmte_id, 
                    cand_office,
                    cand_office_state,
                    cand_office_district,
                    cand_election_year,
                    phone_number,
                    datetime.datetime.now(),
                ]
                    )
    except Exception:
        raise

def get_list_entity(entity_id, cmte_id):
    # logger.debug("get_list_entity with entity_id {} and cmte_id {}".format(entity_id, cmte_id))
    try:
        query_string = """
        SELECT 
            entity_id, 
            entity_type, 
            cmte_id, 
            entity_name, 
            first_name, 
            last_name, 
            middle_name, 
            preffix as prefix, 
            suffix, 
            street_1, 
            street_2, 
            city, 
            state, 
            zip_code, 
            occupation, 
            employer, 
            ref_cand_cmte_id,
            cand_office,
            cand_office_state,
            cand_office_district,
            cand_election_year,
            phone_number,
            last_update_date
        FROM public.entity 
        WHERE entity_id = %s 
        AND cmte_id = %s 
        AND delete_ind is distinct from 'Y'
        """
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [entity_id, cmte_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        # logger.debug('entity data loaded:{}'.format(forms_obj))
        if forms_obj is None:
            raise NoOPError('The Entity ID: {} does not exist or is deleted'.format(entity_id))   
        return forms_obj
    except Exception:
        raise

def get_list_all_entity(cmte_id):

    try:
        query_string = """
        SELECT 
            entity_id, 
            entity_type, 
            cmte_id, 
            entity_name, 
            first_name, 
            last_name, 
            middle_name, 
            preffix as prefix, 
            suffix, 
            street_1, 
            street_2, 
            city, 
            state, 
            zip_code, 
            occupation, 
            employer, 
            ref_cand_cmte_id,
            cand_office,
            cand_office_state,
            cand_office_district,
            cand_election_year,
            phone_number,
            last_update_date
        FROM public.entity 
        WHERE cmte_id = %s 
        AND delete_ind is distinct from 'Y'
        """
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

def put_sql_entity(
    entity_type, 
    entity_name, 
    first_name, 
    last_name, 
    middle_name, 
    preffix, 
    suffix, 
    street_1, 
    street_2, 
    city, 
    state, 
    zip_code, 
    occupation, 
    employer, 
    ref_cand_cmte_id, 
    entity_id, 
    cand_office,
    cand_office_state,
    cand_office_district,
    cand_election_year,
    phone_number,
    cmte_id):

    try:
        with connection.cursor() as cursor:
            # Put data into Entity table
            # cursor.execute("""UPDATE public.entity SET entity_type = %s, entity_name = %s, first_name = %s, last_name = %s, middle_name = %s, preffix = %s, suffix = %s, street_1 = %s, street_2 = %s, city = %s, state = %s, zip_code = %s, occupation = %s, employer = %s, ref_cand_cmte_id = %s, last_update_date = %s WHERE entity_id = %s AND cmte_id = %s AND delete_ind is distinct FROM 'Y'""",
            #             (entity_type, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, ref_cand_cmte_id, last_update_date, entity_id, cmte_id))                       
            cursor.execute(
                """
                UPDATE public.entity SET 
                    entity_type = %s, 
                    entity_name = %s, 
                    first_name = %s, 
                    last_name = %s, 
                    middle_name = %s, 
                    preffix = %s, 
                    suffix = %s, 
                    street_1 = %s, 
                    street_2 = %s, 
                    city = %s, 
                    state = %s, 
                    zip_code = %s, 
                    occupation = %s, 
                    employer = %s, 
                    ref_cand_cmte_id = %s,
                    cand_office = %s,
                    cand_office_state = %s,
                    cand_office_district = %s,
                    cand_election_year = %s,
                    phone_number=%s,
                    last_update_date=%s
                WHERE entity_id = %s AND cmte_id = %s 
                AND delete_ind is distinct FROM 'Y'
                """,
                [
                    entity_type, 
                    entity_name, 
                    first_name, 
                    last_name, 
                    middle_name, 
                    preffix, 
                    suffix, 
                    street_1, 
                    street_2, 
                    city, 
                    state, 
                    zip_code, 
                    occupation, 
                    employer, 
                    ref_cand_cmte_id, 
                    cand_office,
                    cand_office_state,
                    cand_office_district,
                    cand_election_year,
                    phone_number,
                    datetime.datetime.now(),
                    # last_update_date,
                    entity_id, 
                    cmte_id,
                    ])                       
            if (cursor.rowcount == 0):
                raise Exception(
                    'The Entity ID: {} does not exist in Entity table'.format(entity_id))
    except Exception:
        raise

def delete_sql_entity(entity_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # UPDATE delete_ind flag to Y in DB
            # cursor.execute("""UPDATE public.entity SET delete_ind = 'Y', last_update_date = %s WHERE entity_id = '""" + entity_id + """' AND cmte_id = '""" + cmte_id + """' AND delete_ind is distinct from 'Y'""", (datetime.now()))
            cursor.execute(
                """
                UPDATE public.entity 
                SET delete_ind = 'Y' 
                WHERE entity_id = %s 
                AND cmte_id = %s 
                AND delete_ind is distinct from 'Y'
                """, 
                [entity_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception(
                    """The Entity ID: {} is either already deleted or does not 
                    exist in Entity table""".format(entity_id))
    except Exception:
        raise

def undo_delete_sql_entity(entity_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # UPDATE delete_ind flag to Y in DB
            # cursor.execute("""UPDATE public.entity SET delete_ind = 'Y', last_update_date = %s WHERE entity_id = '""" + entity_id + """' AND cmte_id = '""" + cmte_id + """' AND delete_ind is distinct from 'Y'""", (datetime.now()))
            cursor.execute(
                """
                UPDATE public.entity 
                SET delete_ind = '' 
                WHERE entity_id = %s 
                AND cmte_id = %s 
                AND delete_ind = 'Y'
                """, 
                [entity_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception(
                    'The Entity ID: {} is not deleted or does not exist in Entity table'.format(entity_id))
    except Exception:
        raise

def remove_sql_entity(entity_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # DELETE row from entity table    
            cursor.execute(
                """
                DELETE FROM public.entity 
                WHERE entity_id = %s 
                AND cmte_id = %s
                """, 
                [entity_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception(
                    'The Entity ID: {} does not exist in Entity table'.format(entity_id))
    except Exception:
        raise
"""
************************************************ API FUNCTIONS - ENTITIES **********************************************************
"""
def post_entities(data):

    try:
        check_mandatory_fields_entity(data)
        if data.get('prefix'):
            data['preffix'] = data.get('prefix')
        entity_type = data.get('entity_type')
        check_entity_type(entity_type)
        entity_id = get_next_entity_id(entity_type)
        data['entity_id'] = entity_id
        post_sql_entity(
            entity_id, 
            data.get('entity_type'), 
            data.get('cmte_id'), 
            data.get('entity_name'), 
            data.get('first_name'), 
            data.get('last_name'), 
            data.get('middle_name'),
            data.get('preffix'), 
            data.get('suffix'), 
            data.get('street_1'), 
            data.get('street_2'), 
            data.get('city'), 
            data.get('state'), 
            data.get('zip_code'), 
            data.get('occupation'), 
            data.get('employer'), 
            data.get('ref_cand_cmte_id'),
            data.get('cand_office'),
            data.get('cand_office_state'),
            data.get('cand_office_district'),
            data.get('cand_election_year'),
            data.get('phone_number'),
            # data.get('last_update_date')
            )
        output = get_entities(data)
        return output[0]
    except:
        raise

def get_entities(data):

    try:
        cmte_id = data.get('cmte_id')
        entity_flag = False
        if 'entity_id' in data:
            # logger.debug('load entity with entity id: {}'.format(data.get('entity_id')))
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

def clone_fec_entity(cmte_id, entity_type, entity_id):
    """
    a helper function for handling FEC entity:
    clone FEC entity and mark it for future query exclusion
    """
    new_entity_id = get_next_entity_id(entity_type)
    clone_sql = """
            INSERT INTO public.entity(
                entity_id, entity_type, cmte_id, entity_name, 
                first_name, last_name, middle_name, preffix, 
                suffix, street_1, street_2, city, state, zip_code, 
                occupation, employer, ref_cand_cmte_id, delete_ind, 
                create_date, last_update_date, cand_office, cand_office_state, 
                cand_office_district, cand_election_year, phone_number)
            SELECT %s, entity_type, %s, entity_name, 
                first_name, last_name, middle_name, preffix, 
                suffix, street_1, street_2, city, state, zip_code, 
                occupation, employer, ref_cand_cmte_id, delete_ind, 
                create_date, last_update_date, cand_office, cand_office_state, 
                cand_office_district, cand_election_year, phone_number
            FROM public.entity e 
            WHERE e.entity_id = %s;
            """
    exclude_sql = """
    INSERT INTO excluded_entity(entity_id, cmte_id) values(%s, %s);
    """
    with connection.cursor() as cursor:
        # UPDATE delete_ind flag to Y in DB
        # cursor.execute("""UPDATE public.entity SET delete_ind = 'Y', last_update_date = %s WHERE entity_id = '""" + entity_id + """' AND cmte_id = '""" + cmte_id + """' AND delete_ind is distinct from 'Y'""", (datetime.now()))
        cursor.execute(clone_sql, [new_entity_id, cmte_id, entity_id])
        if (cursor.rowcount == 0):
            raise Exception(
                """ FEC Entity ID: {} clone failure.""".format(entity_id))
        cursor.execute(exclude_sql, [entity_id, cmte_id])
        if (cursor.rowcount == 0):
            raise Exception(
                """ FEC Entity ID: {} exclusion failure.""".format(entity_id))
    return new_entity_id

# TODO: need to dsicuss if we need to handle clone-and-update scenario
def put_entities(data):

    try:
        check_mandatory_fields_entity(data)
        if data.get('prefix'):
            data['preffix'] = data.get('prefix')
        cmte_id = data.get('cmte_id')
        entity_type = data.get('entity_type')
        check_entity_type(entity_type)
        entity_id = data.get('entity_id')
        check_entity_id(entity_id)

        # adding code for handling FEC entity
        # add a clone version of FEC entity and update it with current data
        if entity_id.startswith('FEC'):
            logger.debug('current entity {} is FEC entity, need to clone it.'.format(entity_id))
            new_entity_id = clone_fec_entity(cmte_id, entity_type, entity_id)
            # combine db entity data and request entity data
            # fields from api request take priority here
            data['entity_id'] = new_entity_id
            cloned_data = get_entities(data)[0]
            # remove None value field from data
            # TODO: need to evaluate if this 100Per safe
            data = { k:v for k,v in data.items() if v }
            cloned_data.update(data)
            data = cloned_data
        else:
            logger.debug('combine existing data with new data:')
            existing_data = get_entities(data)[0]
            logger.debug('existing data:{}'.format(existing_data))
            # remove None value field from data
            data = { k:v for k,v in data.items() if v }
            existing_data.update(data)
            data = existing_data
            logger.debug('data after update existing data with new data:{}'.format(data))

            # logger.debug('cloned cand entity data:{}'.format(cloned_data))
            # return cloned_data
        # filter out cand_fields for non-can entity
        if data['entity_type'] != 'CAN':
            data = { k:v for k,v in data.items() if not k.startswith('cand_') }

        # for sched_a only, update ref_cand_cmte_id with donor_cmte_id if not null
        if data.get('donor_cmte_id'):
            data['ref_cand_cmte_id'] = data.get('donor_cmte_id')

        # for sched_b only, update ref_cand_cmte-id with beneficiary_cmte_id if not null
        if data.get('beneficiary_cmte_id'):
            data['ref_cand_cmte_id'] = data.get('beneficiary_cmte_id')
            
        logger.debug('put_sql_entity with data:{}'.format(data))
        put_sql_entity(
            data.get('entity_type'), 
            data.get('entity_name'), 
            data.get('first_name'), 
            data.get('last_name'), 
            data.get('middle_name'), 
            data.get('preffix'), 
            data.get('suffix'), 
            data.get('street_1'), 
            data.get('street_2'), 
            data.get('city'), 
            data.get('state'), 
            data.get('zip_code'), 
            data.get('occupation'), 
            data.get('employer'), 
            data.get('ref_cand_cmte_id'), 
            data.get('entity_id'), 
            data.get('cand_office'),
            data.get('cand_office_state'),
            data.get('cand_office_district'),
            data.get('cand_election_year', None),
            data.get('phone_number'),
            # data.get('last_update_date'),
            cmte_id)
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
                    'cand_office': request.data.get('cand_office'),
                    'cand_office_state': request.data.get('cand_office_state'),
                    'cand_office_district': request.data.get('cand_office_district'),
                    'cand_election_year': request.data.get('cand_election_year'),
                    'phone_number': request.data.get('phone_number'),
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
                'cand_office': request.data.get('cand_office'),
                'cand_office_state': request.data.get('cand_office_state'),
                'cand_office_district': request.data.get('cand_office_district'),
                'cand_election_year': request.data.get('cand_election_year'),
                'phone_number': request.data.get('phone_number'),
                # 'last_update_date': request.data.get('last_update_date')
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
    """
    We are changing autoloopup to the converged entity table:
    Parameter name remapping for candidate and committee:
    cmte_id --> ref_cand_cmte_id
    cmte_name --> entity_name
    cand_id --> ref_cand_cmte_id
    cand_last_name --> last_name
    cand_first_name --> first_name
    """
    logger.debug('autolookup with request params:{}'.format(dict(request.query_params.items())))

    allowed_params = [
        'entity_name', 
        'first_name', 
        'last_name', 
        'preffix',
        'prefix',
        'suffix',
        'ref_cand_cmte_id', 
        'principal_campaign_committee'
        ] 
    field_remapper = {
        'cmte_id': 'ref_cand_cmte_id',
        'cmte_name': 'entity_name',
        'cand_id': 'ref_cand_cmte_id',
        'cand_last_name': 'last_name',
        'cand_first_name': 'first_name',
        'payee_cmte_id': 'principal_campaign_committee',
    }

    try:
        committee_id = request.user.username
        param_string = ""
        order_string = ""
        search_string = ""
        query_string = ""
        # cand_q = False
        # cmte_q = False

        # for k in request.query_params:
        #     if k.startswith('cand_'):
        #         cand_q = True
        #     if k.startswith('cmte_'):
        #         cmte_q = True

        
        # rename parameters for candidate and committee
        query_params = { k:v for k,v in request.query_params.items() if k not in field_remapper }
        query_params.update({field_remapper[k]:v for k,v in request.query_params.items() if k in field_remapper})
        if 'prefix' in query_params:
            query_params['preffix'] = query_params.get('prefix')
            

        logger.debug("autolookup with parameters {}".format(query_params))
        for key, value in query_params.items():
            if key in allowed_params:
                if key == 'prefix':
                    continue
                order_string = str(key)
                param_string = " AND LOWER(" + str(key) + ") LIKE LOWER(%s)"
                # if cand_q:
                #     query_string = """
                #     SELECT json_agg(t) FROM 
                #     (SELECT e.preffix as cand_prefix, 
                #             e.last_name as cand_last_name,
                #             e.first_name as cand_first_name,
                #             e.middle_name as cand_middle_name,
                #             e.suffix as cand_suffix,
                #             *
                #     FROM public.entity e WHERE cmte_id in (%s, 'C00000000')
                #     AND e.entity_id not in (select ex.entity_id from excluded_entity ex where cmte_id = %s)
                #     """ + param_string + """ AND delete_ind is distinct from 'Y' ORDER BY """ + order_string + """) t"""
                # elif cmte_q:
                #     query_string = """
                #     SELECT json_agg(t) FROM 
                #     (SELECT e.preffix as prefix, e.entity_name as cmte_name, *
                #     FROM public.entity e WHERE cmte_id in (%s, 'C00000000')
                #     AND e.entity_id not in (select ex.entity_id from excluded_entity ex where cmte_id = %s)
                #     """ + param_string + """ AND delete_ind is distinct from 'Y' ORDER BY """ + order_string + """) t"""
                #     pass
                # else
                # 
                # :
                # print('haha')
                # print('cmte-id' in list(request.query_params.items()))
                if 'cmte_id' in request.query_params:
                    parameters = [committee_id]
                    query_string = """
                        SELECT json_agg(t) FROM 
                        (SELECT e.ref_cand_cmte_id as cmte_id,e.entity_id,e.entity_type,e.entity_name as cmte_name,e.entity_name,e.first_name,e.last_name,e.middle_name,
                          e.preffix,e.suffix,e.street_1,e.street_2,e.city,e.state,e.zip_code,e.occupation,e.employer,e.ref_cand_cmte_id,e.delete_ind,e.create_date,
                        e.last_update_date
                        FROM public.entity e WHERE e.cmte_id in ('C00000000') 
                        AND substr(e.ref_cand_cmte_id,1,1)='C'
                        AND e.entity_id not in (select ex.entity_id from excluded_entity ex where cmte_id = %s)
                        """ + param_string + """ AND delete_ind is distinct from 'Y' ORDER BY """ + order_string + """) t"""
                elif (
                    'cand_id' in request.query_params
                    or 'cand_first_name' in request.query_params
                    or 'cand_last_name' in request.query_params
                    or 'payee_cmte_id' in request.query_params
                    ):
                    parameters = [committee_id]
                    query_string = """
                        SELECT json_agg(t) FROM 
                        (SELECT e.ref_cand_cmte_id as beneficiary_cand_id,e.entity_id as beneficiary_cand_entity_id,e.preffix as cand_prefix,e.last_name as cand_last_name,
                        e.first_name as cand_first_name,e.middle_name as cand_middle_name,e.suffix as cand_suffix,e.entity_id,e.entity_type,e.street_1,e.street_2,
                        e.city,e.state,e.zip_code,e.ref_cand_cmte_id,e.delete_ind,e.create_date,e.last_update_date,e.cand_office,e.cand_office_state,
                        e.cand_office_district,e.cand_election_year, e.principal_campaign_committee as payee_cmte_id
                        FROM public.entity e WHERE e.cmte_id in ('C00000000') 
                        AND e.entity_id not in (select ex.entity_id from excluded_entity ex where cmte_id = %s)
                        AND substr(e.ref_cand_cmte_id,1,1) != 'C'
                        """ + param_string + """ AND delete_ind is distinct from 'Y' ORDER BY """ + order_string + """) t"""
                else:
                    parameters = [committee_id, committee_id]
                    query_string = """
                        SELECT json_agg(t) FROM 
                        (SELECT e.ref_cand_cmte_id as cmte_id,e.entity_id,e.entity_type,e.entity_name as cmte_name,e.entity_name,e.first_name,e.last_name,e.middle_name,
                        e.preffix,e.suffix,e.street_1,e.street_2,e.city,e.state,e.zip_code,e.occupation,e.employer,e.ref_cand_cmte_id,e.delete_ind,e.create_date,
                        e.last_update_date
                        FROM public.entity e WHERE e.cmte_id in (%s)
                        AND e.entity_id not in (select ex.entity_id from excluded_entity ex where cmte_id = %s)
                        """ + param_string + """ AND delete_ind is distinct from 'Y' ORDER BY """ + order_string + """) t"""

                parameters.append(value + '%')
                # parameters.append('C%')
            # elif key in ['cmte_id', 'cmte_name']:
            #     param_string = " LOWER(" + str(key) + ") LIKE LOWER(%s)"
            #     query_string = """SELECT json_agg(t) FROM (SELECT cmte_id, cmte_name, street_1, street_2, city, state, zip_code, cmte_email_1, cmte_email_2, phone_number, cmte_type, cmte_dsgn, cmte_filing_freq, cmte_filed_type, treasurer_last_name, treasurer_first_name, treasurer_middle_name, treasurer_prefix, treasurer_suffix
            #                                         FROM public.committee_master WHERE""" + param_string + """ ORDER BY """ + order_string + """) t"""
            #     parameters = [value + '%']
            # elif key in ['cand_id', 'cand_last_name', 'cand_first_name']:
            #     param_string = " LOWER(" + str(key) + ") LIKE LOWER(%s)"
            #     query_string = """SELECT json_agg(t) FROM (SELECT cand_id, cand_last_name, cand_first_name, cand_middle_name, cand_prefix, cand_suffix, cand_street_1, cand_street_2, cand_city, cand_state, cand_zip, cand_party_affiliation, cand_office, cand_office_state, cand_office_district, cand_election_year
            #                                         FROM public.candidate_master WHERE""" + param_string + """ ORDER BY """ + order_string + """) t"""
            #     parameters = [value + '%']
            # else:
            #     raise Exception("The parameters for this api should be limited to: ['entity_name', 'first_name', 'last_name', 'cmte_id', 'cmte_name', 'cand_id', 'cand_last_name', 'cand_first_name']")

        if query_string == "":
            raise Exception("One parameter has to be passed for this api to display results. The parameters should be limited to: ['entity_name', 'first_name', 'last_name', 'cmte_id', 'cmte_name', 'cand_id', 'cand_last_name', 'cand_first_name', 'payee_cmte_id']")
        with connection.cursor() as cursor:
            logger.debug("autolookup query:{}".format(query_string))
            logger.debug("autolookup parameters:{}".format(parameters))
            cursor.execute(query_string, parameters)
            # print(cursor.query)
            # print('fail..')
            for row in cursor.fetchall():
                data_row = list(row)
                # logger.debug('current data row:{}'.format())
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
- MODIFIED SPRINT 26 - BY Praveen
**********************************************************************************************************************************************
"""

def get_trans_query(category_type, cmte_id, param_string):
        
    if category_type == 'disbursements_tran':
        query_string = """SELECT report_id, report_type, reportStatus, transaction_type, transaction_type_desc, transaction_id, api_call, name, street_1, street_2, city, state, zip_code, transaction_date, 
                                COALESCE(transaction_amount, 0.0) AS transaction_amount, back_ref_transaction_id,
                                COALESCE(aggregate_amt, 0.0) AS aggregate_amt, purpose_description, occupation, employer, memo_code, memo_text, itemized, beneficiary_cmte_id, election_code, 
                                election_year, election_other_description,transaction_type_identifier, entity_id, entity_type, deleteddate, isEditable, hasChild from all_disbursements_transactions_view
                            where cmte_id='""" + cmte_id + """' """ + param_string + """ """

    elif category_type == 'loans_tran':
        query_string = """SELECT report_id, report_type, reportStatus, transaction_type, transaction_type_desc, transaction_id, api_call, name, street_1, street_2, city, state, zip_code, occupation, employer, 
                          purpose_description, loan_amount, loan_payment_to_date, loan_incurred_date, loan_due_date, loan_beginning_balance, loan_incurred_amt, loan_payment_amt, 
                          loan_closing_balance, memo_code, memo_text, transaction_type_identifier, entity_id, entity_type, deleteddate, isEditable, hasChild from all_loans_debts_transactions_view
                            where cmte_id='""" + cmte_id + """' """ + param_string + """ """

    elif category_type == 'other_tran':
        query_string = """SELECT report_id, schedule, report_type, reportStatus, activity_event_identifier, transaction_type, transaction_type_desc, transaction_id, back_ref_transaction_id, api_call, 
                          name, street_1, street_2, city, state, zip_code, transaction_date, COALESCE(transaction_amount, 0.0) AS transaction_amount, 
                                COALESCE(aggregate_amt, 0.0) AS aggregate_amt, purpose_description, occupation, employer, memo_code, memo_text, itemized, 
                                election_code, election_other_description, transaction_type_identifier, entity_id, entity_type, deleteddate, isEditable, hasChild, istrashable
                            from all_other_transactions_view
                            where cmte_id='""" + cmte_id + """' """ + param_string + """ """ 
    else:
        query_string = """SELECT report_id, report_type, reportStatus, transaction_type, transaction_type_desc, transaction_id, api_call, name, street_1, street_2, city, state, zip_code, transaction_date, 
                                COALESCE(transaction_amount, 0.0) AS transaction_amount, back_ref_transaction_id,
                                COALESCE(aggregate_amt, 0.0) AS aggregate_amt, purpose_description, occupation, employer, memo_code, memo_text, itemized, election_code, election_other_description, 
                                transaction_type_identifier, entity_id, entity_type, deleteddate, isEditable, hasChild from all_receipts_transactions_view
                            where cmte_id='""" + cmte_id + """' """ + param_string + """ """
    return query_string

def filter_get_all_trans(request, param_string):
    # if request.method == 'GET':
    #     return param_string
    filt_dict = request.data.get('filters', {})
    ctgry_type = request.data.get('category_type')
    # print(filt_dict)
    if filt_dict.get('filterCategories'):
        cat_tuple = "('"+"','".join(filt_dict['filterCategories'])+"')"
        param_string = param_string + " AND transaction_type_desc In " + cat_tuple
    if filt_dict.get('filterDateFrom') not in [None, 'null']:
        param_string = param_string + " AND transaction_date >= '" + filt_dict['filterDateFrom'] + "'"
    if filt_dict.get('filterDateTo') not in [None, 'null']:
        param_string = param_string + " AND transaction_date <= '" + filt_dict['filterDateTo'] + "'"
    # The below code was added by Praveen. This is added to reuse this function in get_all_trashed_transactions API.
    if filt_dict.get('filterDeletedDateFrom') not in [None, 'null']:
        param_string = param_string + " AND date(last_update_date) >= '" + filt_dict['filterDeletedDateFrom'] + "'"
    if filt_dict.get('filterDeletedDateTo') not in [None, 'null']:
        param_string = param_string + " AND date(last_update_date) <= '" + filt_dict['filterDeletedDateTo'] + "'"
    # End of Addition
    if filt_dict.get('filterAmountMin') not in [None, 'null']:
        param_string = param_string + " AND transaction_amount >= '" + str(filt_dict['filterAmountMin']) + "'"
    if filt_dict.get('filterAmountMax') not in [None, 'null']:
        param_string = param_string + " AND transaction_amount <= '" + str(filt_dict['filterAmountMax']) + "'"
    if filt_dict.get('filterAggregateAmountMin') not in [None, 'null']:
        param_string = param_string + " AND aggregate_amt >= '" + str(filt_dict['filterAggregateAmountMin']) + "'"
    if filt_dict.get('filterAggregateAmountMax') not in [None, 'null']:
        param_string = param_string + " AND aggregate_amt <= '" + str(filt_dict['filterAggregateAmountMax']) + "'"
    if filt_dict.get('filterStates'):
        state_tuple = "('"+"','".join(filt_dict['filterStates'])+"')"
        param_string = param_string + " AND state In " + state_tuple
    if filt_dict.get('filterItemizations'):
        itemized_tuple = "('"+"','".join(filt_dict['filterItemizations'])+"')"
        param_string = param_string + " AND itemized In " + itemized_tuple
    if filt_dict.get('filterElectionCodes'):
        election_tuple = "('"+"','".join(filt_dict['filterElectionCodes'])+"')"
        param_string = param_string + " AND election_code In " + election_tuple
    if filt_dict.get('filterElectionYearFrom') not in [None, 'null']:
        param_string = param_string + " AND election_year >= '" + filt_dict['filterElectionYearFrom'] + "'"
    if filt_dict.get('filterElectionYearTo') not in [None, 'null']:
        param_string = param_string + " AND election_year <= '" + filt_dict['filterElectionYearTo'] + "'"
    if ctgry_type == 'loans_tran' and filt_dict.get('filterLoanAmountMin') not in [None, 'null']:
        param_string = param_string + " AND loan_amount >= '" + str(filt_dict['filterLoanAmountMin']) + "'"
    if ctgry_type == 'loans_tran' and filt_dict.get('filterLoanAmountMax') not in [None, 'null']:
        param_string = param_string + " AND loan_amount <= '" + str(filt_dict['filterLoanAmountMax']) + "'"
    if ctgry_type == 'loans_tran' and filt_dict.get('filterLoanClosingBalanceMin') not in [None, 'null']:
        param_string = param_string + " AND loan_closing_balance >= '" + str(filt_dict['filterLoanClosingBalanceMin']) + "'"
    if ctgry_type == 'loans_tran' and filt_dict.get('filterLoanClosingBalanceMax') not in [None, 'null']:
        param_string = param_string + " AND loan_closing_balance <= '" + str(filt_dict['filterLoanClosingBalanceMax']) + "'"
    if ctgry_type == 'loans_tran' and filt_dict.get('filterDebtBeginningBalanceMin') not in [None, 'null']:
        param_string = param_string + " AND loan_beginning_balance >= '" + str(filt_dict['filterDebtBeginningBalanceMin']) + "'"
    if ctgry_type == 'loans_tran' and filt_dict.get('filterDebtBeginningBalanceMax') not in [None, 'null']:
        param_string = param_string + " AND loan_beginning_balance <= '" + str(filt_dict['filterDebtBeginningBalanceMax']) + "'"
    # print(param_string)
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

# def load_child_transactions(cmte_id, report_id, ctgry_type):
#     """
#     a helper function to query and load all child transactions
#     """
#     query_string = get_child_query_string(ctgry_type)
#     if report_id is None:
#         child_query_string = query_string + """ WHERE cmte_id = %s AND NOT(back_ref_transaction_id IS NULL OR back_ref_transaction_id = '')
#                         AND delete_ind is distinct from 'Y') t;
#                     """
#     else:
#         report_list = superceded_report_id_list(report_id)
#         child_query_string = query_string + """ WHERE report_id in ('{}') AND cmte_id = %s AND NOT(back_ref_transaction_id iIS NULL OR back_ref_transaction_id = '')
#             AND delete_ind is distinct from 'Y') t;
#             """.format("', '".join(report_list))
#     child_dic = {}

#     #child_query_view = get_query_view(ctgry_type)
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute(child_query_string, [cmte_id])
#             child_list = cursor.fetchone()
#             if child_list and ctgry_type!= 'loans_tran':
#                 if child_list[0]:
#                     return child_list[0]
#                 else:
#                     return []
#             else:
#                 return []
#             # TODO : update null value, NOT SURE it is necessary
#             # just go with parent function
#             # if child_list:
#             #     for child in child_list:
#             #         for i in child:
#             #             if not child[i] and i not in ['transaction_amount', 'aggregate_amt']:
#             #                 child[i] = ''
#             #             elif not child[i]:
#             #                 child[i] = 0
#             #         if child['back_ref_transaction_id'] not in child_dic:
#             #             child_dic[child['back_ref_transaction_id']] = [child]
#             #         else:
#             #             child_dic[child['back_ref_transaction_id']].append(child)
#     except Exception as e:
#         # logger.debug("loading child errors:" + str(e))
#         raise
#     # logger.debug('child dictionary loaded with {} items'.format(child_dic))
#     # return child_dic

def superceded_report_id_list(report_id):
    try:
        report_list = []
        report_list.append(str(report_id))
        reportId = []
        # print(report_list)
        while True:
            # print('in loop')
            with connection.cursor() as cursor:
                query_string = """SELECT previous_report_id FROM public.reports WHERE report_id = %s AND form_type = 'F3X' AND delete_ind is distinct FROM 'Y' """
                cursor.execute(query_string, [report_id])
                reportId = cursor.fetchone()
            # print(reportId)
            if reportId is None:
                break
            elif reportId[0] is None:
                break
            else:
                report_list.append(str(reportId[0]))
                report_id = reportId[0]
        # print(report_list)
        return report_list
    except Exception as e:
        raise

def get_core_sched_c1(cmte_id, back_ref_transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET rows from schedC1 table
            _sql = """SELECT json_agg(t) FROM ( SELECT 
            cmte_id,
            report_id,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            last_update_date
            FROM public.sched_c1
            WHERE cmte_id = %s AND back_ref_transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, [cmte_id, back_ref_transaction_id])
            schedC1_list = cursor.fetchone()
            if schedC1_list and schedC1_list[0]:
                return schedC1_list[0]
            else:
                return []
    except Exception as e:
        raise Exception ('The get_core_sched_c1 function is throwing an error: ' + str(e))

def get_core_sched_c2(cmte_id, back_ref_transaction_id):
    """
    load c2 child transactions for sched_c without report_id
    """
    _sql = """
    SELECT 
            cmte_id,
            report_id,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            last_update_date
    FROM public.sched_c2
    WHERE cmte_id = %s 
    AND back_ref_transaction_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + _sql + """) t""",[cmte_id, back_ref_transaction_id])
            schedC2_list = cursor.fetchone()
            if schedC2_list and schedC2_list[0]:
                return schedC2_list[0]
            else:
                return []
    except Exception as e:
        raise Exception ('The get_core_sched_c2 function is throwing an error: ' + str(e))

@api_view(['GET', 'POST'])
def get_all_transactions(request):
    try:
        # print("request.data: ", request.data)
        cmte_id = request.user.username
        ctgry_type = request.data.get('category_type')
        param_string = ""
        page_num = int(request.data.get('page', 1))
        descending = request.data.get('descending', 'false')
        if not ('sortColumnName' in request.data and check_null_value(request.data.get('sortColumnName'))):
            sortcolumn = 'name'
        elif request.data.get('sortColumnName') == 'default':
            sortcolumn = 'name'
        else:
            sortcolumn = request.data.get('sortColumnName')
        itemsperpage = request.data.get('itemsPerPage', 5)
        search_string = request.data.get('search')
        params = request.data.get('filters', {})
        keywords = params.get('keywords')
        if str(descending).lower() == 'true':
            descending = 'DESC'
        else:
            descending = 'ASC'

        # Search and Key word string Handling
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
        
        # ADDED the below code to access transactions across reports
        if 'reportid' in request.data and str(request.data.get('reportid')) not in ['',"", "null", "none"]:
            # add carryover code here so that carryover can be triggered by get_all_transactions
            if int(request.data.get('reportid')) != 0:
                # disable h1 carryover triggered by this API call
                # do_h1_carryover(cmte_id, request.data.get('reportid'))
                do_h2_carryover(cmte_id, request.data.get('reportid'))
                do_loan_carryover(cmte_id, request.data.get('reportid'))
                do_debt_carryover(cmte_id, request.data.get('reportid'))
            report_list = superceded_report_id_list(request.data.get('reportid'))
            if ctgry_type != 'other_tran':
                param_string += " AND report_id in ('{}')".format("', '".join(report_list))
            else:
                if cmte_type(cmte_id) == 'PTY':
                    logger.debug('pty cmte all_other transactions')
                    param_string = param_string + """AND ((transaction_table != 'sched_h2' AND report_id = '{0}')
                                                    OR 
                                                    (transaction_table = 'sched_h2' AND report_id = '{0}' AND ratio_code = 'n')
                                                    OR
                                                    (transaction_table = 'sched_h2' AND report_id = '{0}' AND name IN (
                                                    SELECT h4.activity_event_identifier FROM public.sched_h4 h4
                                                    WHERE  h4.report_id = '{0}'
                                                    AND h4.cmte_id = '{1}'
                                                    UNION
                                                    SELECT h3.activity_event_name
                                                    FROM   public.sched_h3 h3
                                                    WHERE  h3.report_id = '{0}'
                                                    AND h3.cmte_id = '{1}')))""".format(request.data.get('reportid'), cmte_id)
                else:
                    # for PAC, h1 and h2 will show up only when there are transactions tied to it
                    logger.debug('pac cmte all_other transactions')
                    param_string = param_string + """AND (((transaction_table = 'sched_h3' or transaction_table = 'sched_h4') AND report_id = '{0}')
                                                    OR
                                                    (transaction_table = 'sched_h1' AND report_id = '{0}' AND back_ref_transaction_id is null)
                                                    OR
                                                    (transaction_table = 'sched_h1' AND report_id = '{0}' AND transaction_id IN (
                                                    with h1_set as (select  (
                                                    case when administrative is true then 'AD'
                                                    when public_communications is true then 'PC'
                                                    when generic_voter_drive is true then 'GV'
                                                    end) as event_type, transaction_id, cmte_id, report_id
                                                    from sched_h1 where delete_ind is distinct from 'Y' and report_id = '{0}')
                                                    select distinct t.transaction_id from h1_set t
                                                    join sched_h4 h4 on t.event_type = h4.activity_event_type and h4.report_id = t.report_id
                                                    where h4.delete_ind is distinct from 'Y'
                                                    union
                                                    select distinct t.transaction_id from h1_set t
                                                    join sched_h3 h3 on t.event_type = h3.activity_event_type and h3.report_id = t.report_id
                                                    where h3.delete_ind is distinct from 'Y'
                                                    ))
                                                    OR 
                                                    (transaction_table = 'sched_h2' AND report_id = '{0}' AND ratio_code = 'n')
                                                    OR
                                                    (transaction_table = 'sched_h2' AND report_id = '{0}' AND name IN (
                                                    SELECT h4.activity_event_identifier FROM public.sched_h4 h4
                                                    WHERE  h4.report_id = '{0}'
                                                    AND h4.cmte_id = '{1}'
                                                    AND h4.delete_ind is distinct from 'Y'
                                                    UNION
                                                    SELECT h3.activity_event_name
                                                    FROM   public.sched_h3 h3
                                                    WHERE  h3.report_id = '{0}'
                                                    AND h3.delete_ind is distinct from 'Y'
                                                    AND h3.cmte_id = '{1}')))""".format(request.data.get('reportid'), cmte_id)


        # To determine if we are searching for regular or trashed transactions
        if 'trashed_flag' in request.data and str(request.data.get('trashed_flag')).lower() == 'true':
            param_string += " AND delete_ind = 'Y'"
        else:
            param_string += " AND delete_ind is distinct from 'Y'"
        
        filters_post = request.data.get('filters', {})
        memo_code_d = filters_post.get('filterMemoCode', False)
        if str(memo_code_d).lower() == 'true':
            param_string = param_string + " AND memo_code IS NOT NULL AND memo_code != ''"
        
        trans_query_string = get_trans_query(ctgry_type,cmte_id, param_string)

        # transactions ordering ASC or DESC
        if ctgry_type == 'loans_tran':
            trans_query_string = trans_query_string + """ ORDER BY {} {}, loan_incurred_date  ASC, create_date ASC""".format(sortcolumn, descending)
        else:
            trans_query_string = trans_query_string + """ ORDER BY {} {}, transaction_date  ASC, create_date ASC""".format(sortcolumn, descending)

        output_list = []
        total_amount = 0.0
        with connection.cursor() as cursor:
            # logger.debug('query all transactions with sql:{}'.format(trans_query_string))
            cursor.execute("""SELECT json_agg(t) FROM (""" + trans_query_string + """) t""")
            print(cursor.query)
            data_row = cursor.fetchone()
            print(data_row)
            if data_row and data_row[0]:
                transaction_list = data_row[0]
                logger.debug('total transactions loaded:{}'.format(len(transaction_list)))
                status_value = status.HTTP_200_OK
                # Sorting parents and child transactions
                if ctgry_type == 'loans_tran':
                    for transaction in transaction_list:
                        c1_list = get_core_sched_c1(cmte_id, transaction.get('transaction_id'))
                        # print(c1_list)
                        for c1 in c1_list:
                            c1['schedule'] = 'sched_c1'
                            c1['api_call'] = '/sc/schedC1'
                        c2_list = get_core_sched_c2(cmte_id, transaction.get('transaction_id'))
                        for c2 in c2_list:
                            c2['schedule'] = 'sched_c2'
                            c2['api_call'] = '/sc/schedC2'
                        if c1_list or c2_list:
                            transaction['child'] = []
                            transaction['child'].extend(c1_list + c2_list)
                    output_list = transaction_list
                    logger.debug('loans_transactions:')
                else:
                    transaction_dict = {trans.get('transaction_id'): trans for trans in transaction_list}
                    for tran_id,transaction in transaction_dict.items():
                        if transaction.get('memo_code') != 'X':
                            total_amount += transaction.get('transaction_amount', 0.0)
                        # if transaction.get('transaction_type_identifier') in NOT_DELETE_TRANSACTION_TYPE_IDENTIFIER:
                        #     transaction['isEditable'] = False
                        if transaction.get('back_ref_transaction_id') is not None and transaction.get('back_ref_transaction_id') in transaction_dict: 
                            parent = transaction_dict.get(transaction.get('back_ref_transaction_id'))
                            if 'child' not in parent:
                                parent['child'] = []
                            parent['child'].append(transaction)
                        else:
                            output_list.append(transaction)
            else:
                status_value = status.HTTP_200_OK
        # logger.debug(output_list)
        total_count = len(output_list)
        paginator = Paginator(output_list, itemsperpage)
        if paginator.num_pages < page_num:
            forms_obj = []
        else:
            forms_obj = paginator.page(page_num)
        json_result = {'transactions': list(forms_obj), 'totalTransactionCount': total_count,
                    'itemsPerPage': itemsperpage, 'pageNumber': page_num,'totalPages':paginator.num_pages}
        if total_amount:
            json_result['totalAmount'] = total_amount
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
REWRITTEN TO MATCH GET ALL TRANSACTIONS API - CORE APP - SPRINT 16 - FNE 74/4 - BY PRAVEEN JINKA
******************************************************************************************************************************
"""
@api_view(['POST'])
def get_all_trashed_transactions(request):
    try:
        cmte_id = request.user.username
        param_string = ""
        page_num = int(request.data.get('page', 1))
        descending = request.data.get('descending', 'false')
        if not ('sortColumnName' in request.data and check_null_value(request.data.get('sortColumnName'))):
            sortcolumn = 'default'
        else:
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

        trans_query_string = """SELECT transaction_type as "transactionTypeId", transaction_type_desc as "type", transaction_id as "transactionId", name, street_1 as "street", street_2 as "street2", city, state, zip_code as "zip", transaction_date as "date", date(last_update_date) as "deletedDate", COALESCE(transaction_amount,0) as "amount", COALESCE(aggregate_amt,0) as "aggregate", purpose_description as "purposeDescription", occupation as "contributorOccupation", employer as "contributorEmployer", memo_code as "memoCode", memo_text as "memoText", itemized, transaction_type_identifier, entity_id from all_transactions_view
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
        committeeid = request.user.username
        row_count = 0
        for _action in request.data.get('actions', []):
            #report_id = _action.get('report_id', '')
            trans_id = _action.get('transaction_id', '')
            table_list = SCHEDULE_TO_TABLE_DICT.get(trans_id[:2])
            if table_list:
                for table in table_list:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("""Delete FROM public.{} where transaction_id = %s;""".format(table),[trans_id])
                            row_count += cursor.rowcount
                    except Exception as e:
                        raise Exception('delete_trashed_transactions SQl is throwing an error: ' + str(e))
                if not row_count:
                    logger.debug('Delete trashed transaction: '+str(trans_id)+' for committee: '+str(committeeid))
                    raise Exception("""The transaction ID: {1} is either already deleted or does not exist in {0} table""".format(','.join(table_list), trans_id))
            else:
                raise Exception('The transaction id {} has not been assigned to SCHEDULE_TO_TABLE_DICT.'.format(trans_id))
        json_result = {'message':'Transaction deleted successfully'}
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
# LOANS AND DEBTS SQL statements

def loans_sql(sql, value_list, error_message):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, value_list)
            return cursor.fetchone()
    except Exception as e:
        raise Exception(error_message + str(e))

def period_receipts_for_summary_table_sql(calendar_start_dt, calendar_end_dt, cmte_id, report_id ):
    """
    return line number, contribution_amount of each transaction and calendar_year sum of all contribution_amount
    """
    try:
        with connection.cursor() as cursor:
            #cursor.execute("SELECT line_number, contribution_amount FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            cursor.execute("SELECT line_number, COALESCE(contribution_amount,0), ( select COALESCE(sum(contribution_amount),0) as contribution_amount_ytd FROM public.sched_a t2 WHERE t2.memo_code IS NULL AND t2.line_number = t1.line_number AND T2.cmte_id = T1.cmte_id AND t2.contribution_date BETWEEN %s AND %s )  FROM public.sched_a t1 WHERE t1.memo_code IS NULL AND t1.cmte_id = %s AND t1.report_id = %s AND t1.delete_ind is distinct from 'Y'", [calendar_start_dt, calendar_end_dt, cmte_id, report_id])
            return cursor.fetchall()
    except Exception as e:
        raise Exception('The period_receipts_for_summary_table_sql function is throwing an error: ' + str(e))

def period_disbursements_for_summary_table_sql(calendar_start_dt, calendar_end_dt, cmte_id, report_id):
    try:
        with connection.cursor() as cursor:
            #cursor.execute("SELECT line_number, expenditure_amount FROM public.sched_b WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            cursor.execute("SELECT line_number, COALESCE(expenditure_amount,0), ( select COALESCE(sum(expenditure_amount),0) as expenditure_amount_ytd FROM public.sched_b t2 WHERE t2.memo_code IS NULL AND t2.line_number = t1.line_number AND T2.cmte_id = T1.cmte_id AND t2.expenditure_date BETWEEN %s AND %s ) FROM public.sched_b t1 WHERE t1.memo_code IS NULL AND t1.cmte_id = %s AND t1.report_id = %s AND t1.delete_ind is distinct from 'Y'", [calendar_start_dt, calendar_end_dt, cmte_id, report_id])
            return cursor.fetchall()
    except Exception as e:
        raise Exception('The period_disbursements_for_summary_table_sql function is throwing an error: ' + str(e))

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
            if data_row[0] in ['21AI', '21A']:
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

        summary_disbursement_list = [ {'line_item':'31', 'level':1, 'description':'Total Disbursements', 'amt':XXXI_amount, 'amt_ytd':XXXI_amount_ytd},
                                {'line_item':'21', 'level':2, 'description':'Operating Expenditures', 'amt':XXI_amount, 'amt_ytd':XXI_amount_ytd},
                                {'line_item':'21AI', 'level':3, 'description':'Allocated Operating Expenditures - Federal', 'amt':XXIAI_amount, 'amt_ytd':XXIAI_amount_ytd},
                                {'line_item':'21AII', 'level':3, 'description':'Allocated Operating Expenditures - Non-Federal', 'amt':XXIAII_amount, 'amt_ytd':XXIAII_amount_ytd},
                                {'line_item':'21B', 'level':3, 'description':'Other Federal Operating Expenditures', 'amt':XXIB_amount, 'amt_ytd':XXIB_amount_ytd},
                                {'line_item':'22', 'level':2, 'description':'Transfer From Affiliated Committees', 'amt':XXII_amount, 'amt_ytd':XXII_amount_ytd},
                                {'line_item':'23', 'level':2, 'description':'Contributions To Other Committees', 'amt':XXIII_amount, 'amt_ytd':XXIII_amount_ytd},
                                {'line_item':'24', 'level':2, 'description':'Independent Expenditures', 'amt':XXIV_amount, 'amt_ytd':XXIV_amount_ytd},
                                {'line_item':'25', 'level':2, 'description':'Party Coordinated Expenditures', 'amt':XXV_amount, 'amt_ytd':XXV_amount_ytd},
                                {'line_item':'27', 'level':2, 'description':'Loans Made', 'amt':XXVII_amount, 'amt_ytd':XXVII_amount_ytd},
                                {'line_item':'26', 'level':2, 'description':'Loan Repayments Made', 'amt':XXVI_amount, 'amt_ytd':XXVI_amount_ytd},
                                {'line_item':'28', 'level':2, 'description':'Total Contribution Refunds', 'amt':XXVIII_amount, 'amt_ytd':XXVIII_amount_ytd},
                                {'line_item':'28A', 'level':3, 'description':'Individual Refunds', 'amt':XXVIIIA_amount, 'amt_ytd':XXVIIIA_amount_ytd},
                                {'line_item':'28B', 'level':3, 'description':'Political Party Refunds', 'amt':XXVIIIB_amount, 'amt_ytd':XXVIIIB_amount_ytd},
                                {'line_item':'28C', 'level':3, 'description':'Other Committee Refunds', 'amt':XXVIIIC_amount, 'amt_ytd':XXVIIIC_amount_ytd},
                                {'line_item':'29', 'level':2, 'description':'Other Disbursements', 'amt':XXIX_amount, 'amt_ytd':XXIX_amount_ytd},
                                {'line_item':'30', 'level':2, 'description':'Total Federal Election Activity', 'amt':XXX_amount, 'amt_ytd':XXX_amount_ytd},
                                {'line_item':'30AI', 'level':3, 'description':'Allocated Federal Election Activity - Federal Share', 'amt':XXXAI_amount, 'amt_ytd':XXXAI_amount_ytd},
                                {'line_item':'30AII', 'level':3, 'description':'Allocated Federal Election Activity - Levin Share', 'amt':XXXAII_amount, 'amt_ytd':XXXAII_amount_ytd},
                                {'line_item':'30B', 'level':3, 'description':'Federal Election Activity - Federal Only', 'amt':XXXB_amount, 'amt_ytd':XXXB_amount_ytd},
                                {'line_item':'32', 'level':2, 'description':'Total Federal Disbursements', 'amt':XXXII_amount, 'amt_ytd':XXXII_amount_ytd},
                                ]
   
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
            if data_row[0] in ['11AI', '11A']:
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

        XIA_amount = XIA_amount + XIAI_amount + XIAII_amount
        XIA_amount_ytd = XIA_amount_ytd + XIAI_amount_ytd + XIAII_amount_ytd

        XID_amount = XIA_amount + XIB_amount + XIC_amount
        XID_amount_ytd = XIA_amount_ytd + XIB_amount_ytd + XIC_amount_ytd

        XVIII_amount = XVIIIA_amount + XVIIIB_amount
        VIII_amount_ytd = XVIIIA_amount_ytd + XVIIIB_amount_ytd

        XIX_amount =  XID_amount + XII_amount + XIII_amount + XIV_amount + XV_amount + XVI_amount + XVII_amount + XVIII_amount
        XIX_amount_ytd =  XID_amount_ytd + XII_amount_ytd + XIII_amount_ytd + XIV_amount_ytd + XV_amount_ytd + XVI_amount_ytd + XVII_amount_ytd + XVIII_amount_ytd

        XX_amount = XIX_amount - XVIII_amount
        XX_amount_ytd = XIX_amount_ytd - XVIII_amount_ytd

        summary_receipt_list = [ {'line_item':'19', 'level':1, 'description':'Total Receipts', 'amt':XIX_amount, 'amt_ytd':XIX_amount_ytd},
                                {'line_item':'11D', 'level':2, 'description':'Total Contributions', 'amt':XID_amount, 'amt_ytd':XID_amount_ytd},
                                {'line_item':'11A', 'level':3, 'description':'Total Individual Contributions', 'amt':XIA_amount, 'amt_ytd':XIA_amount_ytd},
                                {'line_item':'11AI', 'level':4, 'description':'Itemized Individual Contributions', 'amt':XIAI_amount, 'amt_ytd':XIAI_amount_ytd},
                                {'line_item':'11AII', 'level':4, 'description':'Unitemized Individual Contributions', 'amt':XIAII_amount, 'amt_ytd':XIAII_amount_ytd},
                                {'line_item':'11B', 'level':3, 'description':'Party Committee Contributions', 'amt':XIB_amount, 'amt_ytd':XIB_amount_ytd},
                                {'line_item':'11C', 'level':3, 'description':'Other Committee Contributions', 'amt':XIC_amount, 'amt_ytd':XIC_amount_ytd},
                                {'line_item':'12', 'level':2, 'description':'Transfers From Affiliated Committees', 'amt':XII_amount, 'amt_ytd':XII_amount_ytd},
                                {'line_item':'13', 'level':2, 'description':'All Loans Received', 'amt':XIII_amount,  'amt_ytd':XIII_amount_ytd},
                                {'line_item':'14', 'level':2, 'description':'Loan Repayments Received', 'amt':XIV_amount, 'amt_ytd':XIV_amount_ytd},
                                {'line_item':'15', 'level':2, 'description':'Offsets To Operating Expenditures', 'amt':XV_amount,  'amt_ytd':XV_amount_ytd},
                                {'line_item':'16', 'level':2, 'description':'Candidate Refunds', 'amt':XVI_amount, 'amt_ytd':XVI_amount_ytd},
                                {'line_item':'17', 'level':2, 'description':'Other Receipts', 'amt':XVII_amount, 'amt_ytd':XVII_amount_ytd},
                                {'line_item':'18', 'level':2, 'description':'Total Transfers', 'amt':XVIII_amount, 'amt_ytd':XVIII_amount_ytd},
                                {'line_item':'18A', 'level':3, 'description':'Non-federal Transfers', 'amt':XVIIIA_amount, 'amt_ytd':XVIIIA_amount_ytd},
                                {'line_item':'18B', 'level':3, 'description':'Levin Funds', 'amt':XVIIIB_amount, 'amt_ytd':XVIIIB_amount_ytd},
                                {'line_item':'20', 'level':2, 'description':'Total Federal Receipts', 'amt':XX_amount, 'amt_ytd':XX_amount_ytd},
                                ]
        return summary_receipt_list
    except Exception as e:
        raise Exception('The summary_receipts API is throwing the error: ' + str(e))

def load_loan_debt_summary(period_args):
    """
    query laon and debt sum for current report and ytd
    TODO: still need to verify the business logic is correct
    1. need to check against get_loan_debt_summary api
    2. need to verify the transaction types in the database
    """
    start_dt = period_args[0]
    end_dt = period_args[1]
    cmte_id = period_args[2]
    report_id = period_args[3]
    loan_debt_dic =  {  
        'DEBTS/LOANS OWED TO COMMITTEE': 0,
        'DEBTS/LOANS OWED BY COMMITTEE': 0,
        'DEBTS/LOANS OWED TO COMMITTEE YTD': 0,
        'DEBTS/LOANS OWED BY COMMITTEE YTD': 0
    }

    _sql_rep = """
        SELECT transaction_type_identifier, 
        SUM(loan_balance) 
        FROM   sched_c 
        WHERE  cmte_id = %s 
            AND report_id = %s 
            AND transaction_type_identifier IN ( 
                'LOANS_OWED_TO_CMTE', 'LOANS_OWED_BY_CMTE' ) 
        GROUP  BY transaction_type_identifier 
        UNION 
        SELECT transaction_type_identifier, 
            SUM(balance_at_close) 
        FROM   sched_d 
        WHERE  cmte_id = %s 
            AND report_id = %s 
            AND transaction_type_identifier IN ( 
                'DEBT_TO_VENDER') 
        GROUP  BY transaction_type_identifier 
    """
    _sql_ytd = """
        SELECT transaction_type_identifier AS ytd, 
            Sum(loan_balance) 
        FROM   sched_c 
        WHERE  cmte_id = %s 
            AND loan_incurred_date BETWEEN %s AND %s 
            AND transaction_type_identifier IN ( 
                'LOANS_OWED_TO_CMTE', 'LOANS_OWED_BY_CMTE' ) 
        GROUP  BY transaction_type_identifier 
        UNION 
        SELECT transaction_type_identifier AS ytd, 
            Sum(balance_at_close) 
        FROM   sched_d 
        WHERE  cmte_id = %s
            AND create_date BETWEEN %s AND %s
            AND transaction_type_identifier IN ( 
                'DEBT_TO_VENDER') 
        GROUP  BY transaction_type_identifier 
    """
    try:
        with connection.cursor() as cursor:
            #cursor.execute("SELECT line_number, contribution_amount FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            cursor.execute(_sql_rep, [cmte_id, report_id]*2)
            for row in cursor.fetchall():
                if row[0].endswith('TO_CMTE'):
                    loan_debt_dic['DEBTS/LOANS OWED TO COMMITTEE'] += float(row[1])
                elif row[0].endswith('BY_CMTE'):
                    loan_debt_dic['DEBTS/LOANS OWED BY COMMITTEE'] += float(row[1])
                else:
                    pass
            cursor.execute(_sql_ytd, [cmte_id, start_dt, end_dt]*2)
            for row in cursor.fetchall():
                if row[0].endswith('TO_CMTE'):
                    loan_debt_dic['DEBTS/LOANS OWED TO COMMITTEE YTD'] += float(row[1])
                elif row[0].endswith('BY_CMTE'):
                    loan_debt_dic['DEBTS/LOANS OWED BY COMMITTEE YTD'] += float(row[1])
                else:
                    pass
            return loan_debt_dic
    except Exception as e:
        raise Exception('The get_loan_debt_summary function is throwing an error: ' + str(e))

@api_view(['GET'])
def get_summary_table(request):
    logger.debug('get_summary_table with request:{}'.format(request.query_params))
    try:
        cmte_id = request.user.username

        if not('report_id' in request.query_params and check_null_value(request.query_params.get('report_id'))):
            raise Exception ('Missing Input: report_id is mandatory')

        if not('calendar_year' in request.query_params and check_null_value(request.query_params.get('calendar_year'))):
            raise Exception ('Missing Input: calendar_year is mandatory')

        report_id = check_report_id(request.query_params.get('report_id'))
        calendar_year = check_calendar_year(request.query_params.get('calendar_year'))
        logger.debug('query_params: report_id {}, calendar_year {}'.format(report_id, calendar_year))

        period_args = [datetime.date(int(calendar_year), 1, 1), datetime.date(int(calendar_year), 12, 31),  cmte_id, report_id]
        logger.debug('period_args:{}'.format(period_args))

        logger.debug('load receipts and dsibursements...')
        period_receipt = summary_receipts_for_sumamry_table(period_args)
        period_disbursement = summary_disbursements_for_sumamry_table(period_args)
        
        '''
        calendar_args = [cmte_id, date(int(calendar_year), 1, 1), date(int(calendar_year), 12, 31)]
        calendar_receipt = summary_receipts(calendar_args)
        calendar_disbursement = summary_disbursements(calendar_args)
        '''
        logger.debug('load cash on hand...')
        coh_bop_ytd = prev_cash_on_hand_cop(report_id, cmte_id, True)
        coh_bop = prev_cash_on_hand_cop(report_id, cmte_id, False)
        coh_cop = COH_cop(coh_bop, period_receipt, period_disbursement)

        cash_summary = {'COH AS OF JANUARY 1': coh_bop_ytd,
                        'BEGINNING CASH ON HAND': coh_bop,
                        'ENDING CASH ON HAND': coh_cop}
        logger.debug('cash summary:{}'.format(cash_summary))

        loan_and_debts = load_loan_debt_summary(period_args)
        logger.debug('adding loan and debts:{}'.format(loan_and_debts))
        cash_summary.update(loan_and_debts)
        logger.debug('adding loan and debts:{}'.format(cash_summary))

        forms_obj = {'Total Raised': {'period_receipts': period_receipt},
                    'Total Spent': {'period_disbursements': period_disbursement},
                    'Cash summary': cash_summary}
        logger.debug('summary result:{}'.format(forms_obj))
                        
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
            cursor.execute("SELECT COALESCE(t1.coh_cop, 0) from public.form_3x t1 where t1.cmte_id = %s AND t1.cvg_end_dt = %s AND t1.delete_ind is distinct from 'Y' AND (SELECT t2.delete_ind from public.reports t2 where t2.report_id = t1.report_id) is distinct from 'Y'", [cmte_id, prev_cvg_end_dt])
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

def loansanddebts(report_id, cmte_id):
    try:
        loans_sc_sql = "SELECT COALESCE(SUM(loan_balance), 0.0) FROM public.sched_c WHERE memo_code IS NULL AND cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'"
        error_message_sc = "The loans_sql function is throwing an error for sched_c table : "

        loans_sc1_sql = "SELECT COALESCE(SUM(total_outstanding_balance), 0.0) FROM public.sched_c1 WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'"
        error_message_sc1 = "The loans_sql function is throwing an error for sched_c1 table : "

        loans_sd_sql = "SELECT COALESCE(SUM(payment_amount), 0.0) FROM public.sched_d WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'"
        error_message_sd = "The loans_sql function is throwing an error for sched_d table : "

        value_list = [cmte_id, report_id]
        output = loans_sql(loans_sc_sql, value_list, error_message_sc)[0] + loans_sql(loans_sc1_sql, value_list, error_message_sc1)[0] + loans_sql(loans_sd_sql, value_list, error_message_sd)[0]
        return output
    except Exception as e:
        raise Exception('The loansanddebts function is throwing an error' + str(e))

def getthirdnavamounts(cmte_id, report_id):
    try:
        amounts = []
        _values = [cmte_id, report_id]
        table_list = [['11A','11AI','11AII','11B','11C','12','15','16','17','18A','18B'], 
                      ['21AI','21AII','21B','22','28A','28B','28C','29']]
        for table in table_list:
            _sql = """
                SELECT COALESCE(SUM(transaction_amount),0.0) FROM public.all_transactions_view WHERE line_number in ('{}')
                AND memo_code IS DISTINCT FROM 'X' AND delete_ind IS DISTINCT FROM 'Y' AND cmte_id = %s AND report_id = %s
                """.format("', '".join(table))
            with connection.cursor() as cursor:
                cursor.execute(_sql, _values)
                print(cursor.query)
                amounts.append(cursor.fetchone()[0])
        loans_table = ['sched_c', 'sched_d']
        l_sql = """
            SELECT COALESCE(SUM(transaction_amount),0.0) FROM public.all_transactions_view WHERE transaction_table in ('{}')
            AND memo_code IS DISTINCT FROM 'X' AND delete_ind IS DISTINCT FROM 'Y' AND cmte_id = %s AND report_id = %s
            """.format("', '".join(loans_table))
        with connection.cursor() as cursor:
            cursor.execute(l_sql, _values)
            print(cursor.query)
            amounts.append(cursor.fetchone()[0])
        return amounts[0], amounts[1], amounts[2]
    except Exception as e:
        raise Exception('The getthirdnavamounts function is throwing an error' + str(e))

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

        # period_args = [datetime.date(2019, 1, 1), datetime.date(2019, 12, 31), cmte_id, report_id]
        # period_receipt = summary_receipts_for_sumamry_table(period_args)
        # period_disbursement = summary_disbursements_for_sumamry_table(period_args)

        period_receipt, period_disbursement, loans_and_debts = getthirdnavamounts(cmte_id, report_id)
        loans_and_debts = loansanddebts(report_id, cmte_id)

        coh_bop = prev_cash_on_hand_cop(report_id, cmte_id, False)
        # coh_cop = COH_cop(coh_bop, period_receipt, period_disbursement)
        coh_cop = coh_bop + period_receipt - period_disbursement + loans_and_debts

        # forms_obj = { 'Receipts': period_receipt[0].get('amt'),
        #                 'Disbursements': period_disbursement[0].get('amt'),
        #                 'Loans/Debts': loans_and_debts,
        #                 'Others': 0,
        #                 'COH': coh_cop}

        forms_obj = { 'Receipts': period_receipt,
                        'Disbursements': period_disbursement,
                        'Loans/Debts': loans_and_debts,
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
                    
                    query_string = """SELECT cmte_id as cmteId, report_id as reportId, form_type as formType, '' as electionCode, 
                                        report_type as reportType,  rt.rpt_type_desc as reportTypeDescription, 
                                        rt.regular_special_report_ind as regularSpecialReportInd, '' as stateOfElection, 
                                        '' as electionDate, cvg_start_date as cvgStartDate, cvg_end_date as cvgEndDate, 
                                        due_date as dueDate, amend_ind as amend_Indicator, 0 as coh_bop,
                                         (SELECT CASE WHEN due_date IS NOT NULL THEN to_char(due_date, 'YYYY-MM-DD')::date - to_char(now(), 'YYYY-MM-DD')::date ELSE 0 END ) AS daysUntilDue, 
                                         email_1 as email1, email_2 as email2, additional_email_1 as additionalEmail1, 
                                         additional_email_2 as additionalEmail2, 
                                         (SELECT CASE WHEN due_date IS NOT NULL AND due_date < now() THEN True ELSE False END ) AS overdue
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
        #print("json_builder_resp = ", json_builder_resp)
        #commented by Mahendra 10052019

        bucket_name = 'dev-efile-repo'
        client = boto3.client('s3')
        transfer = S3Transfer(client)
        #s3.download_file(bucket_name , s3_file_path, save_as)
        transfer.download_file(bucket_name , json_builder_resp, json_builder_resp)
        #commented by Mahendra 10052019
        #with open(save_as) as f:
            #print(json_builder_resp.read())

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
def contactsTable(request):
    try:
        
        if request.method == 'POST':
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

            keys = ['id', 'entity_type', 'name', 'street1', 'street2', 'city', 'state', 'zip', 'occupation', 'employer', 'candOfficeState', 'candOfficeDistrict', 'candCmteId', 'phone_number','deleteddate']
            search_keys = ['id', 'entity_type', 'name', 'street1', 'street2', 'city', 'state', 'zip', 'occupation', 'employer', 'candOfficeState', 'candOfficeDistrict', 'candCmteId', 'phone_number','deleteddate']
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
            
            
            trans_query_string = """SELECT id, entity_type, name, street1, street2, city, state, zip, occupation, employer, candOffice, candOfficeState, candOfficeDistrict, candCmteId, phone_number, deleteddate, active_transactions_cnt from all_contacts_view
                                        where (deletedFlag <> 'Y' OR deletedFlag is NULL) AND cmte_id='""" + cmte_id + """' """ + param_string 
            #print("contacts trans_query_string: ",trans_query_string)
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
        return Response("The contactsTable API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_loan_debt_summary(request):
    """
    get loan and debt aggreagation data 'to the committee' and 'by the committee'（FNE-1291）
    Business Logic:
    Loans/Debts owed to committees : (SC + SC1 with line number 9 ) + (SD with line number 9 )
    Loans/Debts owed by committees : (SC + SC1 with line number 10 ) + (SD with line number 10 )

    api query parameters: cmet_id + report_id
    """
    try:
        cmte_id = request.user.username
        report_id = check_report_id(request.data.get('report_id'))
        _sql = """
        SELECT Sum(t._sum) 
        FROM  ( 
            ( 
                    SELECT SUM(loan_balance) AS _sum 
                    FROM   public.sched_c 
                    WHERE  cmte_id = %(cmte_id)s 
                    AND    report_id = %(report_id)s 
                    AND    line_number= %(line_num)s) 
        UNION 
            ( 
                    SELECT SUM(loan_amount) AS _sum 
                    FROM   public.sched_c1 
                    WHERE  cmte_id = %(cmte_id)s 
                    AND    report_id = %(report_id)s 
                    AND    line_number= %(line_num)s) 
        UNION 
            ( 
                    SELECT SUM(payment_amount) AS _sum 
                    FROM   public.sched_d 
                    WHERE  cmte_id = %(cmte_id)s 
                    AND    report_id = %(report_id)s
                    AND    line_num= %(line_num)s)) t;
        """
        with connection.cursor() as cursor:
            cursor.execute(_sql, {'cmte_id':cmte_id, 'report_id': report_id, 'line_num': '9'})
            to_committee_sum = list(cursor.fetchone())[0]
            cursor.execute(_sql, {'cmte_id':cmte_id, 'report_id': report_id, 'line_num': '10'})
            by_committee_sum = list(cursor.fetchone())[0]
            json_result = {"to_committee_sum": to_committee_sum, "by_committee_sum": by_committee_sum}
            return Response(json_result, status.HTTP_200_OK)

    except Exception as e:
        return Response("The get_loan_debt_summary api is throwing an error: " + str(e), 
                        status=status.HTTP_400_BAD_REQUEST)

"""
*****************************************************************************************************************************
END - Contacts API - CORE APP
******************************************************************************************************************************
"""
"""
**********************************************************************************************************************************************
Creating API FOR UPDATING F-3X SUMMARY TABLE - CORE APP - SPRINT 18 - FNE 1323 - BY  Yeswanth Kumar Tella
**********************************************************************************************************************************************
"""
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


def get_line_sum_value(line_number, formula, sched_a_line_sum_dict, cmte_id, report_id):
    val = 0
    if line_number == '6b':
        val = prev_cash_on_hand_cop(report_id, cmte_id, False)
        # print('report_id: '+ report_id + '; cmte_id: ' + cmte_id)
        # print('rep: '+str(val))
        return val
    if line_number == '6a':
        val = prev_cash_on_hand_cop(report_id, cmte_id, True)
        # print('report_id: '+ report_id + '; cmte_id: ' + cmte_id)
        # print('year: '+ str(val))
        return val
    if formula == "":
        val += sched_a_line_sum_dict.get(line_number, 0) if sched_a_line_sum_dict.get(line_number, 0) else 0
        return val
    if formula == "0":
        return val
    formula_split = formula.replace(' ', '').split('+')
    if len(formula_split) == 1:
        if '-' in formula_split[0]:
            cl_n = formula_split[0].replace(' ', '')
            val += get_line_sum_value(cl_n.split('-')[0], "", sched_a_line_sum_dict, cmte_id,
                                          report_id) - get_line_sum_value(cl_n.split('-')[1], "", sched_a_line_sum_dict, cmte_id,
                                          report_id)
        else:
            line_number = formula_split[0]
            val += sched_a_line_sum_dict.get(line_number, 0) if sched_a_line_sum_dict.get(line_number, 0) else 0
    else:
        for cl_n in formula_split:
            if '-' in cl_n:
                val += get_line_sum_value(cl_n.split('-')[0], "", sched_a_line_sum_dict, cmte_id,
                                          report_id) - get_line_sum_value(cl_n.split('-')[1], "", sched_a_line_sum_dict, cmte_id,
                                          report_id)
            else:
                val += get_line_sum_value(cl_n, "", sched_a_line_sum_dict, cmte_id, report_id)
    return val



@api_view(['POST'])
def prepare_json_builders_data(request):
    try:
        #print("request.data: ", request.data)
        #commented by Mahendra 10052019
        cmte_id = request.user.username
        param_string = ""
        report_id = request.data.get('report_id')
        sched_a_line_sum = {}
        sched_b_line_sum = {}

        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)

        #cdate = date.today()
        from_date = date(cvg_start_date.year, 1,1)
       
        to_date = date(cvg_end_date.year, 12, 31)
       

        #schedule_a_b_line_sum_dict = {}
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT line_number, sum(contribution_amount) from public.sched_a 
                where cmte_id = '%s' AND report_id = '%s' group by line_number;""" %(cmte_id, report_id))
            #print(cursor.query)
            #commented by Mahendra 10052019
            sched_a_line_sum_result = cursor.fetchall()
            sched_a_line_sum = {str(i[0].lower()): i[1] if i[1] else 0 for i in sched_a_line_sum_result}
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT line_number, sum(expenditure_amount) from public.sched_b 
                where cmte_id = '%s' AND report_id = '%s' group by line_number;""" %(cmte_id, report_id))
            #print(cursor.query)
            #commented by Mahendra 10052019
            sched_b_line_sum_result = cursor.fetchall()
            sched_b_line_sum = {str(i[0].lower()): i[1] if i[1] else 0 for i in sched_b_line_sum_result}
        
        #sched_a_line_sum.update(sched_b_line_sum)
        #print(sched_a_line_sum, "sched_a_line_sum")
        #commented by Mahendra 10052019
        #print(sched_b_line_sum, "sched_b_line_sum")
        #commented by Mahendra 10052019
        
        ##schedule_a_b_line_sum_dict.update(sched_a_line_sum)
        ##schedule_a_b_line_sum_dict.update(sched_b_line_sum)
        schedule_a_b_line_sum_dict = {}
        schedule_a_b_line_sum_dict.update(sched_a_line_sum)
        schedule_a_b_line_sum_dict.update(sched_b_line_sum)

        col_a_line_sum = {}
        col_b_line_sum = {}


        with connection.cursor() as cursor:
            cursor.execute(""" 
                SELECT line_number, sum(contribution_amount) from public.sched_a 
                where cmte_id = %s AND contribution_date >= %s AND contribution_date <= %s AND delete_ind is distinct from 'Y' group by line_number;""", [cmte_id, from_date, to_date])
            #print(cursor.query)     
            #commented by Mahendra 10052019
            col_a_line_sum_result = cursor.fetchall()
            col_a_line_sum = {str(i[0].lower()): i[1] if i[1] else 0 for i in col_a_line_sum_result}
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT line_number, sum(expenditure_amount) from public.sched_b 
                where cmte_id = %s AND expenditure_date >= %s AND expenditure_date <= %s AND delete_ind is distinct from 'Y' group by line_number;""", [cmte_id, from_date, to_date])
            #print(cursor.query)
            #commented by Mahendra 10052019
            col_b_line_sum_result = cursor.fetchall()
            col_b_line_sum = {str(i[0].lower()): i[1] if i[1] else 0 for i in col_b_line_sum_result}


        col_line_sum_dict = {}
        col_line_sum_dict.update(col_a_line_sum)
        col_line_sum_dict.update(col_b_line_sum)

        #print(col_a_line_sum, "col_a_line_sum")
        #commented by Mahendra 10052019
        #print(col_b_line_sum, "col_b_line_sum")
        #commented by Mahendra 10052019
        


        col_a = [('9', '0'),
                 ('10', '0'), ('11ai', ''), ('11aii', ''), ('11aiii', '11ai + 11aii'), ('11b', ''), ('11c', ''),
                 ('11d', '11aiii + 11b + 11c'), ('12', ''), ('13', ''), ('14', ''), ('15', ''), ('16', ''), ('17', ''),
                 ('18a', '0'), ('18b', '0'), ('18c', '18a+18b'), ('19', '11d+12+13+14+15+16+17+18c'),
                 ('20', '19 - 18c'),
                 ('21ai', '0'), ('21aii', '0'), ('21b', ''), ('21c', '21ai + 21aii + 21b'), ('22', ''), ('23', ''),
                 ('24', ''),
                 ('25', '0'), ('26', ''), ('27', ''), ('28a', ''), ('28b', ''), ('28c', ''), ('28d', '28a + 28b + 28c'),
                 ('29', ''),
                 ('30ai', '0'), ('30aii', '0'), ('30b', ''), ('30c', '30ai + 30aii + 30b'),
                 ('31', '21c + 22 - 27 + 28d + 29'),
                 ('32', '31 - 21aii + 30aii'), ('33', '11d'), ('34', '28d'),
                 ('35', '11d - 28d'), ('36', '21ai + 21b'), ('37', '15'), ('38', '36 - 37'), ('6a', ''),
                 ('6b', ''), ('6c', '19'), ('6d', '6b + 6c'), ('7', '31'), ('8', '6d - 7')]

        col_a_dict_original = OrderedDict()
        for i in col_a:
            col_a_dict_original[i[0]] = i[1]
        final_col_a_dict = {}
        for line_number in col_a_dict_original:
            final_col_a_dict[line_number] = get_line_sum_value(line_number, col_a_dict_original[line_number],
                                                               schedule_a_b_line_sum_dict, cmte_id, report_id)
            schedule_a_b_line_sum_dict[line_number] = final_col_a_dict[line_number]

        #print(final_col_a_dict, "col_a_dict")
        #commented by Mahendra 10052019

        col_b = [
            ('11ai', ''), ('11aii', ''), ('11aiii', '11ai + 11aii'), ('11b', ''), ('11c', ''),
            ('11d', '11aiii + 11b + 11c'), ('12', ''), ('13', ''), ('14', ''), ('15', ''), ('16', ''), ('17', ''),
            ('18a', '0'), ('18b', '0'), ('18c', '18a+18b'), ('19', '11d+12+13+14+15+16+17+18c'), ('20', '19 - 18c'),
            ('21ai', '0'), ('21aii', '0'), ('21b', ''), ('21c', '21ai + 21aii + 21b'), ('22', ''), ('23', ''),
            ('24', ''),
            ('25', '0'), ('26', ''), ('27', ''), ('28a', ''), ('28b', ''), ('28c', ''), ('28d', '28a + 28b + 28c'),
            ('29', ''),
            ('30ai', '0'), ('30aii', '0'), ('30b', ''), ('30c', '30ai + 30aii + 30b'),
            ('31', '21c + 22 - 27 + 28d + 29'),
            ('32', '31 - 21aii + 30aii'), ('33', '11d'), ('34', '28d'),
            ('35', '11d - 28d'), ('36', '21ai + 21b'), ('37', '15'), ('38', '36 - 37'), ('6a', ''),
            ('6b', ''),
            ('6c', '19'), ('6d', '6a + 6c'),
            ('7', '31'), ('8', '6d - 7')]

        col_b_dict_original = OrderedDict()
        for i in col_b:
            col_b_dict_original[i[0]] = i[1]
        final_col_b_dict = {}
        for line_number in col_b_dict_original:
            final_col_b_dict[line_number] = get_line_sum_value(line_number, col_b_dict_original[line_number],
                                                               col_line_sum_dict,
                                                               cmte_id, report_id)
            col_line_sum_dict[line_number] = final_col_b_dict[line_number]
        #print(final_col_b_dict, "col_b_dict")
        #commented by Mahendra 10052019

        for i in final_col_a_dict:
            a_val = final_col_a_dict[i]
            b_val = final_col_b_dict.get(i)
            a_formula = col_a_dict_original.get(i, "")
            b_formula = col_b_dict_original.get(i, "")
            if a_formula:
                a_formula = a_formula.replace(" ", "")
            if b_formula:
                b_formula = b_formula.replace(" ", "")

            # if a_formula == b_formula and a_val != b_val:
            #     try:
            #         correc_val = a_val if a_val > b_val else b_val
            #     except Exception as e:
            #         print("Exception--- same formula and values changes", a_formula, b_formula, e)
            #         correc_val = 0
            #     final_col_b_dict[i] = correc_val
            #     final_col_a_dict[i] = correc_val
            final_col_b_dict[i] = b_val
            final_col_a_dict[i] = a_val

        #commented by Mahendra 10052019
        #print("---------------------------------")
        #print("Final AAAA", final_col_a_dict)
        #print("---------------------------------")
        #print("Final B", final_col_b_dict)


        update_col_a_dict = {'6b': 'coh_bop', '6c': 'ttl_receipts_sum_page_per', '6d': 'subttl_sum_page_per',
                             '7': 'ttl_disb_sum_page_per',
                             '8': 'coh_cop', '9': 'debts_owed_to_cmte', '10': 'debts_owed_by_cmte',
                             '11ai': 'indv_item_contb_per',
                             '11aii': 'indv_unitem_contb_per', '11aiii': 'ttl_indv_contb',
                             '11b': 'pol_pty_cmte_contb_per_i',
                             '11c': 'other_pol_cmte_contb_per_i', '11d': 'ttl_contb_col_ttl_per',
                             '12': 'tranf_from_affiliated_pty_per',
                             '13': 'all_loans_received_per', '14': 'loan_repymts_received_per',
                             '15': 'offsets_to_op_exp_per_i',
                             '16': 'fed_cand_contb_ref_per', '17': 'other_fed_receipts_per',
                             '18a': 'tranf_from_nonfed_acct_per',
                             '18b': 'tranf_from_nonfed_levin_per', '18c': 'ttl_nonfed_tranf_per',
                             '19': 'ttl_receipts_per',
                             '20': 'ttl_fed_receipts_per', '21ai': 'shared_fed_op_exp_per',
                             '21aii': 'shared_nonfed_op_exp_per',
                             '21b': 'other_fed_op_exp_per', '21c': 'ttl_op_exp_per',
                             '22': 'tranf_to_affliliated_cmte_per',
                             '23': 'fed_cand_cmte_contb_per', '24': 'indt_exp_per', '25': 'coord_exp_by_pty_cmte_per',
                             '26': 'loan_repymts_made_per',
                             '27': 'loans_made_per', '28a': 'indv_contb_ref_per', '28b': 'pol_pty_cmte_contb_per_ii',
                             '28c': 'other_pol_cmte_contb_per_ii',
                             '28d': 'ttl_contb_ref_per_i', '29': 'other_disb_per',
                             '30ai': 'shared_fed_actvy_fed_shr_per',
                             '30aii': 'shared_fed_actvy_nonfed_per', '30b': 'non_alloc_fed_elect_actvy_per',
                             '30c': 'ttl_fed_elect_actvy_per',
                             '31': 'ttl_disb_per', '32': 'ttl_fed_disb_per', '33': 'ttl_contb_per',
                             '34': 'ttl_contb_ref_per_ii', '35': 'net_contb_per',
                             '36': 'ttl_fed_op_exp_per', '37': 'offsets_to_op_exp_per_ii', '38': 'net_op_exp_per'}

        update_col_b_dict = {'6a': 'coh_begin_calendar_yr', '6c': 'ttl_receipts_sum_page_ytd', '6d': 'subttl_sum_ytd',
                             '7': 'ttl_disb_sum_page_ytd',
                             '8': 'coh_coy', '11ai': 'indv_item_contb_ytd', '11aii': 'indv_unitem_contb_ytd',
                             '11aiii': 'ttl_indv_contb_ytd',
                             '11b': 'pol_pty_cmte_contb_ytd_i', '11c': 'other_pol_cmte_contb_ytd_i',
                             '11d': 'ttl_contb_col_ttl_ytd',
                             '12': 'tranf_from_affiliated_pty_ytd', '13': 'all_loans_received_ytd',
                             '14': 'loan_repymts_received_ytd',
                             '15': 'offsets_to_op_exp_ytd_i', '16': 'fed_cand_cmte_contb_ytd',
                             '17': 'other_fed_receipts_ytd',
                             '18a': 'tranf_from_nonfed_acct_ytd', '18b': 'tranf_from_nonfed_levin_ytd',
                             '18c': 'ttl_nonfed_tranf_ytd',
                             '19': 'ttl_receipts_ytd', '20': 'ttl_fed_receipts_ytd', '21ai': 'shared_fed_op_exp_ytd',
                             '21aii': 'shared_nonfed_op_exp_ytd',
                             '21b': 'other_fed_op_exp_ytd', '21c': 'ttl_op_exp_ytd',
                             '22': 'tranf_to_affilitated_cmte_ytd', '23': 'fed_cand_cmte_contb_ref_ytd',
                             '24_independentExpenditures': 'indt_exp_ytd', '25': 'coord_exp_by_pty_cmte_ytd',
                             '26': 'loan_repymts_made_ytd', '27': 'loans_made_ytd',
                             '28a': 'indv_contb_ref_ytd', '28b': 'pol_pty_cmte_contb_ytd_ii',
                             '28c': 'other_pol_cmte_contb_ytd_ii', '28d': 'ttl_contb_ref_ytd_i',
                             '29': 'other_disb_ytd', '30ai': 'shared_fed_actvy_fed_shr_ytd',
                             '30aii': 'shared_fed_actvy_nonfed_ytd',
                             '30b': 'non_alloc_fed_elect_actvy_ytd', '30c': 'ttl_fed_elect_actvy_ytd',
                             '31': 'ttl_disb_ytd',
                             '32': 'ttl_fed_disb_ytd', '33': 'ttl_contb_ytd', '34': 'ttl_contb_ref_ytd_ii',
                             '35': 'net_contb_ytd',
                             '36': 'ttl_fed_op_exp_ytd', '37': 'offsets_to_op_exp_ytd_ii', '38': 'net_op_exp_ytd'}

        update_str = ""
        for i in update_col_a_dict:
            sum_value = final_col_a_dict.get(i, None)
            if sum_value in ["",None, "None"]:
                sum_value = 0
            update_str += "%s=%s," % (update_col_a_dict[i], str(sum_value))
        for i in update_col_b_dict:
            sum_value = final_col_b_dict.get(i, None)
            if sum_value in ["",None, "None"]:
                sum_value = 0
            update_str += "%s=%s," % (update_col_b_dict[i], str(sum_value))

        update_str = update_str[:-1]
        # print("-------------------------")
        #print(update_str, "update_str")
        #commented by Mahendra 10052019
        #return Response({'Response':'Success'}, status=status_value)
        
        with connection.cursor() as cursor:
            #query_string = """SELECT * FROM public.form_3x WHERE cmte_id = %s AND report_id = %s"""
            #cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id, report_id])
            update_query = """update public.form_3x set %s WHERE cmte_id = '%s' AND report_id = '%s';"""%(update_str, cmte_id, report_id)
            cursor.execute(update_query)
            #print("Updated on Database ---- yoyooooo")
        return Response({'Response':'Success'}, status= status.HTTP_200_OK)
    except Exception as e:
        return Response({'Response':'Failed', 'Message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
"""
********************************************************************************************************************************
GET CONTACT DYNAMIC FORM FIELDS API- CORE APP - SPRINT 18 - FNE 503 - BY MAHENDRA MARATHE
********************************************************************************************************************************
"""
@api_view(['GET'])
def get_contacts_dynamic_forms_fields(request):

    try:

        with open(os.path.dirname(__file__) + "/contacts_fields.json", encoding='utf-8', errors='ignore') as contacts_json_file:
            data_obj = json.load(contacts_json_file)
                
        if not bool(data_obj):
            return Response("Contacts dynamice fields json file is missing...!", status=status.HTTP_400_BAD_REQUEST)                              
        
        return JsonResponse(data_obj, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return Response("The get_contacts_dynamic_forms_fields API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

# """


# ****************************************************************************************************************************************************************
# TRANSACTION CATOGIRES SCREEN SEARCH BY TYPE FIELD API- CORE APP - SPRINT 18 - FNE 1276 - BY YESWANTH KUMAR TELLA
# *****************************************************************************************************************************************************************
# """
# @api_view(['GET', 'POST'])
# def get_filler_transaction_type(request):
#     try:
#         # print("request.data: ", request.data)
#         #cmte_id = request.user.username
#         param_string = ""
        
#         search_string = request.data.get('search')
#         # import ipdb;ipdb.set_trace()
#         report_id = request.data.get('reportid')
#         search_keys = ['form_type','sched_type', 'line_num', 'tran_code', 
#             'tran_identifier', 'tran_desc']
#         if search_string:
#             for key in search_keys:
#                 if not param_string:
#                     param_string = param_string + " AND (CAST(" + key + " as CHAR(100)) ILIKE '%" + str(search_string) +"%'"
#                 else:
#                     param_string = param_string + " OR CAST(" + key + " as CHAR(100)) ILIKE '%" + str(search_string) +"%'"
#             param_string = param_string + " )"
#         query_string = """SELECT * FROM public.ref_transaction_types where cmte_id = %s """ + param_string + """ AND delete_ind is distinct from 'Y'"""
#                            # + """ ORDER BY """ + order_string
#         # print(query_string)
#         forms_obj = None
#         with connection.cursor() as cursor:
#             cursor.execute(query_string)
#             for row in cursor.fetchall():
#                 data_row = list(row)
#                 forms_obj=data_row[0]
#                 if forms_obj is None:
#                     forms_obj =[]
#                     status_value = status.HTTP_200_OK
        
        
#         #import ipdb; ipdb.set_trace()
#         json_result = {'transaction_type': list(forms_obj)}
#         # json_result = { 'transactions': forms_obj, 'totalAmount': sum_trans, 'totalTransactionCount': count}
#         return Response(json_result, status=status_value)
#     except Exception as e:
#         return Response("The get_filer_transaction_type API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST) 

@api_view(['GET'])
def get_entityTypes(request):
    try:
        cmte_id = request.user.username
      
        data = """{
                    "data":  [
                        {
                            "type_code": "CAN",
                            "type_desc": "Candidate"
                        },
                        {
                            "type_code": "COM",
                            "type_desc": "Committee"
                        },
                      
                        {
                            "type_code": "IND",
                            "type_desc": "Individual"
                        },
                        {
                            "type_code": "ORG",
                            "type_desc": "Organization"
                        }]
                  }
                """
        forms_obj = json.loads(data)
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_entityTypes API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
 
def post_sql_contact(data):
    """persist one contact item."""
    try:
        entity_id = get_next_entity_id(data['entity_type'])  
        data['entity_id'] = entity_id
        with connection.cursor() as cursor:
            # Insert data into entity table
            cursor.execute("""INSERT INTO public.entity (cmte_id, entity_id, entity_type, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, cand_office, cand_office_state, cand_office_district, ref_cand_cmte_id, phone_number)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", 
                                [ data['cmte_id'], data['entity_id'], data['entity_type'], data['entity_name'], data['first_name'], data['last_name'], data['middle_name'], data['preffix'], data['suffix'], data['street_1'], data['street_2'], data['city'], data['state'], data['zip_code'], data['occupation'], data['employer'], data['cand_office'], data['cand_office_state'], data['cand_office_district'], data['ref_cand_cmte_id'], data['phone_number'] ])

    except Exception:
        raise

def post_contact(datum):
    """save contact."""
    #post_sql_contact(datum.get('cmte_id'), datum.get('entity_type'), datum.get('entity_name'), datum.get('first_name'), datum.get('last_name'), datum.get('middle_name'), datum.get('preffix'), datum.get('suffix'), datum.get('street_1'), datum.get('street_2'), datum.get('city'), datum.get('state'), datum.get('zip_code'), datum.get('occupation'), datum.get('employer'), datum.get('officeSought'), datum.get('officeState'), datum.get('district'), datum.get('ref_cand_cmte_id'))
    post_sql_contact(datum)

def contact_sql_dict(data):
    """
    filter data, validate fields and build entity item dic
    """
    try:
        datum = {
         # 'cmte_id' : data.get('cmte_id'), 
          'entity_type'  : is_null(data.get('entity_type')), 
          'entity_name'  : is_null(data.get('entity_name')), 
          'first_name'  : is_null(data.get('first_name')), 
          'last_name'  : is_null(data.get('last_name')), 
          'middle_name' : is_null(data.get('middle_name')), 
          'preffix'  : is_null(data.get('prefix')), 
          'suffix' : is_null(data.get('suffix')), 
          'street_1'  : is_null(data.get('street_1')), 
          'street_2'  : is_null(data.get('street_2')), 
          'city'  : is_null(data.get('city')),  
          'state' : is_null(data.get('state')), 
          'zip_code' : is_null(data.get('zip_code')), 
          'occupation'  : is_null(data.get('occupation')), 
          'employer' : is_null(data.get('employer')), 
          'cand_office'  : is_null(data.get('officeSought')), 
          'cand_office_state'  : is_null(data.get('officeState')), 
          'cand_office_district'  : is_null(data.get('district')), 
          'ref_cand_cmte_id'  : is_null(data.get('ref_cand_cmte_id')), 
          'phone_number'  : is_null(data.get('phone_number'),'phone_number'), 
        }

        return datum
    except:
        raise


def contact_entity_dict(data):
    """
    filter data, validate fields and build entity item dic
    """
    try:
        datum = {
         # 'cmte_id' : data.get('cmte_id'),
          'entity_id' : is_null(data.get('id')),   
          'entity_type'  : is_null(data.get('entity_type')), 
          'entity_name'  : is_null(data.get('entity_name')), 
          'first_name'  : is_null(data.get('first_name')), 
          'last_name'  : is_null(data.get('last_name')), 
          'middle_name' : is_null(data.get('middle_name')), 
          'preffix'  : is_null(data.get('prefix')), 
          'suffix' : is_null(data.get('suffix')), 
          'street_1'  : is_null(data.get('street_1')), 
          'street_2'  : is_null(data.get('street_2')), 
          'city'  : is_null(data.get('city')),  
          'state' : is_null(data.get('state')), 
          'zip_code' : is_null(data.get('zip_code')), 
          'occupation'  : is_null(data.get('occupation')), 
          'employer' : is_null(data.get('employer')), 
          'cand_office'  : is_null(data.get('candOffice')), 
          'cand_office_state'  : is_null(data.get('candOfficeState')), 
          'cand_office_district'  : is_null(data.get('candOfficeDistrict')), 
          'ref_cand_cmte_id'  : is_null(data.get('candCmteId')), 
          'phone_number'  : is_null(data.get('phone_number'),'phone_number'),
          'cand_election_year': is_null(data.get('candElectionYear'),'cand_election_year'),
          'last_update_date' : is_null(data.get('lastupdatedate')),
        }

        return datum
    except:
        raise

def put_contact_data(data):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.entity SET 
                    entity_type = %s, 
                    entity_name = %s, 
                    first_name = %s, 
                    last_name = %s, 
                    middle_name = %s, 
                    preffix = %s, 
                    suffix = %s, 
                    street_1 = %s, 
                    street_2 = %s, 
                    city = %s, 
                    state = %s, 
                    zip_code = %s, 
                    occupation = %s, 
                    employer = %s, 
                    ref_cand_cmte_id = %s,
                    cand_office = %s,
                    cand_office_state = %s,
                    cand_office_district = %s,
                    phone_number= %s,
                    cand_election_year =%s,
                    last_update_date = %s 
                WHERE entity_id = %s
                AND cmte_id = %s 
                AND delete_ind is distinct FROM 'Y'
                """,
                [
                data.get('entity_type', ""), 
                data.get('entity_name', ""), 
                data.get('first_name', ""), 
                data.get('last_name', ""), 
                data.get('middle_name', ""), 
                data.get('preffix', ""), 
                data.get('suffix', ""), 
                data.get('street_1', ""), 
                data.get('street_2', ""), 
                data.get('city', ""), 
                data.get('state', ""), 
                data.get('zip_code', None), 
                data.get('occupation', ""), 
                data.get('employer', ""), 
                data.get('ref_cand_cmte_id'), 
                data.get('cand_office', ""),
                data.get('cand_office_state', ""),
                data.get('cand_office_district', ""),
                data.get('phone_number', None),
                data.get('cand_election_year', None),
                datetime.datetime.now(),
                data.get('entity_id'),
                data.get('cmte_id')])                       
                
            if (cursor.rowcount == 0):
                raise Exception(
                    'The Entity ID: {} does not exist in Entity table'.format(entity_id))
    
    except Exception:
        raise

@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def contacts(request):
    """
    contacts api supporting POST, GET, DELETE, PUT
    """

    if request.method == 'POST':
        try:
            #cmte_id = request.user.username
            datum = contact_sql_dict(request.data)
            datum['cmte_id'] = request.user.username
            #datum['cmte_id'] = cmte_id
            post_contact(datum)
            #commented by Mahendra 10052019
            #print ("datum", datum)
            output = get_contact(datum)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The contacts API - POST is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    """
    *********************************************** contact - GET API CALL STARTS HERE **********************************************************
    """
    # Get records from entity table
    if request.method == 'GET':


        try:
            data = {
                'cmte_id': request.user.username,
                }
            if 'report_id' in request.query_params:
                data['report_id'] = request.query_params.get('report_id')
            output = get_contact(data)   
            return JsonResponse(output[0], status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The reports API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    """
    ************************************************* contact - PUT API CALL STARTS HERE **********************************************************
    """
    if request.method == 'PUT':
        try:
            datum = contact_entity_dict(request.data)
            datum['cmte_id'] = request.user.username
            #datum['cmte_id'] = cmte_id
            put_contact_data(datum)
            print ("datum", datum)
            output = get_entities(datum)
            dict_data = output[0]
            dict_data['phone_number'] = str(dict_data['phone_number']) if dict_data.get('phone_number') else ''
            return JsonResponse(dict_data, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            return Response("The contacts API - PUT is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)

        

    """
    ************************************************ contact - DELETE API CALL STARTS HERE **********************************************************
    """
    if request.method == 'DELETE':

        try:
            data = {
                'cmte_id': request.user.username
            }
            if 'id' in request.query_params and check_null_value(request.query_params.get('id')):
                data['id'] = request.query_params.get('id')
            else:
                raise Exception('Missing Input: entity_id is mandatory')
            delete_contact(data)

            return Response("entity ID: {} has been successfully deleted".format(data.get('id')), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The contacts API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

def delete_contact(data):
    """delete contact
    """
    try:
        cmte_id = data.get('cmte_id')
        entity_id = data.get('id')
        delete_sql_contact(cmte_id, entity_id)
    except:
        raise

def delete_sql_contact(cmte_id, entity_id):
    """delete a contact
    """
    try:
        with connection.cursor() as cursor:

            cursor.execute("""UPDATE public.entity SET delete_ind = 'Y' WHERE cmte_id = %s AND entiy_id = %s AND delete_ind is distinct from 'Y'""", [
                           cmte_id, entity_id ])
            if (cursor.rowcount == 0):
                raise Exception(
                    'The entity ID: {} is either already deleted or does not exist in entity table'.format(entity_id))
    except Exception:
        raise

def get_contact(data):
    """load contacts"""
    try:
        cmte_id = data['cmte_id']
        entity_id = data['entity_id']
        if 'entity_id' in data:
            forms_obj = get_list_contact(cmte_id, entity_id)
        return forms_obj
    except:
        raise

def get_list_contact(cmte_id, entity_id = None, name_select_flag = False, entity_name_flag = False):

    try:
        with connection.cursor() as cursor:
            #This Flag seperates whether I need only entity name or first_name, last_name
            if not name_select_flag:
                if isinstance(entity_id, list):
                    query_string = """SELECT cmte_id, entity_id, entity_type, entity_name, first_name, last_name, middle_name, preffix as prefix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, cand_office, cand_office_state, cand_office_district, ref_cand_cmte_id
                                    FROM public.entity WHERE cmte_id = %s AND entity_id in ('{}') AND delete_ind is distinct from 'Y'""".format("', '".join(entity_id))

                    cursor.execute("""SELECT json_agg(t) FROM (""" + query_string +
                                """) t""", [cmte_id])
                # GET single row from entity table
                elif entity_id:
                    query_string = """SELECT cmte_id, entity_type, entity_name, first_name, last_name, middle_name, preffix as prefix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, cand_office, cand_office_state, cand_office_district, ref_cand_cmte_id
                                    FROM public.entity WHERE cmte_id = %s AND entity_id = %s AND delete_ind is distinct from 'Y'"""

                    cursor.execute("""SELECT json_agg(t) FROM (""" + query_string +
                                """) t""", [cmte_id, entity_id])
                else:
                    query_string = """SELECT cmte_id, entity_type, entity_name, first_name, last_name, middle_name,  preffix as prefix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, cand_office, cand_office_state, cand_office_district, ref_cand_cmte_id
                                    FROM public.entity WHERE cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY entity_id DESC"""

                    cursor.execute("""SELECT json_agg(t) FROM (""" +
                               query_string + """) t""", [cmte_id])
            else:
                if entity_name_flag:
                    query_string = """SELECT cmte_id, entity_id, entity_type, entity_name, street_1, street_2, city, state, zip_code, occupation, employer, cand_office, cand_office_state, cand_office_district, ref_cand_cmte_id
                                    FROM public.entity WHERE cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY entity_id DESC"""
                else:
                    query_string = """SELECT cmte_id, entity_id, entity_type, first_name, last_name, middle_name,  preffix as prefix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, cand_office, cand_office_state, cand_office_district, ref_cand_cmte_id
                                    FROM public.entity WHERE cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY entity_id DESC"""
                cursor.execute("""SELECT json_agg(t) FROM (""" +
                               query_string + """) t""", [cmte_id])
 
            contact_list = cursor.fetchone()[0]
            # print("contact_list", contact_list)
            if not contact_list:
                raise NoOPError(
                    'No entity found for cmte_id {} '.format(cmte_id))
            merged_list = []
            for dictA in contact_list:
                entity_id = dictA.get('entity_id')
                data = {
                    'entity_id': entity_id,
                    'cmte_id': cmte_id
                }
                entity_list = get_entities(data)
                dictEntity = entity_list[0]
                merged_dict = {**dictA, **dictEntity}
                merged_list.append(merged_dict)
        return merged_list
    except Exception:
        raise

def is_null(check_value, check_field =""):
    # if phone_nmumber is numeric field so pass 0 as default 
    if check_field == "phone_number" and (check_value == None or check_value in ["null", " ", "", "none", "Null", "None"]):
        return None
    elif check_field == "cand_election_year" and (check_value == None or check_value in ["null", " ", "", "none", "Null", "None"]):
        return None
    elif check_value == None or check_value in ["null", " ", "", "none","Null"]:
        return ""
    else:
        return check_value

def get_reporttype(cmte_id, report_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT report_type FROM public.reports WHERE cmte_id = %s AND report_id = %s """, [cmte_id, report_id])
            data_row=[]
            report_type=""
            if cursor.rowcount > 0:
                for row in cursor.fetchall():
                    data_row = list(row)
                report_type=data_row[0]
            #commented by Mahendra 10052019
            #print("report_type1", report_type)
            if report_type == "":
                cursor.execute("""SELECT id FROM public.forms_committeeinfo WHERE committeeid = %s AND id = %s """, [cmte_id, report_id])
                data_row=[]
                report_type=""
                if cursor.rowcount > 0:
                    for row in cursor.fetchall():
                        data_row = list(row)
                    report_type=data_row[0]
                #commented by Mahendra 10052019
                #print("report_type2", report_type)
                if not report_type:
                    report_type=""
                else:
                    report_type="F99"    
        return(report_type)
    except Exception as e:
        print(e)
        return Response("The get_reporttype API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def delete_trashed_reports(request):
    try:
        """api for trash and restore report. """
        cmte_id = request.user.username
        #commented by Mahendra 10052019
        #print("trash_restore_report cmte_id = ", cmte_id)
        #print("delete_trashed_reports  request.data =", request.data.get('actions', []))
        list_report_ids=''
        for _action in request.data.get('actions', []):
            report_id = _action.get('id', '')
            list_report_ids = list_report_ids + str(report_id) + ", " 
        #commented by Mahendra 10052019
        #print("delete_trashed_reports list_report_ids before rstrip", list_report_ids)    
        report_ids = list_report_ids.strip().rstrip(',')
        #commented by Mahendra 10052019
        #print("delete_trashed_reports list_report_ids", report_ids)    
        with connection.cursor() as cursor:
            cursor.execute("""DELETE FROM public.forms_committeeinfo WHERE id in (""" + report_ids + """) AND committeeid = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.reports WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.form_3x  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_a  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_b  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_c  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_c1  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_c2  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_d  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_e  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_f  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_h1  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_h2  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_h3  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_h4  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_h5  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")
            cursor.execute("""DELETE FROM public.sched_h6  WHERE report_id in (""" + report_ids + """) AND cmte_id = '""" + cmte_id + """'""")      
        message="success"
        json_result = {'message':message}
        return Response(json_result, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response('The delete_trashed_reports API is throwing an error: ' + str(e), status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_all_trashed_reports(request):
    """
    API that provides all the deleted reports for a specific committee
    """
    if request.method == 'GET':
        try:
            cmte_id = request.user.username
            viewtype = request.query_params.get('view')
            reportid = request.query_params.get('reportId')
            #commented by Mahendra 10052019
            #print ("[cmte_id]", cmte_id)
            #print ("[viewtype]", viewtype)
            #print ("[reportid]", reportid)

            forms_obj = None
            with connection.cursor() as cursor:
                if reportid in ["None", "null", " ", "","0"]:    
                    query_string =  """SELECT json_agg(t) FROM 
                                    (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, viewtype ,
                                            deleteddate   
                                     FROM   (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, 
                                         CASE
                                            WHEN (date_part('year', last_update_date) < date_part('year', now())) THEN 'archieve'
                                            WHEN (date_part('year', last_update_date) = date_part('year', now())) THEN 'current'
                                        END AS viewtype,
                                            deleteddate
                                         FROM public.reports_view WHERE cmte_id = %s AND delete_ind = 'Y' AND last_update_date is not null 
                                    ) t1
                                    WHERE  viewtype = %s ORDER BY last_update_date DESC ) t; """
                else:
                    query_string =  """SELECT json_agg(t) FROM 
                                    (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, viewtype ,
                                            deleteddate   
                                     FROM   (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, 
                                         CASE
                                            WHEN (date_part('year', last_update_date) < date_part('year', now())) THEN 'archieve'
                                            WHEN (date_part('year', last_update_date) = date_part('year', now())) THEN 'current'
                                        END AS viewtype,
                                            deleteddate
                                         FROM public.reports_view WHERE cmte_id = %s AND delete_ind = 'Y' AND last_update_date is not null 
                                    ) t1
                                    WHERE report_id = %s  AND  viewtype = %s ORDER BY last_update_date DESC ) t; """

                if reportid in ["None", "null", " ", "","0"]:  
                    cursor.execute(query_string, [cmte_id, viewtype])
                else:
                    cursor.execute(query_string, [cmte_id, reportid, viewtype])

                for row in cursor.fetchall():
                    data_row = list(row)
                    forms_obj=data_row[0]

            if forms_obj is None:
               forms_obj = []

            with connection.cursor() as cursor:

                if reportid in ["None", "null", " ", "","0"]:    
                    query_count_string =  """SELECT count('a') as totalreportsCount FROM 
                                    (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, viewtype ,
                                            deleteddate   
                                     FROM   (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, 
                                         CASE
                                            WHEN (date_part('year', last_update_date) < date_part('year', now())) THEN 'archieve'
                                            WHEN (date_part('year', last_update_date) = date_part('year', now())) THEN 'current'
                                        END AS viewtype,
                                            deleteddate
                                         FROM public.reports_view WHERE cmte_id = %s AND delete_ind = 'Y' AND last_update_date is not null 
                                    ) t1
                                    WHERE  viewtype = %s ORDER BY last_update_date DESC ) t; """
                else:
                    query_count_string =  """SELECT count('a') as totalreportsCount FROM 
                                    (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, viewtype,
                                            deleteddate    
                                     FROM   (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, 
                                         CASE
                                            WHEN (date_part('year', last_update_date) < date_part('year', now())) THEN 'archieve'
                                            WHEN (date_part('year', last_update_date) = date_part('year', now())) THEN 'current'
                                        END AS viewtype,
                                            deleteddate
                                         FROM public.reports_view WHERE cmte_id = %s AND  delete_ind = 'Y' AND last_update_date is not null 
                                    ) t1
                                    WHERE report_id = %s  AND  viewtype = %s ORDER BY last_update_date DESC ) t; """

                if reportid in ["None", "null", " ", "","0"]:  
                    cursor.execute(query_count_string, [cmte_id, viewtype])
                else:
                    cursor.execute(query_count_string, [cmte_id, reportid, viewtype])

                for row in cursor.fetchall():
                    data_row = list(row)
                    forms_cnt_obj=data_row[0]

            if forms_cnt_obj is None:
                forms_cnt_obj = []

            json_result = { 'reports': forms_obj, 'totalreportsCount':forms_cnt_obj}    
        except Exception as e:
            # print (str(e))
            return Response("The reports view api - get_all_trashed_reports is throwing an error" + str(e), status=status.HTTP_400_BAD_REQUEST)

        #return Response(forms_obj, status=status.HTTP_200_OK)
        return Response(json_result, status=status.HTTP_200_OK)

def trash_restore_sql_report(cmte_id, report_id, _delete='Y'):
    """trash or restore reports table by updating delete_ind"""
    try:
        with connection.cursor() as cursor:
            # UPDATE delete_ind flag to Y in DB
            #form 99 report
            report_type = get_reporttype(cmte_id, report_id)
            #commented by Mahendra 10052019
            #print("report_type3", report_type)
            #print("trash_restore_sql_report cmte_id = ", cmte_id)
            #print("trash_restore_sql_report report_id = ", report_id)
            
            if report_type == 'F99':
                if (_delete == 'Y'):
                    cursor.execute("""UPDATE public.forms_committeeinfo SET isdeleted = True, deleted_at = '{}'  WHERE committeeid = '{}' AND id = '{}'  """.format(datetime.datetime.now(), cmte_id, report_id))
                else:
                    cursor.execute("""UPDATE public.forms_committeeinfo SET isdeleted = False, deleted_at = '{}'  WHERE committeeid = '{}' AND id = '{}'  """.format(datetime.datetime.now(), cmte_id, report_id))
                #commented by Mahendra 10052019
                #print("report_type4", report_type)
            else:
                #form 3X report
                cursor.execute("""UPDATE public.reports SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                if not cursor.rowcount:
                    raise Exception(
                        """The report ID: {} is either already deleted
                        or does not exist in reports table""".format(report_id))
                else:
                    cursor.execute("""UPDATE public.form_3x SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_a SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_b SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}' """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_c SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_c1 SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_c2 SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_d SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_e SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_f SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_h1 SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}' """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_h2 SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}' """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_h3 SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_h4 SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_h5 SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}' """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
                    cursor.execute("""UPDATE public.sched_h6 SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND report_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, report_id))
    
    except Exception:
        raise

@api_view(['PUT'])
def trash_restore_report(request):
    """api for trash and restore report. """
    cmte_id = request.user.username
    #commented by Mahendra 10052019
    #print("trash_restore_report  request.data =", request.data.get('actions', []))
    for _action in request.data.get('actions', []):
        report_id = _action.get('id', '')
        #commented by Mahendra 10052019
        #print("trash_restore_report cmte_id = ", cmte_id)
        #print("trash_restore_report report_id = ", report_id)

        result='failed'
        action = _action.get('action', '')
        _delete = 'Y' if action == 'trash' else ''
        try:
            if _delete == 'Y':
                if check_report_to_delete(cmte_id, report_id) == 'N':
                    result = 'failed'
                else:
                    trash_restore_sql_report(cmte_id, report_id, _delete)
                    result = 'success'
            else:
                trash_restore_sql_report(cmte_id, report_id, _delete)
                result = 'success'
        
        except Exception as e:
            return Response("The trash_restore_report API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    if result=='success':
        return Response({"result":"success"}, status=status.HTTP_200_OK)
    else:   
        return Response({"result":"failed"}, status=status.HTTP_200_OK)
    

@api_view(['POST'])
def delete_trashed_contacts(request):
    try:
        """api for trash and restore contact. """
        cmte_id = request.user.username
        #commented by Mahendra 10052019
        #print("trash_restore_contact cmte_id = ", cmte_id)
        #print("delete_trashed_contacts  request.data =", request.data.get('actions', []))
        list_entity_ids="'"
        for _action in request.data.get('actions', []):
            entity_id = _action.get('id', '')
            list_entity_ids = list_entity_ids + str(entity_id) + "','" 
        #print("delete_trashed_contacts list_entity_ids before substring", list_entity_ids)
        entity_ids = list_entity_ids[0:len(list_entity_ids)-2]
        #print("delete_trashed_contacts list_entity_ids", entity_ids)    
        with connection.cursor() as cursor:
             cursor.execute("""DELETE FROM public.entity WHERE entity_id in (""" + entity_ids + """) AND cmte_id = '""" + cmte_id + """'""")
      
        
        message="success"
        json_result = {'message':message}
        return Response(json_result, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response('The delete_trashed_contacts API is throwing an error: ' + str(e), status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def get_all_trashed_contacts(request):
    """
    API that provides all the deleted contacts for a specific committee
    """
    if request.method == 'POST':
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

                keys = ['id', 'entity_type', 'name', 'street1', 'street2', 'city', 'state', 'zip', 'occupation', 'employer', 'candOfficeState', 'candOfficeDistrict', 'candCmteId', 'phone_number', 'deletedDate']
                search_keys = ['id', 'entity_type', 'name', 'street1', 'street2', 'city', 'state', 'zip', 'occupation', 'employer', 'candOfficeState', 'candOfficeDistrict', 'candCmteId', 'phone_number', 'deletedDate']
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
                
                
                #trans_query_string = """SELECT id, type, name, street1, street2, city, state, zip, occupation, employer from all_contacts_view where cmte_id='""" + cmte_id + """' """ + param_string 

                #trans_query_string= """SELECT cmte_id, entity_type, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, , candOffice, candOfficeState, candOfficeDistrict, candCmteId, phone_number FROM public.entity WHERE cmte_id =  AND delete_ind = 'Y' """
                #cursor.execute("""SELECT cmte_id, entity_type, entity_name, first_name, last_name, middle_name, preffix, suffix, street_1, street_2, city, state, zip_code, occupation, employer, , candOffice, candOfficeState, candOfficeDistrict, candCmteId, phone_number FROM public.entity WHERE cmte_id = %s AND delete_ind = 'Y' """.format(cmte_id))

                # print("trans_query_string: ",trans_query_string)
                # import ipdb;ipdb.set_trace()

                trans_query_string = """SELECT id, entity_type, name, street1, street2, city, state, zip, occupation, employer, candOffice, candOfficeState, candOfficeDistrict, candCmteId, phone_number, deleteddate, active_transactions_cnt from all_contacts_view
                    where  deletedFlag = 'Y' AND cmte_id='""" + cmte_id + """' """ + param_string 
                
                if sortcolumn and sortcolumn != 'default':
                    trans_query_string = trans_query_string + """ ORDER BY """+ sortcolumn + """ """ + descending
                elif sortcolumn == 'default':
                    trans_query_string = trans_query_string + """ ORDER BY name ASC"""
                
                #print("contacts recycle trans_query_string: ",trans_query_string)

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
            return Response("The contactsTable API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

def trash_restore_sql_contact(cmte_id, entity_id, _delete='Y'):
    """trash or restore contacts table by updating delete_ind"""
    #commented by Mahendra 10052019
    #print("check_report_to_delete cmte_id = ", cmte_id)
    #print("check_report_to_delete entity_id = ", entity_id)
    try:
        with connection.cursor() as cursor:
            # UPDATE delete_ind flag to Y in DB
            cursor.execute("""UPDATE public.entity SET delete_ind = '{}', last_update_date = '{}' WHERE cmte_id = '{}' AND entity_id = '{}'  """.format(_delete, datetime.datetime.now(), cmte_id, entity_id))
    except Exception:
        raise

@api_view(['PUT'])
def trash_restore_contact(request):
    """api for trash and restore contact. """
    cmte_id = request.user.username
    #commented by Mahendra 10052019
    #print("trash_restore_contact  request.data =", request.data.get('actions', []))
    result=''
    for _action in request.data.get('actions', []):
        entity_id = _action.get('id', '')
        #print("trash_restore_contact entity_id = ", entity_id)
        #print("trash_restore_contact cmte_id = ", cmte_id)
        result='failed'
        action = _action.get('action', '')
        _delete = 'Y' if action == 'trash' else ''
        try:
            if _delete == 'Y':
                #print("trying to trash_restore_contact...")
                if check_contact_to_delete(cmte_id, entity_id) == 'N':
                    result = 'failed'
                else:
                    trash_restore_sql_contact(cmte_id, entity_id, _delete)
                    result = 'success'
            else:
                trash_restore_sql_contact(cmte_id, entity_id, _delete)
                result = 'success'


        except Exception as e:
            return Response("The trash_restore_contact API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
    if result=='success':
        return Response({"result":"success"}, status=status.HTTP_200_OK)
    else:   
        return Response({"result":"failed"}, status=status.HTTP_200_OK)

def check_contact_to_delete(cmte_id, entity_id):
    try:
        #commented by Mahendra 10052019
        #print("check_contact_to_delete cmte_id = ", cmte_id)
        #print("check_contact_to_delete entity_id = ", entity_id)
        _delete = 'Y'
        entity_id_found=''
        with connection.cursor() as cursor:
            cursor.execute("""SELECT entity_id FROM public.all_transactions_view vw, public.reports rp 
                            WHERE rp.cmte_id = %s 
                            AND rp.cmte_id = vw.cmte_id 
                            AND rp.report_id = vw.report_id  
                            AND rp.status= 'Submitted'
                            AND vw.entity_id = %s """, [cmte_id, entity_id])           

            entity_ids = cursor.fetchone()
            #print("entity_ids_found =", entity_ids)
            entity_id_found = entity_ids[0]
            #print("entity_id_found =", entity_id_found)
            if entity_id_found == '':
                _delete = 'Y'
            else:
                _delete = 'N'

        return _delete    
    except Exception as e:
        return Response("The check_contact_to_delete function is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    
def check_report_to_delete(cmte_id, report_id):
    try:
        _delete = 'Y'
        entity_id_found=''
        #commented by Mahendra 10052019
        #print("check_report_to_delete cmte_id = ", cmte_id)
        #print("check_report_to_delete report_id = ", report_id)
        with connection.cursor() as cursor:
            cursor.execute("""SELECT report_id FROM public.all_transactions_view vw, public.reports rp 
                            WHERE rp.cmte_id = %s 
                            AND rp.cmte_id = vw.cmte_id 
                            AND rp.report_id = vw.report_id  
                            AND rp.status= 'Filed'
                            AND vw.report_id = %s """, [cmte_id, report_id])           

            report_ids = cursor.fetchone()
            report_id_found = report_ids[0]
            #print("report_id_found =",report_id_found)
            if entity_id_found == '':
                _delete = 'Y'
            else:
                _delete = 'N'

        return _delete    
    except Exception as e:
        return Response("The check_report_to_delete function is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

def get_next_transaction_id(trans_char):
    """get next transaction_id with seeding letter, like 'SA' """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT public.get_next_transaction_id(%s)""", [trans_char])
            transaction_id = cursor.fetchone()[0]
            # transaction_id = transaction_ids[0]
        return transaction_id
    except Exception:
        raise

def get_sched_h_transaction_table(transaction_id):
    """
    helper function for querying transaction table name for sched h
    """
    _sql = """
    select transaction_table 
    from all_other_transactions_view 
    where transaction_id = %s;
    """
    try:
        with connection.cursor() as cursor:
            logger.debug("fetching transaction table name for {}".format(transaction_id))
            # cursor.execute(table_schema_sql, (transaction_table))
            cursor.execute(_sql, [transaction_id]) 
            if cursor.rowcount == 0:
                raise Exception('transaction_id not found.')
            return cursor.fetchone()[0]
    except:
        raise

@api_view(['POST'])
def clone_a_transaction(request):
    """
    api for clone a transaction. 
    expect: a transaction_id for transaction to be cloned
    return: new transaction_id with clone data in json
    note:
    1. transaction date is set to current date 
    2. transaction amount is set to 0
    3. create date is also today's date 
    4. last update date has null value

    update 20191220: sched_h clone function added. transaction_table for a 
    transaction_id is fetched from all_other_transactions_view
    """
    # TODO: need to update this list for ohter transactions
    logger.debug('request for cloning a transaction:{}'.format(request.data))

    transaction_tables = {
        'SA': 'sched_a',
        'LA': 'sched_a',
        'SB': 'sched_b',
        'LB': 'sched_b',
        'SC': 'sched_c',
        'SD': 'sched_d',
        'SE': 'sched_e',
        'SF': 'sched_f',
    }
    # cmte_id = request.user.username
    transaction_id = request.data.get('transaction_id')
    if not transaction_id:
        raise Exception('Error: transaction_id is required for this api.')

    if transaction_id[0:2] in transaction_tables:
        transaction_table = transaction_tables.get(transaction_id[0:2])
        # raise Exception('Error: invalid transaction id found.')
    elif transaction_id[0:2] == 'SH':
        transaction_table = get_sched_h_transaction_table(transaction_id)
    else:
        raise Exception('Error: invalid transaction id found.')

    table_schema_sql = """
    SELECT column_name FROM information_schema.columns
    WHERE table_name = '{}'
    """.format(transaction_table)
    
    with connection.cursor() as cursor:
        logger.debug("fetching transaction table column names...")
        # cursor.execute(table_schema_sql, (transaction_table))
        cursor.execute(table_schema_sql)
        rows = cursor.fetchall()  
        columns = []
        for row in rows:
            columns.append(row[0])
        logger.debug('table columns: {}'.format(list(columns)))



        insert_str = ','.join(columns)
        replace_list = ['transaction_id', 'create_date', 'last_update_date']
        tmp_list = [col if col not in replace_list else '%s' for col in columns]
        select_str = ','.join(tmp_list)
        print('select_str:{}'.format(select_str))

        # set transaction date to today's date and transaction amount to 0
        from datetime import date
        _today = date.today().strftime('%m/%d/%Y')
        if transaction_id.startswith('SA') or transaction_id.startswith('LA'):
            select_str = select_str.replace('contribution_date', "'"+_today+"'")
            select_str = select_str.replace('contribution_amount', "'"+'0.00'+"'")
        if transaction_id.startswith('SB') or transaction_id.startswith('LB') or transaction_id.startswith('SF'):
            select_str = select_str.replace('expenditure_date', "'"+_today+"'")
            select_str = select_str.replace('expenditure_amount', "'"+'0.00'+"'")
        if transaction_id.startswith('SE'):
            select_str = select_str.replace('disbursement_date', "'"+_today+"'")
            select_str = select_str.replace('dissemination_date', "'"+_today+"'")
            select_str = select_str.replace('expenditure_amount', "'"+'0.00'+"'")
        if transaction_id.startswith('SH') and transaction_table == 'sched_h4':
            select_str = select_str.replace('expenditure_date', "'"+_today+"'")
            select_str = select_str.replace('total_amount', "'"+'0.00'+"'")
            select_str = select_str.replace('non_fed_share_amount', "'"+'0.00'+"'")
            select_str = select_str.replace('fed_share_amount', "'"+'0.00'+"'")
        if transaction_id.startswith('SH') and transaction_table == 'sched_h6':
            select_str = select_str.replace('expenditure_date', "'"+_today+"'")
            select_str = select_str.replace('total_fed_levin_amount', "'"+'0.00'+"'")
            select_str = select_str.replace('federal_share', "'"+'0.00'+"'")
            select_str = select_str.replace('levin_share', "'"+'0.00'+"'")
            # exclude_list = ['expenditure_date', 'expenditure_amount'] 
        # select_str = insert_str.replace(',transaction_id,', ',%s,'
        # ).replace('create_date', '%s'
        # ).replace('last_update_date', '%s')
        
        
        clone_sql = """
            INSERT INTO public.{table_name}({_insert})
            SELECT {_select}
            FROM public.{table_name}
        """.format(table_name=transaction_table, _insert=insert_str, _select=select_str)
        clone_sql = clone_sql + ' WHERE transaction_id = %s;'
        logger.debug('clone transaction with sql:{}'.format(clone_sql))

        new_tran_id = get_next_transaction_id(transaction_id[0:2])
        logger.debug('new transaction id:{}'.format(new_tran_id))

        cursor.execute(clone_sql, (new_tran_id, datetime.datetime.now(), None, transaction_id))

        if not cursor.rowcount:
            raise Exception('transaction clone error')

        # exclude_list = []
        # if transaction_id.startswith('SA'):
        #     exclude_list = ['contribution_date', 'contribution_amount']
        # if transaction_id.startswith('SB'):
            # exclude_list = ['expenditure_date', 'expenditure_amount'] 
        # columns = set(columns) - set(exclude_list)
        select_str = ','.join(columns)
        load_sql = """
        SELECT {_select}
        FROM public.{table_name}
        """.format(table_name=transaction_table, _select=select_str)

        load_sql = """SELECT json_agg(t) 
        FROM (""" + load_sql + """WHERE transaction_id = '{}' ) t
        """.format(new_tran_id)
        logger.debug('load_sql:{}'.format(load_sql))
        cursor.execute(load_sql)
        rep_json = cursor.fetchone()[0]
        for obj in rep_json:
            if transaction_id.startswith('LA'):
                obj['api_call'] = '/sa/schedA'
            if transaction_id.startswith('LB'):
                obj['api_call'] = '/sb/schedB'  

        # return Response({"result":"success", "transaction_id":new_tran_id}, status=status.HTTP_200_OK)
        return Response(rep_json, status=status.HTTP_200_OK)

"""
********************************************************************************************************************************
GET REPORTS AMENDENT API- CORE APP - SPRINT 22 - FNE 1547 - BY YESWANTH KUMAR TELLA
********************************************************************************************************************************
"""
def get_reports_data(report_id):
    try:
        query_string = """SELECT * FROM public.reports WHERE report_id = %s AND status = 'Submitted' AND form_type = 'F3X' AND superceded_report_id IS NULL """
        forms_obj = None
        #print('here',forms_obj)
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [report_id])
            # print(cursor.query)
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        # print(forms_obj)
        if forms_obj is None:
            pass
            #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))   
        return forms_obj
    except Exception:
        raise


# def insert_sql_report(dict_data):
#     try:
#         sql = "INSERT INTO public.reports (" + ", ".join(dict_data.keys()) + ") VALUES (" + ", ".join(["%("+k+")s" for k in dict_data]) + ");"
#         with connection.cursor() as cursor:
#             # INSERT row into Reports table
#             cursor.execute(sql,dict_data)                                          
#     except Exception:
#         raise


def create_amended(reportid):
    try:
        data_dict = get_reports_data(reportid)
        if data_dict:
            #data = data[0]
            # report_id = get_next_report_id()

            for data in data_dict:
                #print(data)
                # data['report_id'] = report_id

                #post_sql_report(reports_obj(''))
                data['amend_ind'] = 'A'
                data['amend_number'] = data.get('amend_number')+1 if data.get('amend_number') else 1
                data['previous_report_id'] = reportid
                #data['report_seq'] = get_next_report_id()
                del data['report_seq']
                data['status'] = 'Saved'
                #print(data,'here')
                data['cvg_start_dt'] = datetime.datetime.strptime(data['cvg_start_date'], '%Y-%m-%d').date()
                data['cvg_end_dt'] = datetime.datetime.strptime(data['cvg_end_date'], '%Y-%m-%d').date()
                # print('just before post_reports')
                created_data = post_reports(data, reportid)
                if type(created_data) is list:                    
                    raise Exception ('coverage dates already cover a existing report id')
                elif type(created_data) is dict:
                    print(created_data)
                # print('just after post_reports')
                # print(data)

                with connection.cursor() as cursor:
                    cursor.execute("""UPDATE public.reports SET superceded_report_id = %s WHERE report_id = %s """,[created_data['reportid'], reportid])
                    cursor.execute("""UPDATE public.reports SET previous_report_id = %s WHERE report_id = %s """,[ reportid, created_data['reportid']])


                return data

        else:
            return False

    except Exception as e:
        print(e)
        return False


def get_report_ids(cmte_id, from_date):
    data_ids =[]
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT report_id FROM public.reports WHERE cmte_id= %s AND cvg_start_date >= %s AND status = 'Submitted' AND form_type = 'F3X' AND superceded_report_id IS NULL""", [cmte_id, from_date])
            if cursor.rowcount > 0:
                for row in cursor.fetchall():
                    data_ids.append(row[0])
            
        return data_ids
    except Exception as e:
        print(e)
        return data_ids


@api_view(['POST'])
def create_amended_reports(request):

    try:
        if request.method == 'POST':
            reportid = request.POST.get('report_id')
            cmte_id = request.user.username

            val_data = get_reports_data(reportid)

            if not val_data:
                return Response("Given Report_id canot be amended", status=status.HTTP_400_BAD_REQUEST)


            cvg_start_date, cvg_end_date = get_cvg_dates(reportid, cmte_id)

            #cdate = date.today()
            from_date = cvg_start_date
            data_obj = None

            report_id_list = get_report_ids(cmte_id, from_date)

            print(report_id_list, from_date)

            if report_id_list:
                for i in report_id_list:
                    amended_obj = create_amended(i)
                    if str(i) == str(reportid):
                        data_obj = amended_obj


            
                    #post_sql_report(report_id, data.get('cmte_id'), data.get('form_type'), data.get('amend_ind'), data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('due_dt'), data.get('status'), data.get('email_1'), data.get('email_2'), data.get('additional_email_1'), data.get('additional_email_2'))
            else:
                return Response("Given Report_id Not found", status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data_obj, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return Response("Create amended report API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)







def none_text_to_none(text):
    try:
        if text in ['None', 'none', 'NONE']:
            return None
        else:
            return text
    except:
        raise

def USPS_address_validation(data):
    try:
        output = {}
        street_1 = data.get('street_1')
        street_2 = data.get('street_2')
        city = data.get('city')
        state = data.get('state')
        zip_code = data.get('zip_code')

        XML_input = """<AddressValidateRequest USERID="{0}">
<Revision>1</Revision>
<Address ID="0">
<Address1>{2}</Address1>
<Address2>{1}</Address2>
<City>{3}</City>
<State>{4}</State>
<Zip5>{5}</Zip5>
<Zip4/>
</Address>
</AddressValidateRequest> """.format(settings.USPS_USERNAME, street_1, street_2, city, state, zip_code)
        parameters = {'API': 'verify',
                        'XML': XML_input}
        response = requests.get("http:" + settings.USPS_API_URL, params=parameters)
        if not response:
            raise Exception(response.json())
        else:
            output['data'] = {}
            root = ElementTree.fromstring(response.text)
            Address = root.find('Address')
            if Address.find('Error') != None:
                output['status_code'] = "FAIL"
            else:
                output['status_code'] = "SUCCESS"
                output['data']['street_1'] = Address.find('Address2').text
                output['data']['street_2'] = none_text_to_none(Address.find('Address1').text)
                output['data']['city'] = none_text_to_none(Address.find('City').text)
                output['data']['state'] = Address.find('State').text
                output['data']['zip_code'] = Address.find('Zip5').text
                output['data']['zip_code4'] = none_text_to_none(Address.find('Zip4').text)
                if Address.find('ReturnText') != None:
                    output['status_code'] = "WARNING"
                    output['warning_message'] = Address.find('ReturnText').text
            return output
    except Exception as err:
        raise Exception(f'USPS_address_validation API is throwing an error: {err}')

@api_view(['POST'])
def address_validation(request):
    try:
        output = USPS_address_validation(request.data)
        return Response(output, status.HTTP_200_OK)

    except requests.exceptions.HTTPError as http_err:
        return Response(f'address_validation API is throwing an HTTP error: {http_err}', status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        return Response(f'address_validation API is throwing an error: {err}', status=status.HTTP_400_BAD_REQUEST)

def partial_match(x,y):
    return(max(fuzz.ratio(x,y),fuzz.partial_ratio(x,y),fuzz.token_sort_ratio(x,y),fuzz.token_set_ratio(x,y),fuzz.WRatio(x,y)))

def duplicate_address(cmte_id, data):
    try:
        moderation_score = 92
        if 'entity_name' in data and data.get('entity_name') not in ['null', 'None', '', "", None]:
            org_name_flag = True
            input_name = data.get('entity_name')
        else:
            org_name_flag = False
            input_list = [data.get('preffix'), data.get('first_name'), data.get('middle_name'), data.get('last_name'), data.get('suffix')]
            input_name = " ".join(filter(None, input_list))

        USPS_input = USPS_address_validation(data)
        if USPS_input.get('status_code') != "FAIL":
            input_address = " ".join(filter(None, [USPS_input.get('data').get('street_1'), USPS_input.get('data').get('street_2'), USPS_input.get('data').get('city'), USPS_input.get('data').get('state'), USPS_input.get('data').get('zip_code')]))
        else:
            input_address = " ".join(filter(None, [data.get('street_1'), data.get('street_2'), data.get('city'), data.get('state')]))
            if 'zip_code' in data and data.get('zip_code') not in ['null', 'None', '', "", None]:
                input_address += " " + data.get('zip_code')[0:5]
        input_total_address_list = [" ".join([input_name, input_address, data.get('occupation',""), data.get('employer',"")])]

        contact_list = get_list_contact(cmte_id, None, True, org_name_flag)
        compare_entity_id_list = []
        compare_total_address_list = []
        if org_name_flag:
            for contact in contact_list:
                compare_entity_id_list.append(contact.get('entity_id'))
                if 'zip_code' in contact and contact.get('zip_code') not in ['null', 'None', '', "", None]:
                    compare_total_address = " ".join(filter(None, [contact.get('entity_name'), contact.get('street_1'), contact.get('street_2'), contact.get('city'), contact.get('state'), contact.get('zip_code')[0:5], contact.get('occupation'), contact.get('employer')]))
                else:
                    compare_total_address = " ".join(filter(None, [contact.get('entity_name'), contact.get('street_1'), contact.get('street_2'), contact.get('city'), contact.get('state'), contact.get('occupation'), contact.get('employer')]))
                compare_total_address_list.append(compare_total_address)
        else:
            for contact in contact_list:
                compare_entity_id_list.append(contact.get('entity_id'))
                if 'zip_code' in contact and contact.get('zip_code') not in ['null', 'None', '', "", None]:
                    compare_total_address_list.append(" ".join(filter(None, [contact.get('preffix'), contact.get('first_name'), contact.get('middle_name'), contact.get('last_name'), contact.get('suffix'), contact.get('street_1'), contact.get('street_2'), contact.get('city'), contact.get('state'), contact.get('zip_code')[0:5], contact.get('occupation'), contact.get('employer')])))
                else:
                    compare_total_address_list.append(" ".join(filter(None, [contact.get('preffix'), contact.get('first_name'), contact.get('middle_name'), contact.get('last_name'), contact.get('suffix'), contact.get('street_1'), contact.get('street_2'), contact.get('city'), contact.get('state'), contact.get('occupation'), contact.get('employer')])))
        inputcolumn = pandas.DataFrame(input_total_address_list)
        inputcolumn.columns = ['Match']
        compare_dict = {'EntityId':compare_entity_id_list, 'Compare':compare_total_address_list}
        comparecolumn = pandas.DataFrame(compare_dict)

        inputcolumn['Key'] = 1
        comparecolumn['Key'] = 1
        combined_dataframe = comparecolumn.merge(inputcolumn,on="Key",how="left")

        partial_match_vector = numpy.vectorize(partial_match)
        combined_dataframe['Score']=partial_match_vector(combined_dataframe['Match'],combined_dataframe['Compare'])
        combined_dataframe = combined_dataframe[combined_dataframe.Score>=moderation_score]
        if combined_dataframe.empty:
            return []
        else:
            return get_list_contact(cmte_id, combined_dataframe['EntityId'].values.tolist())

    except Exception as e:
        raise Exception(f'duplicate_Address function is throwing an error: {e}')

@api_view(['POST'])
def check_duplicate_address(request):
    try:
        cmte_id = request.user.username
        address = duplicate_address(cmte_id, request.data)
        if address:
            status_code = "FAIL"
            status_desc = "Duplicate exists"
        else:
            status_code = "SUCCESS"
            status_desc = "Duplicate does not exist"
        output = {}
        output['statusCode'] = status_code
        output['statusDescription'] = status_desc
        output['data'] = address
        return Response(output, status=status.HTTP_200_OK)
    except requests.exceptions.HTTPError as http_err:
        return Response(f'address_validation API is throwing an HTTP error: {http_err}', status=status.HTTP_400_BAD_REQUEST)
    except Exception as err:
        return Response(f'address_validation API is throwing an error: {err}', status=status.HTTP_400_BAD_REQUEST)

def get_next_levin_acct_id():
    """
    get a new levin account id
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT nextval('levin_account_id_seq')""")
            return cursor.fetchone()[0]
    except Exception:
        logger.debug('failed to get a new levin account id.')
        raise 


def get_levin_accounts(cmte_id):
    """
    load levin_account names and account ids for a committee
    """
    _sql = """
    select json_agg(t) from 
    (select levin_account_id, levin_account_name 
    from levin_account where cmte_id = %s 
    and delete_ind is distinct from 'Y') t
    """
    try:
        with connection.cursor() as cursor:
                # INSERT row into Reports table
            cursor.execute(_sql,[cmte_id])
            return cursor.fetchone()[0]  
    except Exception as e:
        logger.debug('Error on loading levin account names:'+str(e))
        raise

def get_levin_account(cmte_id, levin_account_id):
    """
    load levin_account names and account ids for a committee
    """
    _sql = """
    select json_agg(t) from 
    (select levin_account_id, levin_account_name, create_date, last_update_date
    from levin_account where cmte_id = %s
    and levin_account_id = %s
    and delete_ind is distinct from 'Y') t
    """
    try:
        with connection.cursor() as cursor:
                # INSERT row into Reports table
            cursor.execute(_sql,[cmte_id, levin_account_id])
            return cursor.fetchone()[0]  
    except Exception as e:
        logger.debug('Error on loading levin account names:'+str(e))
        raise

def post_levin_account(cmte_id, levin_account_id, levin_account_name):
    """
    db transaction for saving a new levin account
    """
    _sql = """
    INSERT INTO public.levin_account(levin_account_id, cmte_id, levin_account_name) 
    VALUES(%s, %s, %s)
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (levin_account_id, cmte_id, levin_account_name))
    except Exception as e:
        raise Exception('Error creating levin account.')
    

def put_levin_account(cmte_id, levin_account_id, levin_account_name):
    """
    db transaction for updating a levin acccount name
    """
    _sql = """
    UPDATE public.levin_account
    SET levin_account_name = %s
    WHERE cmte_id = %s
    AND levin_account_id = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (levin_account_name, cmte_id, levin_account_id))
    except Exception as e:
        raise Exception('Error updating levin account.')

def delete_levin_account(cmte_id, levin_account_id):
    """
    delete a levin account
    """    
    _sql = """
        UPDATE public.levin_account
        SET delete_ind = 'Y'
        WHERE cmte_id = %s
        AND levin_account_id = %s 
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (cmte_id, levin_account_id))
    except Exception as e:
        raise Exception('Error deleting levin account.')

@api_view(['POST','GET','DELETE','PUT'])
def levin_accounts(request):
    """
    the api for adding/retrieving levin accounts
    """
    if request.method == 'GET':
        try:
            cmte_id = request.user.username
            levin_account_id = request.query_params.get('levin_account_id')
            if not levin_account_id:
                forms_obj = get_levin_accounts(cmte_id)
            else:
                forms_obj = get_levin_account(cmte_id, levin_account_id)
                
            if forms_obj:   
                return JsonResponse(forms_obj, status=status.HTTP_200_OK, safe=False)
            else:
                return JsonResponse([], status=status.HTTP_204_NO_CONTENT, safe=False)

        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response(
                "The levin_account API - GET is throwing an error: " + str(e), 
                status.HTTP_400_BAD_REQUEST
            )

    elif request.method == 'POST':
        try:
            cmte_id = request.user.username

            if not 'levin_account_name' in request.data:
                raise Exception('levin account name is required.')
            if not request.data.get('levin_account_name'):
                raise Exception('a valid levin account name is required.')
            levin_account_name = request.data.get('levin_account_name')

            levin_account_id = get_next_levin_acct_id()
            post_levin_account(cmte_id, levin_account_id, levin_account_name)
            levin_obj = get_levin_account(cmte_id, levin_account_id)
            return Response(
                levin_obj, status.HTTP_200_OK
            )
        except Exception as e:
            logger.debug('Error on creating a new levin account:'+str(e))
            return Response(
                "Error on creating a new levin account:" + str(e),
                status.HTTP_400_BAD_REQUEST
            )

    elif request.method == 'PUT':
        try:
            cmte_id = request.user.username
            levin_account_name = request.data.get('levin_account_name')
            levin_account_id = request.data.get('levin_account_id')
            put_levin_account(cmte_id, levin_account_id, levin_account_name)
            levin_obj = get_levin_account(cmte_id, levin_account_id)
            return Response(
                levin_obj,
                status.HTTP_200_OK
            )
        except Exception as e:
            logger.debug('Error on saving a new levin account name:' + str(e))
            return Response(
                'Error on saving levin account name:' + str(e),
                status.HTTP_400_BAD_REQUEST
            )
    elif request.method == 'DELETE':
        try:
            cmte_id = request.user.username
            levin_account_id = request.query_params.get('levin_account_id')
            if not levin_account_id:
                raise Exception('a valid levin account id is required.')
            delete_levin_account(cmte_id, levin_account_id)
            return Response("The account: {} has been successfully deleted".format(levin_account_id),status=status.HTTP_200_OK)
        except Exception as e:
            logger.debug('Error on deleting account:' + str(e))
            return Response("The levin account API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)        


        
        

    else:
        pass

@api_view(['PUT'])
def new_report_update_date(request):
    logger.debug('request for update report last_update_date:')
    try:
        if request.method == 'PUT':
            cmte_id = request.user.username
            logger.debug('cmte id:{}'.format(cmte_id))
            if not request.data.get('report_id'):
                raise Exception("Error: report_id is required for this api.")
            report_id = check_report_id(request.data.get('report_id'))
            logger.debug('report_id:{}'.format(report_id))
            _sql = """
            UPDATE public.reports
            SET last_update_date = %s
            WHERE cmte_id = %s
            AND report_id = %s 
            """
            with connection.cursor() as cursor:
                cursor.execute(_sql, [
                    datetime.datetime.now(),
                    cmte_id,
                    report_id
                ])
                if cursor.rowcount == 0:
                    raise Exception('Error: updating report update date failed.')
            
        else:
            raise Exception('Error: request type not implemented.')
    except Exception as e:
        return Response(
            "new report update date API is throwing an error: " + str(e), 
            status=status.HTTP_400_BAD_REQUEST
            )
    return Response({"result" : "success"}, status=status.HTTP_200_OK)

"""
********************************************************************************************************************************
GET REPORT STATUS SPRINT-23 - FNE 1064 - BY MAHENDRA MARATHE
********************************************************************************************************************************
"""
@api_view(['GET'])
def get_report_status(request):

    try:
        cmte_id = request.user.username
        report_id =request.query_params.get('report_id')
        form_type =request.query_params.get('form_type')
        
        with connection.cursor() as cursor:
            forms_obj= {}

            if form_type == "F99":    
                cursor.execute("SELECT id as report_id, fec_status, fec_id FROM public.forms_committeeinfo  WHERE committeeid = %s AND id = %s", [cmte_id, report_id])
            elif form_type == "F3X":
                cursor.execute("SELECT report_id, fec_status, fec_id FROM public.reports  WHERE cmte_id = %s AND report_id = %s", [cmte_id, report_id])
            
            for row in cursor.fetchall():
                data_row = list(row)

                if (data_row[1] == '' or data_row[1] == None):
                        forms_obj = {
                        'report_id':data_row[0],
                        'fec_status':'',
                        'fec_id':''
                        }
                else:
                    forms_obj = {
                        'report_id':data_row[0],
                        'fec_status':data_row[1],
                        'fec_id':data_row[2]
                         }

        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_report_status API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

"""
********************************************************************************************************************************
GET LOAN ENDORSER DYNAMIC FORM FIELDS API- CORE APP - SPRINT 23 - FNE 1502 - BY MAHENDRA MARATHE
********************************************************************************************************************************
"""
@api_view(['GET'])
def get_sched_c_endorser_dynamic_forms_fields(request):

    try:

        with open(os.path.dirname(__file__) + "/loan_endorser_fields.json", encoding='utf-8', errors='ignore') as loan_endorser_json_file:
            data_obj = json.load(loan_endorser_json_file)
                
        if not bool(data_obj):
            return Response("Loan Endorser dynamice fields json file is missing...!", status=status.HTTP_400_BAD_REQUEST)                              
        
        return JsonResponse(data_obj, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return Response("The get_sched_c_endorser_dynamic_forms_fields API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


"""
********************************************************************************************************************************
GET LOAN  DYNAMIC FORM FIELDS API- CORE APP - SPRINT 23 - FNE 1501 - BY MAHENDRA MARATHE
********************************************************************************************************************************
"""
@api_view(['GET'])
def get_sched_c_loan_dynamic_forms_fields(request):

    try:
        print("get_sched_c_loan_dynamic_forms_fields called...")
        with open(os.path.dirname(__file__) + "/loan_fields.json", encoding='utf-8', errors='ignore') as loans_json_file:
            data_obj = json.load(loans_json_file)
                
        if not bool(data_obj):
            return Response("Loan dynamice fields json file is missing...!", status=status.HTTP_400_BAD_REQUEST)                              
        
        return JsonResponse(data_obj, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return Response("The get_sched_c_loan_dynamic_forms_fields API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


"""
********************************************************************************************************************************
GET LOAN REPAYMENT DYNAMIC FORM FIELDS API- CORE APP - SPRINT 23 - FNE 1503 - BY MAHENDRA MARATHE
********************************************************************************************************************************
"""
@api_view(['GET'])
def get_sched_c_loanPayment_dynamic_forms_fields(request):

    try:

        with open(os.path.dirname(__file__) + "/loan_endorser_fields.json", encoding='utf-8', errors='ignore') as loan_repayment_json_file:
            data_obj = json.load(loan_repayment_json_file)
                
        if not bool(data_obj):
            return Response("Loan Repayment dynamice fields json file is missing...!", status=status.HTTP_400_BAD_REQUEST)                              
        
        return JsonResponse(data_obj, status=status.HTTP_200_OK, safe=False)
    except Exception as e:
        return Response("The get_sched_c_loanPayment_dynamic_forms_fields API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

"""
********************************************************************************************************************************
GET COVERAGE DATES BASED ON A REPORT ID - BY ZOBAIR SALEEM
********************************************************************************************************************************
"""
@api_view(['GET'])
def get_coverage_dates(request):

    try:
        cmte_id = request.user.username
        report_id =request.query_params.get('report_id')
        
        with connection.cursor() as cursor:
            forms_obj= {}
            cursor.execute("SELECT cvg_start_date, cvg_end_date FROM reports where report_id = %s ", [report_id])
            
            row = cursor.fetchone()
            data_row = list(row)

            forms_obj = {
                'cvg_start_date':data_row[0],
                'cvg_end_date':data_row[1]
                }

        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_coverage_datess API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


"""
********************************************************************************************************************************
END LOAN REPAYMENT DYNAMIC FORM FIELDS API
********************************************************************************************************************************
"""
"""
********************************************************************************************************************************
Creating API FOR UPDATING Schedule-L SUMMARY TABLE - CORE APP - SPRINT 25 - FNE 1800- BY  Yeswanth Kumar Tella
********************************************************************************************************************************
"""

def get_sl_cash_on_hand_cop(report_id, cmte_id, levin_accnt_name, yr_to_dat):
    try:
        prev_yr = False
        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)

        if yr_to_dat:
            #cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)
            from_date = date(cvg_start_date.year, 1,1)
            #to_date = date(cvg_end_date.year, 12, 31)
            prev_cvg_year = cvg_start_date.year - 1
            prev_cvg_end_dt = datetime.date(prev_cvg_year, 12, 31)

            # print(prev_cvg_end_dt,'prevvvvvvvvvvvvvvvvvvvvvvvv')
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(t1.coh_cop, 0) from public.sched_l t1 where t1.cmte_id = %s AND t1.account_name = %s AND t1.cvg_end_date <= %s AND t1.delete_ind is distinct from 'Y' order by t1.cvg_end_date desc limit 1", 
                [cmte_id, levin_accnt_name, prev_cvg_end_dt])
                if (cursor.rowcount == 0):
                    coh_cop = 0
                else:
                    result = cursor.fetchone()
                    coh_cop = result[0]

        else:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(t1.coh_cop, 0) from public.sched_l t1 where t1.cmte_id = %s AND t1.account_name = %s AND t1.cvg_end_date < %s AND t1.delete_ind is distinct from 'Y' order by t1.cvg_end_date desc limit 1", 
                [cmte_id, levin_accnt_name, cvg_end_date])
                if (cursor.rowcount == 0):
                    coh_cop = 0
                else:
                    result = cursor.fetchone()
                    coh_cop = result[0]

        return coh_cop
    except Exception as e:
        raise Exception(
            "The prev_cash_on_hand_cop(sl) function is throwing an error: " + str(e)
        )

def get_sl_item_aggregate(report_id, cmte_id, prev_yr,levin_accnt_name):
    try:
        # import pdb;pdb.set_trace()
        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)
        # import pdb;pdb.set_trace()
        if not prev_yr:
            #cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)
            from_date = date(cvg_start_date.year, 1,1)
            #to_date = date(cvg_end_date.year, 12, 31)
            to_date = cvg_end_date

        with connection.cursor() as cursor:
            if prev_yr:
                cursor.execute("""
                    SELECT SUM(aggregate_amt) from public.sched_a sa
                    join levin_account la on sa.levin_account_id = la.levin_account_id 
                    where sa.cmte_id = %s AND sa.aggregate_amt > 200 AND sa.line_number = '1A' AND sa.report_id= %s  AND sa.delete_ind is distinct from 'Y'""",
                    [cmte_id, report_id]
                )
            else:
                cursor.execute("""
                    SELECT SUM(aggregate_amt) from public.sched_a sa
                    join levin_account la on sa.levin_account_id = la.levin_account_id 
                    where sa.cmte_id = %s AND sa.aggregate_amt > 200 AND sa.line_number = '1A' AND sa.contribution_date >= %s AND sa.contribution_date <= %s AND sa.delete_ind is distinct from 'Y'""",
                    [cmte_id, from_date, to_date]
                )
            if cursor.rowcount == 0:
                agg_amt = 0
            else:
                result = cursor.fetchone()
                agg_amt = result[0] if result[0] else 0
        

        return agg_amt
    except Exception as e:
        raise Exception(
            "The Agg itm_amnt: " + str(e)
        )

def get_sl_unitem_aggregate(report_id, cmte_id, prev_yr, levin_accnt_name):
    try:
        if not prev_yr:
            cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)
            from_date = date(cvg_start_date.year, 1,1)
            #to_date = date(cvg_end_date.year, 12, 31)
            to_date = cvg_end_date
        with connection.cursor() as cursor:
            if prev_yr:
                cursor.execute("""
                    SELECT SUM(aggregate_amt) from public.sched_a sa
                    join levin_account la on sa.levin_account_id = la.levin_account_id 
                    where sa.cmte_id = %s AND sa.aggregate_amt <= 200 AND sa.line_number = '1A' AND sa.report_id= %s  AND sa.delete_ind is distinct from 'Y'""",
                    [cmte_id, report_id]
                )
            else:
                cursor.execute("""
                    SELECT SUM(aggregate_amt) from public.sched_a sa
                    join levin_account la on sa.levin_account_id = la.levin_account_id 
                    where sa.cmte_id = %s AND sa.aggregate_amt <= 200 AND sa.line_number = '1A' AND sa.contribution_date >= %s AND sa.contribution_date <= %s AND sa.delete_ind is distinct from 'Y'""",
                    [cmte_id,from_date, to_date]
                )
            if cursor.rowcount == 0:
                agg_amt = 0
            else:
                result = cursor.fetchone()
                agg_amt = result[0] if result[0] else 0

        return agg_amt
    except Exception as e:
        raise Exception(
            "The Agg unitem_amnt: " + str(e)
        )

def get_sl_line_sum_value(line_number, levin_accnt_name, formula, sched_la_line_sum_dict, cmte_id, report_id, prev_yr=None):
    #print(line_number, levin_accnt_name, formula, sched_la_line_sum_dict, cmte_id, report_id, prev_yr,'paramss')
   
    val = 0
    if line_number == '1a':
        sl_item_val = get_sl_item_aggregate(report_id, cmte_id, prev_yr, levin_accnt_name)
        #print(sl_item_val,'-item vel',levin_accnt_name)
        
        return sl_item_val,levin_accnt_name

    if line_number == '1b':
        sl_unitem_val = get_sl_unitem_aggregate(report_id, cmte_id, prev_yr, levin_accnt_name)
        return sl_unitem_val,levin_accnt_name

    if line_number == '7':
       
        if formula == '':
          val = get_sl_cash_on_hand_cop(report_id, cmte_id, levin_accnt_name, False)
        else:
          val = get_sl_cash_on_hand_cop(report_id, cmte_id, levin_accnt_name, True)
         
       
        return val,levin_accnt_name

 
 
    if formula == "":
       
        val += sched_la_line_sum_dict.get(line_number, 0)[0] if sched_la_line_sum_dict.get(line_number, 0) else 0
      
        return val,levin_accnt_name
    if formula == "0":
        return val,levin_accnt_name
    formula_split = formula.replace(' ', '').split('+')

    #print(formula_split,'formula_split')
    
    if len(formula_split) == 1:
        if '-' in formula_split[0]:
           
            cl_n = formula_split[0].replace(' ', '')
            val += get_sl_line_sum_value(cl_n.split('-')[0],levin_accnt_name, "", sched_la_line_sum_dict, cmte_id,
                                          report_id)[0] - get_sl_line_sum_value(cl_n.split('-')[1],levin_accnt_name, "", sched_la_line_sum_dict, cmte_id,
                                          report_id)[0]
        else:
           
            line_number = formula_split[0]
            val += sched_la_line_sum_dict.get(line_number, 0)[0] if sched_la_line_sum_dict.get(line_number, 0) else 0

    else:
        for cl_n in formula_split:
            if '-' in cl_n:
                val += get_sl_line_sum_value(cl_n.split('-')[0],levin_accnt_name, "", sched_la_line_sum_dict, cmte_id,
                                          report_id) - get_sl_line_sum_value(cl_n.split('-')[1],levin_accnt_name, "", sched_la_line_sum_dict, cmte_id,
                                          report_id)[0]
            else:

                #print(cl_n,levin_accnt_name, "", sched_la_line_sum_dict, cmte_id, report_id,'addddddddddddddddddddddddddddddddddddddddddddddddd')
              
                #line_val = get_sl_line_sum_value(cl_n,levin_accnt_name, "", sched_la_line_sum_dict, cmte_id, report_id)
                val_l_changed = sched_la_line_sum_dict.get(cl_n, 0)[0] if sched_la_line_sum_dict.get(cl_n, 0) else 0
                if val_l_changed:
                    val += val_l_changed
                else:
                    val += get_sl_line_sum_value(cl_n,levin_accnt_name, "", sched_la_line_sum_dict, cmte_id, report_id)[0]
                # print(val,'val-add')
               
    return val,levin_accnt_name


@api_view(['POST'])
def prepare_Schedl_summary_data(request):
    try:
        # import ipdb;ipdb.set_trace()
        cmte_id = request.user.username
        param_string = ""
        report_id = request.data.get('report_id')
        sched_la_line_sum = {}
        sched_lb_line_sum = {}

        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)
        
        #cdate = date.today()
        from_date = date(cvg_start_date.year, 1,1)
       
        to_date = cvg_end_date
       

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT sa.line_number, sum(sa.contribution_amount), la.levin_account_name from public.sched_a sa
                join levin_account la on sa.levin_account_id = la.levin_account_id  
                where sa.cmte_id = '%s' AND sa.report_id = '%s'  And line_number in ('1A','2')  group by sa.line_number,la.levin_account_name;""" %(cmte_id, report_id))
           
            sched_la_line_sum_result = cursor.fetchall()
            sched_la_line_sum = {str(i[0].lower()): (i[1], i[2]) if i[1] else (0, i[2]) for i in sched_la_line_sum_result}

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT sb.line_number, sum(sb.expenditure_amount), la.levin_account_name from public.sched_b sb
                join levin_account la on sb.levin_account_id = la.levin_account_id 
                where sb.cmte_id = '%s' AND sb.report_id = '%s' AND sb.line_number in  ('4A', '4B','4C','4D','5') group by sb.line_number,la.levin_account_name;""" %(cmte_id, report_id))
         
            sched_lb_line_sum_result = cursor.fetchall()
            sched_lb_line_sum = {str(i[0].lower()): (i[1], i[2]) if i[1] else (0, i[2]) for i in sched_lb_line_sum_result}
        
        schedule_la_lb_line_sum_dict = {}
        schedule_la_lb_line_sum_dict.update(sched_la_line_sum)
        schedule_la_lb_line_sum_dict.update(sched_lb_line_sum)

 

        col_la_line_sum = {}
        col_lb_line_sum = {}


        with connection.cursor() as cursor:
            cursor.execute(""" 
                SELECT sa.line_number, sum(sa.contribution_amount), la.levin_account_name from public.sched_a sa
                join levin_account la on sa.levin_account_id = la.levin_account_id  
                where sa.cmte_id = %s AND sa.contribution_date >= %s AND sa.contribution_date <= %s AND sa.line_number in ('1A','2') AND
                sa.delete_ind is distinct from 'Y' group by sa.line_number,la.levin_account_name;""", [cmte_id, from_date, to_date])

            col_la_line_sum_result = cursor.fetchall()
            col_la_line_sum = {str(i[0].lower()): (i[1], i[2]) if i[1] else (0, i[2]) for i in col_la_line_sum_result}
           
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT sb.line_number, sum(sb.expenditure_amount), la.levin_account_name from public.sched_b sb
                join levin_account la on sb.levin_account_id = la.levin_account_id 
                where sb.cmte_id = %s AND sb.expenditure_date >= %s AND sb.expenditure_date <= %s AND sb.line_number in  ('4A', '4B','4C','4D','5') AND
                sb.delete_ind is distinct from 'Y' group by sb.line_number,la.levin_account_name;""", [cmte_id, from_date, to_date])
            
            col_lb_line_sum_result = cursor.fetchall()
            col_lb_line_sum = {str(i[0].lower()): (i[1], i[2]) if i[1] else (0, i[2]) for i in col_lb_line_sum_result}
           
        
        col_line_sum_dict = {}
        col_line_sum_dict.update(col_la_line_sum)
        col_line_sum_dict.update(col_lb_line_sum)

        


        col_la = [('1a', ''),('1b', ''),
                ('1c', '1a+1b'),('2', ''),('3', '1c+2'), ('4a', ''),('4b', ''), ('4c', ''), 
                ('4d', ''), ('4e', '4a+4b+4c+4d'), ('5', ''), ('6', '4e+5'), ('7', ''), ('8', '3'), ('9', '7+8'), 
                ('10', '6'), ('11', '9 - 10')]
        
       

        col_la_dict_original = OrderedDict()
        for i in col_la:
            col_la_dict_original[i[0]] = i[1]
        final_col_la_dict = {}
        #print(col_la_dict_original,';;;;;;;;;;;;;;;;;;;;;;;;;;;;;')

       
        levin_name = ''
        for line_number in col_la_dict_original:
            if not levin_name:
                levin_name = schedule_la_lb_line_sum_dict.get(line_number)[1] if schedule_la_lb_line_sum_dict.get(line_number) else ''
                #print(line_number,levin_name,'------------line_number lllllllllllllllllllllllllllllllllllll')
            
            final_col_la_dict[line_number] = get_sl_line_sum_value(line_number,levin_name, 
                                                               col_la_dict_original[line_number],
                                                               schedule_la_lb_line_sum_dict, cmte_id, report_id, True)
           
           
            schedule_la_lb_line_sum_dict[line_number] = final_col_la_dict[line_number]
            #print(schedule_la_lb_line_sum_dict,'vallllllllllllllllllllllllllllllllllll scaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
   
        

        col_lb = [('1a', ''),
                ('1b', ''), ('1c', '1a+1b'), ('2', ''), ('3', '1c+2'), ('4a', ''),('4b', ''), ('4c', ''), 
                ('4d', ''), ('4e', '4a+4b+4c+4d'), ('5', ''), ('6', '4e+5'), ('7', 'prev'), ('8', '3'), ('9', '7+8'), 
                ('10', '6'), ('11', '9 - 10')]



        col_lb_dict_original = OrderedDict()
        for i in col_lb:
            col_lb_dict_original[i[0]] = i[1]
        final_col_lb_dict = {}
        for line_number in col_lb_dict_original:
            if not levin_name:
                levin_name = col_line_sum_dict.get(line_number)[1] if col_line_sum_dict.get(line_number) else ''
            final_col_lb_dict[line_number] = get_sl_line_sum_value(line_number,levin_name, col_lb_dict_original[line_number],
                                                               col_line_sum_dict,
                                                               cmte_id, report_id, False)
            col_line_sum_dict[line_number] = final_col_lb_dict[line_number]


        for i in final_col_la_dict:
            la_val = final_col_la_dict[i]
            lb_val = final_col_lb_dict.get(i)
            la_formula = col_la_dict_original.get(i, "")
            lb_formula = col_lb_dict_original.get(i, "")
            if la_formula:
                la_formula = la_formula.replace(" ", "")
            if lb_formula:
                lb_formula = lb_formula.replace(" ", "")

           
            final_col_lb_dict[i] = lb_val
            final_col_la_dict[i] = la_val
        


        update_col_la_dict = {'1a': 'item_receipts',
                             '1b': 'unitem_receipts',
                             '1c': 'total_c_receipts',
                             '2':  'other_receipts',
                             '3':  'total_receipts',
                             '4a': 'voter_reg_disb_amount',
                             '4b': 'voter_id_disb_amount',
                             '4c': 'gotv_disb_amount',
                             '4d': 'generic_campaign_disb_amount',
                             '4e': 'total_tran_to_fed_or_alloc',
                             '5':  'other_disb',
                             '6':  'total_disb',
                             '7':  'coh_bop',
                             '8':  'receipts',
                             '9':  'subtotal',
                             '10': 'disbursements',
                             '11': 'coh_cop'}

        update_col_lb_dict = {'1a': 'item_receipts_ytd',
                             '1b': 'unitem_receipts_ytd',
                             '1c': 'total_c_receipts_ytd',
                             '2': 'other_receipts_ytd',
                             '3': 'total_receipts_ytd',
                             '4a': 'voter_reg_disb_amount_ytd',
                             '4b': 'voter_id_disb_amount_ytd',
                             '4c': 'gotv_disb_amount_ytd',
                             '4d': 'generic_campaign_disb_amount_ytd',
                             '4e': 'total_tran_to_fed_or_alloc_ytd',
                             '5': 'other_disb_ytd',
                             '6': 'total_disb_ytd',
                             '7': 'coh_coy',
                             '8': 'receipts_ytd',
                             '9': 'sub_total_ytd',
                             '10': 'disbursements_ytd',
                             '11': 'coh_cop_ytd'}
        
        update_str = ""
        levin_accnt_name = None
        sum_value = 0
        for i in update_col_la_dict:
            dict_value = final_col_la_dict.get(i, None)
            if dict_value in ["",None, "None"]:
                sum_value = 0
                levin_accnt_name = None
            else:
              sum_value = dict_value[0]
              levin_accnt_name = dict_value[1]
            update_str += "%s=%s," % (update_col_la_dict[i], str(sum_value))
            # update_str += "%s='%s'," % ('account_name', str(levin_accnt_name))
        for i in update_col_lb_dict:
            dict_value = final_col_lb_dict.get(i, None)
            if dict_value in ["",None, "None"]:
                sum_value = 0
                levin_accnt_name = None
            else:
              sum_value = dict_value[0]
              levin_accnt_name = dict_value[1]

            update_str += "%s=%s," % (update_col_lb_dict[i], str(sum_value))
        update_str += "%s='%s'," % ('account_name', str(levin_accnt_name))

        
        update_str = update_str[:-1]
        with connection.cursor() as cursor:
            update_query = """update public.sched_l set %s WHERE cmte_id = '%s' AND report_id = '%s';"""%(update_str, cmte_id, report_id)
            cursor.execute(update_query)
        return Response({'Response':'Success'}, status= status.HTTP_200_OK)
    except Exception as e:
        return Response({'Response':'Failed', 'Message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


    
