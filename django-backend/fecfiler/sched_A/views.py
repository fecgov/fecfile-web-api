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
from datetime import datetime
from django.conf import settings
from fecfiler.core.views import get_entities, put_entities, post_entities, remove_entities, undo_delete_entities, delete_entities, date_format, NoOPError


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
        transaction_type_list = ["SA", ]
        transaction_type = transaction_id[0:2]
        if not (transaction_type in transaction_type_list):
            raise Exception('The Transaction ID: {} is not in specified format'.format(transaction_id))
    except Exception:
        raise 
        
"""
**************************************************** FUNCTIONS - SCHED A TRANSACTION *************************************************************
"""
def post_sql_schedA(cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description):

    try:
        with connection.cursor() as cursor:
            # Insert data into Reports table
            cursor.execute("""INSERT INTO public.sched_a (cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",[cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, datetime.now()])
    except Exception:
        raise

def get_list_all_schedA(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET all rows from Reports table
            query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date
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
            # GET single row from Reports table
            query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date
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

def put_sql_schedA(cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description):

    try:
        with connection.cursor() as cursor:
            # Insert data into Reports table
            cursor.execute("""UPDATE public.sched_a SET line_number = %s, transaction_type = %s, back_ref_transaction_id = %s, back_ref_sched_name = %s, entity_id = %s, contribution_date = %s, contribution_amount = %s, purpose_description = %s, memo_code = %s, memo_text = %s, election_code = %s, election_other_description = %s WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", 
                [line_number, transaction_type, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, transaction_id, report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Transaction ID: {} does not exist in Reports table'.format(transaction_id))
    except Exception:
        raise

def delete_sql_schedA(transaction_id, report_id, cmte_id):

    try:
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from Reports table
            # cursor.execute("""UPDATE public.reports SET delete_ind = 'Y', last_update_date = %s WHERE report_id = '""" + report_id + """' AND cmte_id = '""" + cmte_id + """' AND delete_ind is distinct from 'Y'""", (datetime.now()))
            cursor.execute("""UPDATE public.sched_a SET delete_ind = 'Y' WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [transaction_id, report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception('The Transaction ID: {} is either already deleted or does not exist in Reports table'.format(transaction_id))
    except Exception:
        raise  
"""
**************************************************** API FUNCTIONS - SCHED A TRANSACTION *************************************************************
"""
def post_schedA(datum):
    try:
        if 'entity_id' in datum:
            get_data = {
                'cmte_id': datum.get('cmte_id'),
                'entity_id': datum.get('entity_id')
            }
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
        else:
            entity_data = post_entities(datum)
        #print(entity_data)
        entity_id = entity_data.get('entity_id')
        trans_char = "SA"
        transaction_id = get_next_transaction_id(trans_char)
        datum['transaction_id'] = transaction_id
        try:
            post_sql_schedA(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), datum.get('purpose_description'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'))
            output = get_schedA(datum)
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
        return output[0]
    except:
        raise

def get_schedA(data):
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
            forms_obj = get_list_schedA(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedA(report_id, cmte_id)
        return forms_obj

    except:
        raise

def put_schedA(datum):
    try:
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
        #print(entity_data)
        entity_id = entity_data.get('entity_id')
        transaction_id = datum.get('transaction_id')
        check_transaction_id(transaction_id)
        try:
            put_sql_schedA(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), datum.get('purpose_description'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'))
            output = get_schedA(datum)
        except Exception as e:
            print(datum)
            if flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {
                    'cmte_id': datum.get('cmte_id'),
                    'entity_id': entity_id
                }
                remove_entities(get_data)
            raise Exception('The put_sql_schedA function is throwing an error: ' + str(e))
        return output[0]
    except:
        raise

def delete_schedA(data):
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        transaction_id = data.get('transaction_id')
        check_transaction_id(transaction_id)
        delete_sql_schedA(transaction_id, report_id, cmte_id)
    except:
        raise

"""
***************************************************** SCHED A - POST API CALL STARTS HERE **********************************************************
"""
@api_view(['POST','GET','DELETE','PUT'])
def schedA(request):

    if request.method == 'POST':
        try:
            if request.data.get('report_id') in ['',""," ", 'None', 'null']:
                report_id = 0
            else:
                report_id = request.data.get('report_id')
            datum = {
                'report_id': report_id,
                'line_number': request.data.get('line_number'),
                'transaction_type': request.data.get('transaction_type'),
                'back_ref_transaction_id': request.data.get('back_ref_transaction_id'),
                'back_ref_sched_name': request.data.get('back_ref_sched_name'),
                'contribution_date': date_format(request.data.get('contribution_date')),
                'contribution_amount': request.data.get('contribution_amount'),
                'purpose_description': request.data.get('purpose_description'),
                'memo_code': request.data.get('memo_code'),
                'memo_text': request.data.get('memo_text'),
                'election_code': request.data.get('election_code'),
                'election_other_description': request.data.get('election_other_description'),
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
            if 'entity_id' in request.data:
                datum['entity_id'] = request.data.get('entity_id')  
            data = post_schedA(datum)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedA API - POST is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)
        
    """
    *********************************************** SCHED A - GET API CALL STARTS HERE **********************************************************
    """
    #Get records from reports table
    if request.method == 'GET':

        try:
            data = {
            'cmte_id': request.user.username,
            'report_id': request.query_params.get('report_id')
            }
            if 'transaction_id' in request.query_params:
                data['transaction_id'] =  request.query_params.get('transaction_id')
            data = get_schedA(data)
            return JsonResponse(data, status=status.HTTP_200_OK, safe=False)
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
            datum = {
                'transaction_id': request.data.get('transaction_id'),
                'report_id': request.data.get('report_id'),
                'line_number': request.data.get('line_number'),
                'transaction_type': request.data.get('transaction_type'),
                'back_ref_transaction_id': request.data.get('back_ref_transaction_id'),
                'back_ref_sched_name': request.data.get('back_ref_sched_name'),
                'contribution_date': date_format(request.data.get('contribution_date')),
                'contribution_amount': request.data.get('contribution_amount'),
                'purpose_description': request.data.get('purpose_description'),
                'memo_code': request.data.get('memo_code'),
                'memo_text': request.data.get('memo_text'),
                'election_code': request.data.get('election_code'),
                'election_other_description': request.data.get('election_other_description'),
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
            if 'entity_id' in request.data:
                datum['entity_id'] = request.data.get('entity_id')  
            data = put_schedA(datum)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.debug(e)
            return Response("The schedA API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST) 

    """
    ************************************************ SCHED A - DELETE API CALL STARTS HERE **********************************************************
    """
    if request.method == 'DELETE':

        try:
            data = {
                'transaction_id': request.query_params.get('transaction_id'),
                'cmte_id': request.user.username,
                'report_id': request.query_params.get('report_id')
            }
            delete_schedA(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')),status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedA API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
"""
******************************************************************************************************************************
END - SCHEDULE A TRANSACTIONS API - SCHED_A APP
******************************************************************************************************************************
"""
