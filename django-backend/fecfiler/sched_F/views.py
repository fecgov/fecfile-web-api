from django.shortcuts import render
import datetime
import json
import logging
import os
from decimal import Decimal

import requests
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from fecfiler.core.views import (NoOPError, check_null_value, check_report_id,
                                 date_format, delete_entities, get_entities,
                                 post_entities, put_entities, remove_entities,
                                 undo_delete_entities)
from fecfiler.core.transaction_util import transaction_exists                                 
from fecfiler.sched_A.views import get_next_transaction_id
from fecfiler.sched_D.views import do_transaction


# TODO: still need to add line_number and transaction_code to sched_f

# Create your views here.
logger = logging.getLogger(__name__)

MANDATORY_FIELDS_SCHED_F = ['cmte_id', 'report_id', 'transaction_id']

# need to verify those child memo transactions have:
# 1. back_ref_transaction_id 
# 2. parent transaction exist in the db
MEMO_SCHED_F_TRANSACTIONS = [
    'COEXP_CC_PAY_MEMO',
    'COEXP_STAF_REIM_MEMO',
    'COEXP_PMT_PROL_MEMO',
]

def parent_transaction_exists(tran_id, sched_tp):
    """
    check if parent transaction exists
    """
    return transaction_exists(tran_id, sched_tp)


def validate_parent_transaction_exist(data):
    """
    validate parent transaction exsit if saving a child transaction
    """
    if data.get("transaction_type_identifier") in MEMO_SCHED_F_TRANSACTIONS:
        if not data.get("back_ref_transaction_id"):
            raise Exception("Error: parent transaction id missing.")
        elif not parent_transaction_exists(
            data.get("back_ref_transaction_id"),
            'sched_f'
        ):
            raise Exception("Error: parent transaction not found.")
        else:
            pass

def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SF"):
        raise Exception(
            'The Transaction ID: {} is not in the specified format.' +
            'Transaction IDs start with SF characters'.format(transaction_id))
    return transaction_id


def check_mandatory_fields_SF(data):
    """
    validate mandatory fields for sched_e item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_F:
            if not(field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                'The following mandatory fields are required in order to save data to schedF table: {}'.format(','.join(errors)))
    except:
        raise


def schedF_sql_dict(data):
    """
    filter out valid fileds for sched_F

    """
    validate_parent_transaction_exist(data)
    valid_fields = [

            'transaction_type_identifier',
            'transaction_id', 
            'back_ref_transaction_id',
            'back_ref_sched_name',
            'coordinated_exp_ind',
            'designating_cmte_id',
            'designating_cmte_name',
            'subordinate_cmte_id',
            'subordinate_cmte_name',
            'subordinate_cmte_street_1',
            'subordinate_cmte_street_2',
            'subordinate_cmte_city',
            'subordinate_cmte_state',
            'subordinate_cmte_zip',
            'payee_entity_id',
            'expenditure_date',
            'expenditure_amount ',
            'aggregate_general_elec_exp ',
            'purpose',
            'category_code',
            'payee_cmte_id',
            'payee_cand_id',
            'payee_cand_last_name',
            'payee_cand_fist_name',
            'payee_cand_middle_name',
            'payee_cand_prefix',
            'payee_cand_suffix',
            'payee_cand_office',
            'payee_cand_state',
            'payee_cand_district',
            'memo_code',
            'memo_text',
            
    ]
    try:
        return {k: v for k, v in data.items() if k in valid_fields}
    except:
        raise Exception('invalid request data.')


def put_schedF(data):
    """
    update sched_F item
    here we are assuming entity_id are always referencing something already in our DB
    """
    try:
        check_mandatory_fields_SF(data)
        #check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedF(data)
        except Exception as e:
            raise Exception(
                'The put_sql_schedF function is throwing an error: ' + str(e))
        return data
    except:
        raise


def put_sql_schedF(data):
    """
    update a schedule_f item                    
            
    """
    _sql = """UPDATE public.sched_f
              SET transaction_type_identifier= %s, 
                  back_ref_transaction_id= %s,
                  back_ref_sched_name= %s,
                  coordinated_exp_ind= %s,
                  designating_cmte_id= %s,
                  designating_cmte_name= %s,
                  subordinate_cmte_id= %s,
                  subordinate_cmte_name= %s,
                  subordinate_cmte_street_1= %s,
                  subordinate_cmte_street_2= %s,
                  subordinate_cmte_city= %s,
                  subordinate_cmte_state= %s,
                  subordinate_cmte_zip= %s,
                  payee_entity_id= %s,
                  expenditure_date= %s,
                  expenditure_amount = %s,
                  aggregate_general_elec_exp= %s,
                  purpose= %s,
                  category_code= %s,
                  payee_cmte_id= %s,
                  payee_cand_id= %s,
                  payee_cand_last_name= %s,
                  payee_cand_fist_name= %s,
                  payee_cand_middle_name= %s,
                  payee_cand_prefix= %s,
                  payee_cand_suffix= %s,
                  payee_cand_office= %s,
                  payee_cand_state= %s,
                  payee_cand_district= %s,
                  memo_code= %s,
                  memo_text= %s,
                  create_date= %s,
                  last_update_date= %s,
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (  
           
            data.get('transaction_type_identifier', ''),
            data.get('back_ref_transaction_id', ''),
            data.get('back_ref_sched_name', ''),
            data.get('coordinated_exp_ind', ''),
            data.get('designating_cmte_id', ''),
            data.get('designating_cmte_name', ''),
            data.get('subordinate_cmte_id', ''),
            data.get('subordinate_cmte_name', ''),
            data.get('subordinate_cmte_street_1', ''),
            data.get('subordinate_cmte_street_2', ''),
            data.get('subordinate_cmte_city', ''),
            data.get('subordinate_cmte_state', ''),
            data.get('subordinate_cmte_zip', ''),
            data.get('payee_entity_id', ''),
            data.get('expenditure_date', None),
            data.get('expenditure_amount ', None),
            data.get('aggregate_general_elec_exp', None),
            data.get('purpose', ''),
            data.get('category_code', ''),
            data.get('payee_cmte_id', ''),
            data.get('payee_cand_id', ''),
            data.get('payee_cand_last_name', ''),
            data.get('payee_cand_fist_name', ''),
            data.get('payee_cand_middle_name', ''),
            data.get('payee_cand_prefix', ''),
            data.get('payee_cand_suffix', ''),
            data.get('payee_cand_office', ''),
            data.get('payee_cand_state', ''),
            data.get('payee_cand_district', ''),
            data.get('memo_code', ''),
            data.get('memo_text', ''),
            datetime.datetime.now(),
            data.get('transaction_id'),
            data.get('report_id'),
            data.get('cmte_id'),
         )
    do_transaction(_sql, _v)


def validate_sF_data(data):
    """
    validate sF json data
    """
    check_mandatory_fields_SF(data)


def post_schedF(data):
    """
    function for handling POST request for sF, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        data['transaction_id'] = get_next_transaction_id('SF')
        print(data)
        validate_sF_data(data)
        try:
            post_sql_schedF(data)
        except Exception as e:
            raise Exception(
                'The post_sql_schedF function is throwing an error: ' + str(e))
        return data
    except:
        raise


def post_sql_schedF(data):
    try:
        _sql = """
        INSERT INTO public.sched_f (
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id, 
            back_ref_transaction_id,
            back_ref_sched_name,
            coordinated_exp_ind,
            designating_cmte_id,
            designating_cmte_name,
            subordinate_cmte_id,
            subordinate_cmte_name,
            subordinate_cmte_street_1,
            subordinate_cmte_street_2,
            subordinate_cmte_city,
            subordinate_cmte_state,
            subordinate_cmte_zip,
            payee_entity_id,
            expenditure_date,
            expenditure_amount ,
            aggregate_general_elec_exp ,
            purpose,
            category_code,
            payee_cmte_id,
            payee_cand_id,
            payee_cand_last_name,
            payee_cand_fist_name,
            payee_cand_middle_name,
            payee_cand_prefix,
            payee_cand_suffix,
            payee_cand_office,
            payee_cand_state,
            payee_cand_district,
            memo_code,
            memo_text,
            create_date,
            last_update_date
            )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get('cmte_id'),
            data.get('report_id'),
            data.get('transaction_type_identifier', ''),
            data.get('transaction_id', ''), 
            data.get('back_ref_transaction_id', ''),
            data.get('back_ref_sched_name', ''),
            data.get('coordinated_exp_ind', ''),
            data.get('designating_cmte_id', ''),
            data.get('designating_cmte_name', ''),
            data.get('subordinate_cmte_id', ''),
            data.get('subordinate_cmte_name', ''),
            data.get('subordinate_cmte_street_1', ''),
            data.get('subordinate_cmte_street_2', ''),
            data.get('subordinate_cmte_city', ''),
            data.get('subordinate_cmte_state', ''),
            data.get('subordinate_cmte_zip', ''),
            data.get('payee_entity_id', ''),
            data.get('expenditure_date', None),
            data.get('expenditure_amount ', None),
            data.get('aggregate_general_elec_exp', None),
            data.get('purpose', ''),
            data.get('category_code', ''),
            data.get('payee_cmte_id', ''),
            data.get('payee_cand_id', ''),
            data.get('payee_cand_last_name', ''),
            data.get('payee_cand_fist_name', ''),
            data.get('payee_cand_middle_name', ''),
            data.get('payee_cand_prefix', ''),
            data.get('payee_cand_suffix', ''),
            data.get('payee_cand_office', ''),
            data.get('payee_cand_state', ''),
            data.get('payee_cand_district', ''),
            data.get('memo_code', ''),
            data.get('memo_text', ''),
            datetime.datetime.now(),
            datetime.datetime.now()    
         )
        with connection.cursor() as cursor:
            # Insert data into schedD table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def get_schedF(data):
    """
    load sched_F data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        if 'transaction_id' in data:
            transaction_id = check_transaction_id(data.get('transaction_id'))
            forms_obj = get_list_schedF(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedF(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedF(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id, 
            back_ref_transaction_id,
            back_ref_sched_name,
            coordinated_exp_ind,
            designating_cmte_id,
            designating_cmte_name,
            subordinate_cmte_id,
            subordinate_cmte_name,
            subordinate_cmte_street_1,
            subordinate_cmte_street_2,
            subordinate_cmte_city,
            subordinate_cmte_state,
            subordinate_cmte_zip,
            payee_entity_id,
            expenditure_date,
            expenditure_amount ,
            aggregate_general_elec_exp ,
            purpose,
            category_code,
            payee_cmte_id,
            payee_cand_id,
            payee_cand_last_name,
            payee_cand_fist_name,
            payee_cand_middle_name,
            payee_cand_prefix,
            payee_cand_suffix,
            payee_cand_office,
            payee_cand_state,
            payee_cand_district,
            memo_code,
            memo_text,
            delete_ind,
            create_date,
            last_update_date
            FROM public.sched_f
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedF_list = cursor.fetchone()[0]
            if schedF_list is None:
                raise NoOPError('No sched_F transaction found for report_id {} and cmte_id: {}'.format(
                    report_id, cmte_id))
            merged_list = []
            for dictF in schedE_list:
                merged_list.append(dictF)
        return merged_list
    except Exception:
        raise


def get_list_schedF(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id, 
            back_ref_transaction_id,
            back_ref_sched_name,
            coordinated_exp_ind,
            designating_cmte_id,
            designating_cmte_name,
            subordinate_cmte_id,
            subordinate_cmte_name,
            subordinate_cmte_street_1,
            subordinate_cmte_street_2,
            subordinate_cmte_city,
            subordinate_cmte_state,
            subordinate_cmte_zip,
            payee_entity_id,
            expenditure_date,
            expenditure_amount ,
            aggregate_general_elec_exp ,
            purpose,
            category_code,
            payee_cmte_id,
            payee_cand_id,
            payee_cand_last_name,
            payee_cand_fist_name,
            payee_cand_middle_name,
            payee_cand_prefix,
            payee_cand_suffix,
            payee_cand_office,
            payee_cand_state,
            payee_cand_district,
            memo_code,
            memo_text,
            delete_ind,
            create_date,
            last_update_date
            FROM public.sched_f
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedF_list = cursor.fetchone()[0]
            if schedF_list is None:
                raise NoOPError('No sched_f transaction found for transaction_id {}'.format(
                    transaction_id))
            merged_list = []
            for dictF in schedF_list:
                merged_list.append(dictF)
        return merged_list
    except Exception:
        raise


def delete_sql_schedF(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_f
            SET delete_ind = 'Y' 
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedF(data):
    """
    function for handling delete request for se
    """
    try:
        
        delete_sql_schedF(data.get('cmte_id'), data.get(
            'report_id'), data.get('transaction_id'))
    except Exception as e:
        raise


@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedF(request):
    
    if request.method == 'POST':
        try:
            cmte_id = request.user.username
            if not('report_id' in request.data):
                raise Exception('Missing Input: Report_id is mandatory')
            # handling null,none value of report_id
            if not (check_null_value(request.data.get('report_id'))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get('report_id'))
            # end of handling
            datum = schedF_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'transaction_id' in request.data and check_null_value(
                    request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
                data = put_schedF(datum)
            else:
                print(datum)
                data = post_schedF(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedF(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedF API - POST is throwing an exception: "
                            + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        try:
            data = {
                'cmte_id': request.user.username
            }
            if 'report_id' in request.data and check_null_value(request.data.get('report_id')):
                data['report_id'] = check_report_id(
                    request.data.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
            datum = get_schedF(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedF API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            data = {
                'cmte_id': request.user.username
            }
            if 'report_id' in request.data and check_null_value(request.data.get('report_id')):
                data['report_id'] = check_report_id(
                    request.data.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
            else:
                raise Exception('Missing Input: transaction_id is mandatory')
            delete_schedF(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedF API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            datum = schedF_sql_dict(request.data)
            if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
                datum['transaction_id'] = request.data.get('transaction_id')
            else:
                raise Exception('Missing Input: transaction_id is mandatory')

            if not('report_id' in request.data):
                raise Exception('Missing Input: Report_id is mandatory')
            # handling null,none value of report_id
            if not (check_null_value(request.data.get('report_id'))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get('report_id'))
            # end of handling
            datum['report_id'] = report_id
            datum['cmte_id'] = request.user.username

            # if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
            #     datum['entity_id'] = request.data.get('entity_id')
            # if request.data.get('transaction_type') in CHILD_SCHED_B_TYPES:
            #     data = put_schedB(datum)
            #     output = get_schedB(data)
            # else:
            data = put_schedF(datum)
            # output = get_schedA(data)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedF API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    else:
        raise NotImplementedError






