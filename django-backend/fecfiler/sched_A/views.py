from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
import os
import requests
from django.views.decorators.csrf import csrf_exempt
import logging
from django.db import connection
from django.http import JsonResponse
import datetime
from django.conf import settings
from decimal import Decimal
from fecfiler.core.views import get_entities, put_entities, post_entities, remove_entities, undo_delete_entities, delete_entities, date_format, NoOPError, check_null_value, check_report_id
from fecfiler.sched_B.views import post_schedB, get_schedB, put_schedB, delete_schedB, schedB_sql_dict, get_list_child_schedB, delete_parent_child_link_sql_schedB

# Create your views here.
logger = logging.getLogger(__name__)

"""
********************************************************************************************************************************
SCHEDULE A TRANSACTION API - SCHED_A APP - SPRINT 7 - FNE 552 - BY PRAVEEN JINKA 
********************************************************************************************************************************
"""

"""
**************************************************** FUNCTIONS - TRANSACTION IDS **********************************************************
"""
list_mandatory_fields_schedA = ['report_id', 'cmte_id', 'line_number', 'transaction_type', 'contribution_date', 'contribution_amount']
list_mandatory_fields_aggregate = ['transaction_type']
list_child_schedB = ['16']

def get_next_transaction_id(trans_char):

    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT public.get_next_transaction_id(%s)""", [trans_char])
            transaction_ids = cursor.fetchone()
            transaction_id = transaction_ids[0]
        return transaction_id
    except Exception:
        raise 

def check_transaction_id(transaction_id):

    try:
        transaction_type_list = ["SA",]
        transaction_type = transaction_id[0:2]
        if not (transaction_type in transaction_type_list):
            raise Exception('The Transaction ID: {} is not in the specified format. Transaction IDs start with SA characters'.format(transaction_id))
        return transaction_id
    except Exception:
        raise 

def check_mandatory_fields_SA(data, list_mandatory_fields):
    try:
        error =[]
        for field in list_mandatory_fields:
            if not(field in data and check_null_value(data.get(field))):
                error.append(field)
        if len(error) > 0:
            string = ""
            for x in error:
                string = string + x + ", "
            string = string[0:-2]
            raise Exception('The following mandatory fields are required in order to save data to schedA table: {}'.format(string))
    except:
        raise

def check_decimal(value):

    try:
        check_value = Decimal(value)
        return value
    except Exception as e:
        raise Exception('Invalid Input: Expecting a decimal value like 18.11, 24.07. Input received: {}'.format(value))        
"""
**************************************************** FUNCTIONS - SCHED A TRANSACTION *************************************************************
"""
def post_sql_schedA(cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description):

    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute("""INSERT INTO public.sched_a (cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",[cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, datetime.datetime.now()])
    except Exception:
        raise

def get_list_all_schedA(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET all rows from schedA table
            query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date
                            FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""

            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id])
            for row in cursor.fetchall():
            #forms_obj.append(data_row)
                data_row = list(row)
                schedA_list = data_row[0]
            if schedA_list is None:
                raise NoOPError('The Report id:{} does not have any schedA transactions'.format(report_id))  
            merged_list= []
            for dictA in schedA_list:
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

def get_list_schedA(report_id, cmte_id, transaction_id):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date
                            FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s AND delete_ind is distinct from 'Y'"""
            
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id, transaction_id])

            for row in cursor.fetchall():
            #forms_obj.append(data_row)
                data_row = list(row)
                schedA_list = data_row[0]
            if schedA_list is None:
                raise NoOPError('The transaction id: {} does not exist or is deleted'.format(transaction_id))    
            merged_list= []
            for dictA in schedA_list:
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

def get_list_child_schedA(report_id, cmte_id, transaction_id):

    try:
        with connection.cursor() as cursor:

            # GET child rows from schedA table

            query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date
                            FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s AND delete_ind is distinct from 'Y'"""
            
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id, transaction_id])

            for row in cursor.fetchall():
            #forms_obj.append(data_row)
                data_row = list(row)
                schedA_list = data_row[0]
            merged_list= []
            if not (schedA_list is None):
                for dictA in schedA_list:
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

def put_sql_schedA(cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description):

    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute("""UPDATE public.sched_a SET line_number = %s, transaction_type = %s, back_ref_transaction_id = %s, back_ref_sched_name = %s, entity_id = %s, contribution_date = %s, contribution_amount = %s, purpose_description = %s, memo_code = %s, memo_text = %s, election_code = %s, election_other_description = %s WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", 
                [line_number, transaction_type, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, transaction_id, report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Transaction ID: {} does not exist in schedA table'.format(transaction_id))
    except Exception:
        raise

def delete_sql_schedA(transaction_id, report_id, cmte_id):

    try:
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from Sched_A table
            cursor.execute("""UPDATE public.sched_a SET delete_ind = 'Y' WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [transaction_id, report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Transaction ID: {} is either already deleted or does not exist in schedA table'.format(transaction_id))
    except Exception:
        raise

def delete_parent_child_link_sql_schedA(transaction_id, report_id, cmte_id):

    try:
        with connection.cursor() as cursor:

            # UPDATE back_ref_transaction_id value to null in sched_a table
            value = None
            cursor.execute("""UPDATE public.sched_a SET back_ref_transaction_id = %s WHERE back_ref_transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [value, transaction_id, report_id, cmte_id])

    except Exception:
        raise

def find_form_type(report_id, cmte_id):
    try:
        #handling cases where report_id is reported as 0
        if report_id in ["0", '0', 0]:
            return "F3X"
        #end of error handling    
        with connection.cursor() as cursor:
            cursor.execute("""SELECT form_type FROM public.reports WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [report_id, cmte_id])
            form_types = cursor.fetchone()
        if (cursor.rowcount == 0):
            raise Exception('The Report ID: {} is either already deleted or does not exist in reports table'.format(report_id))
        else:
            return form_types[0]
    except Exception as e:
        raise Exception('The form_type function is throwing an error:' + str(e))

def find_aggregate_date(form_type, contribution_date):
    try:
        aggregate_start_date = None
        if form_type == "F3X":
            year = contribution_date.year
            aggregate_start_date = datetime.date(year, 1, 1)
            aggregate_end_date = datetime.date(year, 12, 31)
        return aggregate_start_date, aggregate_end_date
    except Exception as e:
        raise Exception('The aggregate_start_date function is throwing an error: ' + str(e))

def func_aggregate_amount(aggregate_start_date, aggregate_end_date, transaction_type, entity_id, cmte_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT COALESCE(SUM(contribution_amount),0) FROM public.sched_a WHERE entity_id = %s AND transaction_type = %s AND cmte_id = %s AND contribution_date >= %s AND contribution_date <= %s AND delete_ind is distinct FROM 'Y'""", [entity_id, transaction_type, cmte_id, aggregate_start_date, aggregate_end_date])
            aggregate_amt = cursor.fetchone()[0]
        return aggregate_amt
    except Exception as  e:
        raise Exception('The aggregate_amount function is throwing an error: ' + str(e))

def list_all_transactions_entity(aggregate_start_date, aggregate_end_date, transaction_type, entity_id, cmte_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT contribution_amount, transaction_id, report_id, line_number, contribution_date FROM public.sched_a WHERE entity_id = %s AND transaction_type = %s AND cmte_id = %s AND contribution_date >= %s AND contribution_date <= %s AND delete_ind is distinct FROM 'Y' ORDER BY contribution_date ASC, create_date ASC""", [entity_id, transaction_type, cmte_id, aggregate_start_date, aggregate_end_date])
            transactions_list = cursor.fetchall()
        return transactions_list
    except Exception as  e:
        raise Exception('The list_all_transactions_entity function is throwing an error: ' + str(e))

def update_linenumber_aggamt_transactions_SA(contribution_date, transaction_type, entity_id, cmte_id, report_id):
    try:
        itemization_transaction_type_list = ["15",]
        itemization_value = 200
        itemized_transaction_list = []
        unitemized_transaction_list = []
        if transaction_type in itemization_transaction_type_list:
            form_type = find_form_type(report_id, cmte_id)
            aggregate_start_date, aggregate_end_date = find_aggregate_date(form_type, contribution_date)
            transactions_list = list_all_transactions_entity(aggregate_start_date, aggregate_end_date, transaction_type, entity_id, cmte_id)
            aggregate_amount = 0
            for transaction in transactions_list:
                aggregate_amount = aggregate_amount + transaction[0]
                if str(report_id) == str(transaction[2]):
                    if contribution_date <= transaction[4]:
                        if aggregate_amount <= itemization_value:
                            put_sql_linenumber_schedA(cmte_id, report_id, "11AII", transaction[1], entity_id, aggregate_amount)
                        else:
                            put_sql_linenumber_schedA(cmte_id, report_id, "11AI", transaction[1], entity_id, aggregate_amount)
    except Exception as  e:
        raise Exception('The update_linenumber_aggamt_transactions_SA function is throwing an error: ' + str(e))

def put_sql_linenumber_schedA(cmte_id, report_id, line_number, transaction_id, entity_id, aggregate_amount):

    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute("""UPDATE public.sched_a SET line_number = %s, aggregate_amt = %s WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s AND entity_id = %s AND delete_ind is distinct from 'Y'""", 
                [line_number, aggregate_amount, transaction_id, report_id, cmte_id, entity_id])
            if (cursor.rowcount == 0):
                raise Exception('put_sql_linenumber_schedA function: The Transaction ID: {} does not exist in schedA table'.format(transaction_id))
    except Exception:
        raise

# def disclosure_rules(line_number, report_id, transaction_type, contribution_amount, contribution_date, entity_id, cmte_id):
#     try:
#         itemization_transaction_type_list = ["15",]
#         # itemization value above (> and not >=) which transactions become itemized for each entity
#         itemization_value = 200
#         unitemized_line_number = "11AII"
#         if transaction_type in itemization_transaction_type_list:
#             form_type = find_form_type(report_id, cmte_id)
#             year = contribution_date.year
#             aggregate_start_date = datetime.date(year, 1, 1)
#             aggregate_amt = func_aggregate_amount(aggregate_start_date, contribution_date, transaction_type, entity_id, cmte_id)
#         else:
#             aggregate_amt = itemization_value + 1
#         total_amt = aggregate_amt + Decimal(contribution_amount)
#         if total_amt <= itemization_value:
#             return unitemized_line_number
#         else:
#             return line_number 
#     except Exception as e:
#         raise Exception('The disclosure_rules function is throwing an error: ' + str(e))
"""
**************************************************** API FUNCTIONS - SCHED A TRANSACTION *************************************************************
"""
def post_schedA(datum):
    try:
        check_mandatory_fields_SA(datum, list_mandatory_fields_schedA)
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
        #datum['line_number'] = disclosure_rules(datum.get('line_number'), datum.get('report_id'), datum.get('transaction_type'), datum.get('contribution_amount'), datum.get('contribution_date'), entity_id, datum.get('cmte_id'))
        trans_char = "SA"
        transaction_id = get_next_transaction_id(trans_char)
        datum['transaction_id'] = transaction_id
        try:
            post_sql_schedA(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), datum.get('purpose_description'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'))
        except Exception as e:
            if 'entity_id' in datum:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {
                    'cmte_id': datum.get(cmte_id),
                    'entity_id': entity_id
                }
                remove_entities(get_data)
            raise Exception('The post_sql_schedA function is throwing an error: ' + str(e))
        update_linenumber_aggamt_transactions_SA(datum.get('contribution_date'), datum.get('transaction_type'), entity_id, datum.get('cmte_id'), datum.get('report_id'))
        return datum
    except:
        raise

def get_schedA(data):
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        flag = False
        if 'transaction_id' in data:
            try:
                transaction_id = check_transaction_id(data.get('transaction_id'))
                flag = True
            except Exception:
                flag = False

        if flag:
            forms_obj = get_list_schedA(report_id, cmte_id, transaction_id)
            childA_forms_obj = get_list_child_schedA(report_id, cmte_id, transaction_id)
            childB_forms_obj = get_list_child_schedB(report_id, cmte_id, transaction_id)
            child_forms_obj = childA_forms_obj + childB_forms_obj
            if len(child_forms_obj) > 0:
                forms_obj[0]['child'] = child_forms_obj
        else:
            forms_obj = get_list_all_schedA(report_id, cmte_id)
        return forms_obj

    except:
        raise

def put_schedA(datum):
    try:
        check_mandatory_fields_SA(datum, list_mandatory_fields_schedA)
        transaction_id = check_transaction_id(datum.get('transaction_id'))
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
            put_sql_schedA(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), datum.get('purpose_description'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'))
        except Exception as e:
            if flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {
                    'cmte_id': datum.get('cmte_id'),
                    'entity_id': entity_id
                }
                remove_entities(get_data)
            raise Exception('The put_sql_schedA function is throwing an error: ' + str(e))
        update_linenumber_aggamt_transactions_SA(datum.get('contribution_date'), datum.get('transaction_type'), entity_id, datum.get('cmte_id'), datum.get('report_id'))
        return datum
    except:
        raise

def delete_schedA(data):
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        transaction_id = check_transaction_id(data.get('transaction_id'))
        datum = get_list_schedA(report_id, cmte_id, transaction_id)[0]
        delete_sql_schedA(transaction_id, report_id, cmte_id)
        delete_parent_child_link_sql_schedA(transaction_id, report_id, cmte_id)
        delete_parent_child_link_sql_schedB(transaction_id, report_id, cmte_id)
        update_linenumber_aggamt_transactions_SA(datetime.datetime.strptime(datum.get('contribution_date'), '%Y-%m-%d').date(), datum.get('transaction_type'), datum.get('entity_id'), datum.get('cmte_id'), datum.get('report_id'))
    except:
        raise

def check_type_list(data):
    try:
        if not type(data) is list:
            raise Exception('The child transactions have to be sent in as an array or list. Input received: {}'.format(data))
        else:
            return data
    except:
        raise

def schedA_sql_dict(data):
    try:
        datum = {
            'line_number': data.get('line_number'),
            'transaction_type': data.get('transaction_type'),
            'back_ref_sched_name': data.get('back_ref_sched_name'),
            'contribution_date': date_format(data.get('contribution_date')),
            'contribution_amount': check_decimal(data.get('contribution_amount')),
            'purpose_description': data.get('purpose_description'),
            'memo_code': data.get('memo_code'),
            'memo_text': data.get('memo_text'),
            'election_code': data.get('election_code'),
            'election_other_description': data.get('election_other_description'),
            'entity_type': data.get('entity_type'),
            'entity_name': data.get('entity_name'),
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'middle_name': data.get('middle_name'),
            'preffix': data.get('prefix'),
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
***************************************************** SCHED A - POST API CALL STARTS HERE **********************************************************
"""
@api_view(['POST','GET','DELETE','PUT'])
def schedA(request):

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
            datum = schedA_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                datum['entity_id'] = request.data.get('entity_id')
            if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(request.data.get('transaction_id'))
                data = put_schedA(datum)
            else:
                data = post_schedA(datum)
            # Associating child transactions to parent and storing them to DB
            if 'child' in request.data:
                children = check_type_list(request.data.get('child'))
                if len(children) > 0:
                    child_output=[]
                    for child in children:
                        transaction_type = child.get('transaction_type')
                        if transaction_type in list_child_schedB:
                            child_datum =schedB_sql_dict(child)
                        else:
                            child_datum = schedA_sql_dict(child)

                        child_datum['back_ref_transaction_id'] = data.get('transaction_id')
                        child_datum['report_id'] = report_id
                        child_datum['cmte_id'] = cmte_id
                        if 'entity_id' in child and check_null_value(child.get('entity_id')):
                            child_datum['entity_id'] = child.get('entity_id')
                        if 'transaction_id' in child and check_null_value(child.get('transaction_id')):
                            child_datum['transaction_id'] = check_transaction_id(child.get('transaction_id'))
                            if transaction_type in list_child_schedB:
                                child_data = put_schedB(child_datum)
                            else:
                                child_data = put_schedA(child_datum)
                        else:
                            if transaction_type in list_child_schedB:
                                child_data = post_schedB(child_datum)
                            else:
                                child_data = post_schedA(child_datum)
            output = get_schedA(data)                                           
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedA API - POST is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)
        
    """
    *********************************************** SCHED A - GET API CALL STARTS HERE **********************************************************
    """
    #Get records from schedA table
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
            datum = get_schedA(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedA API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    """
    ************************************************* SCHED A - PUT API CALL STARTS HERE **********************************************************
    """
    if request.method == 'PUT':

        try:
            if request.data.get('transaction_type') in list_child_schedB:
                datum = schedB_sql_dict(request.data)
            else:
                datum = schedA_sql_dict(request.data)

            if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
                datum['transaction_id'] = request.data.get('transaction_id')
            else:
                raise Exception('Missing Input: transaction_id is mandatory')

            if not('report_id' in request.data):
                raise Exception ('Missing Input: Report_id is mandatory')
            #handling null,none value of report_id
            if not (check_null_value(request.data.get('report_id'))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get('report_id'))
            #end of handling
            datum['report_id'] = report_id
            datum['cmte_id'] = request.user.username

            if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                datum['entity_id'] = request.data.get('entity_id')
            if request.data.get('transaction_type') in list_child_schedB:
                data = put_schedB(datum)
                output = get_schedB(data)
            else:    
                data = put_schedA(datum)
                output = get_schedA(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)            
        except Exception as e:
            logger.debug(e)
            return Response("The schedA API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST) 

    """
    ************************************************ SCHED A - DELETE API CALL STARTS HERE **********************************************************
    """
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
            delete_schedA(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')),status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedA API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
END - SCHEDULE A TRANSACTIONS API - SCHED_A APP
******************************************************************************************************************************
"""
"""
********************************************************************************************************************************
AGGREGATE AMOUNT API - SCHED_A APP - SPRINT 11 - FNE 871 - BY PRAVEEN JINKA 
********************************************************************************************************************************
"""
@api_view(['POST'])
def aggregate_amount(request):

    if request.method == 'POST':
        try:
            check_mandatory_fields_SA(request.data, list_mandatory_fields_aggregate)
            cmte_id = request.user.username
            if not('report_id' in request.data):
                raise Exception ('Missing Input: Report_id is mandatory')
            #handling null,none value of report_id
            if check_null_value(request.data.get('report_id')):
                report_id = check_report_id(request.data.get('report_id'))
            else:
                report_id = "0"
            #end of handling
            if report_id == "0":
                aggregate_date = datetime.datetime.today()
            else:
                aggregate_date = report_end_date(report_id, cmte_id)
            transaction_type = request.data.get('transaction_type')
            if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                entity_id = request.data.get('entity_id')
            else:
                entity_id = "0"
            if 'contribution_amount' in request.data and check_null_value(request.data.get('contribution_amount')):
                contribution_amount = check_decimal(request.data.get('contribution_amount'))
            else:
                contribution_amount = "0"
            form_type = find_form_type(report_id, cmte_id)
            aggregate_start_date, aggregate_end_date = find_aggregate_date(form_type, aggregate_date)
            aggregate_amt = func_aggregate_amount(aggregate_start_date, aggregate_end_date, transaction_type, entity_id, cmte_id)
            total_amt = aggregate_amt + Decimal(contribution_amount)
            return JsonResponse({"aggregate_amount":total_amt}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response('The aggregate_amount API is throwing an error: ' + str(e), status=status.HTTP_400_BAD_REQUEST)

def report_end_date(report_id, cmte_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT cvg_end_date FROM public.reports WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct FROM 'Y'""", [report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Report ID: {} does not exist in reports table'.format(report_id))
            cvg_end_date = cursor.fetchone()[0]
        return cvg_end_date
    except Exception as e:
        raise Exception('The report_end_date function is throwing an error: ' + str(e))

"""
******************************************************************************************************************************
END - AGGREGATE AMOUNT API - SCHED_A APP
******************************************************************************************************************************
"""