from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
import datetime
import os
import requests
from django.views.decorators.csrf import csrf_exempt
import logging
from django.db import connection
from django.http import JsonResponse
from django.conf import settings
from fecfiler.core.views import get_entities, put_entities, post_entities, remove_entities, undo_delete_entities, delete_entities, date_format, NoOPError, check_null_value, check_report_id
from fecfiler.sched_A.views import get_next_transaction_id, check_transaction_id, check_type_list, check_decimal

# Create your views here.
logger = logging.getLogger(__name__)

"""
********************************************************************************************************************************
SCHEDULE B TRANSACTION API - SCHED_B APP - SPRINT 10 - FNE 708 - BY PRAVEEN JINKA 
********************************************************************************************************************************
"""
"""
**************************************************** FUNCTIONS - MANDATORY FIELDS CHECK **********************************************************
"""

def check_mandatory_fields_schedB(data):
    try:
        list_mandatory_fields_schedB = ['report_id', 'expenditure_date', 'expenditure_amount', 'semi_annual_refund_bundled_amount', 'cmte_id', 'line_number', 'transaction_type', ]
        error =[]
        for field in list_mandatory_fields_schedB:
            if not(field in data and check_null_value(data.get(field))):
                error.append(field)
        if len(error) > 0:
            string = ""
            for x in error:
                string = string + x + ", "
            string = string[0:-2]
            raise Exception('The following mandatory fields are required in order to save data to schedB table: {}'.format(string))
    except:
        raise        
"""
**************************************************** FUNCTIONS - SCHED B TRANSACTION - work to be done*************************************************************
"""
def post_sql_schedB(cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account):

    try:
        with connection.cursor() as cursor:
            # Insert data into schedB table
            cursor.execute("""INSERT INTO public.sched_b (cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",[cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account])
    except Exception:
        raise

def get_list_all_schedB(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET all rows from schedB table
            query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account, create_date
                            FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""

            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id])
            for row in cursor.fetchall():
                data_row = list(row)
                schedB_list = data_row[0]
            if schedB_list is None:
                raise NoOPError('The Report id:{} does not have any schedB transactions'.format(report_id))  
            merged_list= []
            for dictB in schedB_list:
                entity_id = dictB.get('entity_id')
                data = {
                    'entity_id': entity_id,
                    'cmte_id': cmte_id
                }
                entity_list = get_entities(data)
                dictEntity = entity_list[0]
                merged_dict = {**dictB, **dictEntity}
                merged_list.append(merged_dict)                
        return merged_list
    except Exception:
        raise

def get_list_schedB(report_id, cmte_id, transaction_id):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedB table
            query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account, create_date
                            FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s AND delete_ind is distinct from 'Y'"""
            
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id, transaction_id])

            for row in cursor.fetchall():
                data_row = list(row)
                schedB_list = data_row[0]
            if schedB_list is None:
                raise NoOPError('The transaction id: {} does not exist or is deleted'.format(transaction_id))    
            merged_list= []
            for dictB in schedB_list:
                entity_id = dictB.get('entity_id')
                data = {
                    'entity_id': entity_id,
                    'cmte_id': cmte_id
                }
                entity_list = get_entities(data)
                dictEntity = entity_list[0]
                merged_dict = {**dictB, **dictEntity}
                merged_list.append(merged_dict)
        return merged_list
    except Exception:
        raise

def get_list_child_schedB(report_id, cmte_id, transaction_id):

    try:
        with connection.cursor() as cursor:
            # GET child rows from schedB table
            query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account, create_date
                            FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s AND delete_ind is distinct from 'Y'"""
            
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id, transaction_id])

            for row in cursor.fetchall():
                data_row = list(row)
                schedB_list = data_row[0]
            merged_list= []
            if not (schedB_list is None):
                for dictB in schedB_list:
                    entity_id = dictB.get('entity_id')
                    data = {
                        'entity_id': entity_id,
                        'cmte_id': cmte_id
                    }
                    entity_list = get_entities(data)
                    dictEntity = entity_list[0]
                    merged_dict = {**dictB, **dictEntity}
                    merged_list.append(merged_dict)
        return merged_list
    except Exception:
        raise

def put_sql_schedB(cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account):

    try:
        with connection.cursor() as cursor:
            # Insert data into schedB table
            cursor.execute("""UPDATE public.sched_b SET line_number = %s, transaction_type = %s, back_ref_transaction_id = %s, back_ref_sched_name = %s, entity_id = %s, expenditure_date = %s, expenditure_amount = %s, semi_annual_refund_bundled_amount = %s, expenditure_purpose = %s, category_code = %s, memo_code = %s, memo_text = %s, election_code = %s, election_other_description = %s, beneficiary_cmte_id = %s, beneficiary_cand_id = %s, other_name = %s, other_street_1 = %s, other_street_2 = %s, other_city = %s, other_state = %s, other_zip = %s, nc_soft_account = %s WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", 
                [line_number, transaction_type, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account, transaction_id, report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Transaction ID: {} does not exist in schedB table'.format(transaction_id))
    except Exception:
        raise

def delete_sql_schedB(transaction_id, report_id, cmte_id):

    try:
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from Sched_B table
            cursor.execute("""UPDATE public.sched_b SET delete_ind = 'Y' WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [transaction_id, report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Transaction ID: {} is either already deleted or does not exist in schedB table'.format(transaction_id))
    except Exception:
        raise

def delete_parent_child_link_sql_schedB(transaction_id, report_id, cmte_id):

    try:
        with connection.cursor() as cursor:

            # UPDATE back_ref_transaction_id value to null in sched_b table
            value = None
            cursor.execute("""UPDATE public.sched_b SET back_ref_transaction_id = %s WHERE back_ref_transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [value, transaction_id, report_id, cmte_id])
    except Exception:
        raise  
"""
**************************************************** API FUNCTIONS - SCHED B TRANSACTION *************************************************************
"""
def post_schedB(datum):
    try:
        check_mandatory_fields_schedB(datum)
        if 'entity_id' in datum:
            get_data = {
                'cmte_id': datum.get('cmte_id'),
                'entity_id': datum.get('entity_id')
            }
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
        else:
            entity_data = post_entities(datum)
        entity_id = entity_data.get('entity_id')
        datum['entity_id'] = entity_id
        trans_char = "SB"
        transaction_id = get_next_transaction_id(trans_char)
        datum['transaction_id'] = transaction_id
        try:
            post_sql_schedB(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('expenditure_date'), datum.get('expenditure_amount'), datum.get('semi_annual_refund_bundled_amount'), datum.get('expenditure_purpose'), datum.get('category_code'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'), datum.get('beneficiary_cmte_id'), datum.get('beneficiary_cand_id'), datum.get('other_name'), datum.get('other_street_1'), datum.get('other_street_2'), datum.get('other_city'), datum.get('other_state'), datum.get('other_zip'), datum.get('nc_soft_account'))
        except Exception as e:
            if 'entity_id' in datum:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {
                    'cmte_id': datum.get(cmte_id),
                    'entity_id': entity_id
                }
                remove_entities(get_data)
            raise Exception('The post_sql_schedB function is throwing an error: ' + str(e))
        return datum
    except:
        raise

def get_schedB(data):
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        flag = False
        if 'transaction_id' in data:
            try:
                transaction_id = data.get('transaction_id')
                check_transaction_id(transaction_id)
                flag = True
            except Exception:
                flag = False

        if flag:
            forms_obj = get_list_schedB(report_id, cmte_id, transaction_id)
            child_forms_obj = get_list_child_schedB(report_id, cmte_id, transaction_id)
            if len(child_forms_obj) > 0:
                forms_obj[0]['child'] = child_forms_obj
        else:
            forms_obj = get_list_all_schedB(report_id, cmte_id)
        return forms_obj

    except:
        raise

def put_schedB(datum):
    try:
        check_mandatory_fields_schedB(datum)
        transaction_id = datum.get('transaction_id')
        check_transaction_id(transaction_id)
        flag = False
        if 'entity_id' in datum:
            flag = True
            get_data = {
                'cmte_id': datum.get('cmte_id'),
                'entity_id': datum.get('entity_id')
            }
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
        else:
            entity_data = post_entities(datum)
        entity_id = entity_data.get('entity_id')
        datum['entity_id'] = entity_id
        try:
        	put_sql_schedB(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('expenditure_date'), datum.get('expenditure_amount'), datum.get('semi_annual_refund_bundled_amount'), datum.get('expenditure_purpose'), datum.get('category_code'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'), datum.get('beneficiary_cmte_id'), datum.get('beneficiary_cand_id'), datum.get('other_name'), datum.get('other_street_1'), datum.get('other_street_2'), datum.get('other_city'), datum.get('other_state'), datum.get('other_zip'), datum.get('nc_soft_account'))
        except Exception as e:
            if flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {
                    'cmte_id': datum.get('cmte_id'),
                    'entity_id': entity_id
                }
                remove_entities(get_data)
            raise Exception('The put_sql_schedB function is throwing an error: ' + str(e))
        return datum
    except:
        raise

def delete_schedB(data):
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        transaction_id = data.get('transaction_id')
        check_transaction_id(transaction_id)
        delete_sql_schedB(transaction_id, report_id, cmte_id)
        delete_parent_child_link_sql_schedB(transaction_id, report_id, cmte_id)
    except:
        raise

def schedB_sql_dict(data):
    try:
        datum = {
            'line_number': data.get('line_number'),
            'transaction_type': data.get('transaction_type'),
            'back_ref_sched_name': data.get('back_ref_sched_name'),
            'expenditure_date': date_format(data.get('expenditure_date')),
            'expenditure_amount': check_decimal(data.get('expenditure_amount')),
            'semi_annual_refund_bundled_amount': check_decimal(data.get('semi_annual_refund_bundled_amount')),
            'expenditure_purpose': data.get('expenditure_purpose'),
            'category_code': data.get('category_code'),
            'memo_code': data.get('memo_code'),
            'memo_text': data.get('memo_text'),
            'election_code': data.get('election_code'),
            'election_other_description': data.get('election_other_description'),
            'beneficiary_cmte_id': data.get('beneficiary_cmte_id'),
            'beneficiary_cand_id': data.get('beneficiary_cand_id'),
            'other_name': data.get('other_name'),
            'other_street_1': data.get('other_street_1'),
            'other_street_2': data.get('other_street_2'),
            'other_city': data.get('other_city'),
            'other_state': data.get('other_state'),
            'other_zip': data.get('other_zip'),
            'nc_soft_account': data.get('nc_soft_account'),
            'entity_type': data.get('entity_type'),
            'entity_name': data.get('entity_name'),
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'middle_name': data.get('middle_name'),
            'preffix': data.get('preffix'),
            'suffix': data.get('suffix'),
            'street_1': data.get('street_1'),
            'street_2': data.get('street_2'),
            'city': data.get('city'),
            'state': data.get('state'),
            'zip_code': data.get('zip_code'),
            'occupation': data.get('occupation'),
            'employer': data.get('employer'),
            'ref_cand_cmte_id': data.get('ref_cand_cmte_id'),
            'back_ref_transaction_id': data.get('back_ref_transaction_id'),
        }
        return datum
    except:
        raise
"""
***************************************************** SCHED B - POST API CALL STARTS HERE **********************************************************
"""
@api_view(['POST','GET','DELETE','PUT'])
def schedB(request):
    if request.method == 'POST':
        try:
            cmte_id = request.user.username
            if not('report_id' in request.data):
                raise Exception ('Missing Input: Report_id is mandatory')
            #handling null,none value of report_id
            if not (check_null_value(request.data.get('report_id'))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get('report_id'))
            #end of handling
            datum = schedB_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                datum['entity_id'] = request.data.get('entity_id')
            if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(request.data.get('transaction_id'))
                data = put_schedB(datum)
            else:
                data = post_schedB(datum)

            # Associating child transactions to parent and storing them to DB
            if 'child' in request.data:
                children = check_type_list(request.data.get('child'))
                if len(children) > 0:
                    child_output=[]
                    for child in children:
                        child_datum = schedB_sql_dict(child)
                        child_datum['back_ref_transaction_id'] = data.get('transaction_id')
                        child_datum['report_id'] = report_id
                        child_datum['cmte_id'] = cmte_id
                        if 'entity_id' in child and check_null_value(child.get('entity_id')):
                            child_datum['entity_id'] = child.get('entity_id')
                        if 'transaction_id' in child and check_null_value(child.get('transaction_id')):
                            child_datum['transaction_id'] = check_transaction_id(child.get('transaction_id'))
                            child_data = put_schedB(child_datum)
                        else:
                            child_data = post_schedB(child_datum)                   
            output = get_schedB(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedB API - POST is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)
        
    """
    *********************************************** SCHED B - GET API CALL STARTS HERE **********************************************************
    """
    #Get records from schedB table
    if request.method == 'GET':

        try:
            data = {
            'cmte_id': request.user.username
            }
            if 'report_id' in request.query_params and check_null_value(request.query_params.get('report_id')):
                data['report_id'] = check_report_id(request.query_params.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            if 'transaction_id' in request.query_params and check_null_value(request.query_params.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(request.query_params.get('transaction_id'))
            datum = get_schedB(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedB API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    """
    ************************************************* SCHED B - PUT API CALL STARTS HERE **********************************************************
    """
    #Modify a single record from schedB table
    if request.method == 'PUT':

        try:
            datum = schedB_sql_dict(request.data)

            if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(request.data.get('transaction_id'))
            else:
                raise Exception('Missing Input: transaction_id is mandatory')

            if not('report_id' in request.data):
                raise Exception ('Missing Input: Report_id is mandatory')
            #handling null,none value of report_id
            if not (check_null_value(request.data.get('report_id'))):
                report_id = 0
            else:
                report_id = check_report_id(request.data.get('report_id'))
            #end of handling
            datum['report_id'] = report_id
            datum['back_ref_transaction_id'] = request.data.get('back_ref_transaction_id')
            datum['cmte_id'] = request.user.username

            if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                datum['entity_id'] = request.data.get('entity_id')

            data = put_schedB(datum)
            output = get_schedB(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.debug(e)
            return Response("The schedB API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST) 

    """
    ************************************************ SCHED B - DELETE API CALL STARTS HERE **********************************************************
    """
    #Delete a single record from schedB table
    if request.method == 'DELETE':

        try:
            data = {
            'cmte_id': request.user.username
            }
            if 'report_id' in request.query_params and check_null_value(request.query_params.get('report_id')):
                data['report_id'] = check_report_id(request.query_params.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            if 'transaction_id' in request.query_params and check_null_value(request.query_params.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(request.query_params.get('transaction_id'))
            else:
                raise Exception('Missing Input: transaction_id is mandatory')
            delete_schedB(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')),status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedB API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
END - SCHEDULE B TRANSACTIONS API - SCHED_B APP
******************************************************************************************************************************
"""