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
from fecfiler.sched_A.views import get_next_transaction_id
from fecfiler.sched_D.views import do_transaction


# Create your views here.
logger = logging.getLogger(__name__)

MANDATORY_FIELDS_SCHED_H3 = ['cmte_id', 'report_id', 'transaction_id']
MANDATORY_FIELDS_SCHED_H4 = ['cmte_id', 'report_id', 'transaction_id']



def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SH3"):
        raise Exception(
            'The Transaction ID: {} is not in the specified format.' +
            'Transaction IDs start with SH3 characters'.format(transaction_id))
    return transaction_id


def check_mandatory_fields_SH3(data):
    """
    validate mandatory fields for sched_H3 item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H3:
            if not(field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                'The following mandatory fields are required in order to save data to schedH3 table: {}'.format(','.join(errors)))
    except:
        raise


def schedH3_sql_dict(data):
    """
    filter out valid fileds for sched_H3

    """
    valid_fields = [

            'transaction_type_identifier',
            'back_ref_transaction_id',
            'back_ref_sched_name',
            'account_name',
            'activity_event_type',
            'activity_event_name',
            'receipt_date',
            'total_amount_transferred',
            'transferred_amount',
            'memo_code',
            'memo_text',         
    ]
    try:
        return {k: v for k, v in data.items() if k in valid_fields}
    except:
        raise Exception('invalid request data.')


def put_schedH3(data):
    """
    update sched_H3 item
    here we are assuming entity_id are always referencing something already in our DB
    """
    try:
        check_mandatory_fields_SH3(data)
        #check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedH3(data)
        except Exception as e:
            raise Exception(
                'The put_sql_schedH3 function is throwing an error: ' + str(e))
        return data
    except:
        raise


def put_sql_schedH3(data):
    """
    update a schedule_H3 item                    
            
    """
    _sql = """UPDATE public.sched_h3
              SET transaction_type_identifier= %s, 
                  back_ref_transaction_id= %s,
                  back_ref_sched_name= %s,
                  account_name= %s,
                  activity_event_type= %s,
                  activity_event_name= %s,
                  receipt_date= %s,
                  total_amount_transferred= %s,
                  transferred_amount= %s,
                  memo_code= %s,
                  memo_text= %s,
                  create_date= %s,
                  last_update_date= %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (  
           
            data.get('transaction_type_identifier', ''),
            data.get('back_ref_transaction_id', ''),
            data.get('back_ref_sched_name', ''),
            data.get('account_name', ''),
            data.get('activity_event_type', ''),
            data.get('activity_event_name', ''),
            data.get('receipt_date', None),
            data.get('total_amount_transferred', None),
            data.get('transferred_amount', None),
            data.get('memo_code', ''),
            data.get('memo_text', ''),
            datetime.datetime.now(),
            data.get('transaction_id'),
            data.get('report_id'),
            data.get('cmte_id'),
         )
    do_transaction(_sql, _v)


def validate_sh3_data(data):
    """
    validate sH3 json data
    """
    check_mandatory_fields_SH3(data)


def post_schedH3(data):
    """
    function for handling POST request for sH3, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        data['transaction_id'] = get_next_transaction_id('SH3')
        print(data)
        validate_sh3_data(data)
        try:
            post_sql_schedH3(data)
        except Exception as e:
            raise Exception(
                'The post_sql_schedH3 function is throwing an error: ' + str(e))
        return data
    except:
        raise


def post_sql_schedH3(data):
    try:
        _sql = """
        INSERT INTO public.sched_h3 (
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            account_name,
            activity_event_type,
            activity_event_name,
            receipt_date,
            total_amount_transferred,
            transferred_amount,
            memo_code,
            memo_text,
            create_date ,
            last_update_date
            )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get('cmte_id'),
            data.get('report_id'),
            data.get('transaction_type_identifier', ''),
            data.get('transaction_id'),
            data.get('back_ref_transaction_id', ''),
            data.get('back_ref_sched_name', ''),
            data.get('account_name', ''),
            data.get('activity_event_type', ''),
            data.get('activity_event_name', ''),
            data.get('receipt_date', None),
            data.get('total_amount_transferred', None),
            data.get('transferred_amount', None),
            data.get('memo_code', ''),
            data.get('memo_text', ''),
            datetime.datetime.now(),    
         )
        with connection.cursor() as cursor:
            # Insert data into schedH3 table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def get_schedH3(data):
    """
    load sched_H3 data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        if 'transaction_id' in data:
            transaction_id = check_transaction_id(data.get('transaction_id'))
            forms_obj = get_list_schedH3(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedH3(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedH3(report_id, cmte_id):

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
            account_name,
            activity_event_type,
            activity_event_name,
            receipt_date,
            total_amount_transferred,
            transferred_amount,
            memo_code,
            memo_text,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_h3
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedH3_list = cursor.fetchone()[0]
            if schedH3_list is None:
                raise NoOPError('No sched_H3 transaction found for report_id {} and cmte_id: {}'.format(
                    report_id, cmte_id))
            merged_list = []
            for dictH3 in schedH3_list:
                merged_list.append(dictH3)
        return merged_list
    except Exception:
        raise


def get_list_schedH3(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH3 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            account_name,
            activity_event_type,
            activity_event_name,
            receipt_date,
            total_amount_transferred,
            transferred_amount,
            memo_code,
            memo_text,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_h3
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH3_list = cursor.fetchone()[0]
            if schedH3_list is None:
                raise NoOPError('No sched_H3 transaction found for transaction_id {}'.format(
                    transaction_id))
            merged_list = []
            for dictH3 in schedH3_list:
                merged_list.append(dictH3)
        return merged_list
    except Exception:
        raise


def delete_sql_schedH3(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_h3
            SET delete_ind = 'Y' 
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH3(data):
    """
    function for handling delete request for sh3
    """
    try:
        
        delete_sql_schedH3(data.get('cmte_id'), data.get(
            'report_id'), data.get('transaction_id'))
    except Exception as e:
        raise


@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedH3(request):
    
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
            datum = schedH3_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'transaction_id' in request.data and check_null_value(
                    request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
                data = put_schedH3(datum)
            else:
                print(datum)
                data = post_schedH3(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedH3(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH3 API - POST is throwing an exception: "
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
            datum = get_schedH3(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH3 API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
            delete_schedH3(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH3 API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            datum = schedH3_sql_dict(request.data)
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
            data = put_schedH3(datum)
            # output = get_schedA(data)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH3 API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    else:
        raise NotImplementedError

"""
************************************************* CRUD API FOR SCHEDULE_H4 ********************************************************************************

"""
def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SH4"):
        raise Exception(
            'The Transaction ID: {} is not in the specified format.' +
            'Transaction IDs start with SH4 characters'.format(transaction_id))
    return transaction_id


def check_mandatory_fields_SH4(data):
    """
    validate mandatory fields for sched_H4 item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H4:
            if not(field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                'The following mandatory fields are required in order to save data to schedH4 table: {}'.format(','.join(errors)))
    except:
        raise


def schedH4_sql_dict(data):
    """
    filter out valid fileds for sched_H4

    """
    valid_fields = [

            'transaction_type_identifier',
            'back_ref_transaction_id',
            'back_ref_sched_name',
            'payee_entity_id',
            'activity_event_identifier',
            'expenditure_date',
            'fed_share_amount',
            'non_fed_share_amount',
            'total_amount',
            'activity_event_amount_ytd',
            'purpose',
            'category_code',
            'activity_event_type',
            'memo_code',
            'memo_text',         
    ]
    try:
        return {k: v for k, v in data.items() if k in valid_fields}
    except:
        raise Exception('invalid request data.')


def put_schedH4(data):
    """
    update sched_H4 item
    
    """
    try:
        check_mandatory_fields_SH4(data)
        #check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedH4(data)
        except Exception as e:
            raise Exception(
                'The put_sql_schedH4 function is throwing an error: ' + str(e))
        return data
    except:
        raise


def put_sql_schedH4(data):
    """
    update a schedule_H4 item                    
            
    """
    _sql = """UPDATE public.sched_h4
              SET transaction_type_identifier= %s, 
                  back_ref_transaction_id = %s,
                  back_ref_sched_name = %s,
                  payee_entity_id = %s,
                  activity_event_identifier = %s,
                  expenditure_date = %s,
                  fed_share_amount = %s,
                  non_fed_share_amount = %s,
                  total_amount = %s,
                  activity_event_amount_ytd = %s,
                  purpose = %s,
                  category_code = %s,
                  activity_event_type = %s,
                  memo_code = %s,
                  memo_text = %s,
                  create_date= %s,
                  last_update_date= %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (  
           
            data.get('transaction_type_identifier', ''),
            data.get('back_ref_transaction_id ', ''),
            data.get('back_ref_sched_name ', ''),
            data.get('payee_entity_id ', ''),
            data.get('activity_event_identifier ', ''),
            data.get('expenditure_date ', None),
            data.get('fed_share_amount ', None),
            data.get('non_fed_share_amount ', None),
            data.get('total_amount ', None),
            data.get('activity_event_amount_ytd ', None),
            data.get('purpose ', ''),
            data.get('category_code ', ''),
            data.get('activity_event_type ', ''),
            data.get('memo_code ', ''),
            data.get('memo_text ', ''),
            datetime.datetime.now(),
            data.get('transaction_id'),
            data.get('report_id'),
            data.get('cmte_id'),
         )
    do_transaction(_sql, _v)


def validate_sh4_data(data):
    """
    validate sH4 json data
    """
    check_mandatory_fields_SH4(data)


def post_schedH4(data):
    """
    function for handling POST request for sH4, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_H4)
        data['transaction_id'] = get_next_transaction_id('SH4')
        print(data)
        validate_sh4_data(data)
        try:
            post_sql_schedH4(data)
        except Exception as e:
            raise Exception(
                'The post_sql_schedH4 function is throwing an error: ' + str(e))
        return data
    except:
        raise


def post_sql_schedH4(data):
    try:
        _sql = """
        INSERT INTO public.sched_h4 (
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            payee_entity_id,
            activity_event_identifier,
            expenditure_date,
            fed_share_amount,
            non_fed_share_amount,
            total_amount,
            activity_event_amount_ytd,
            purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            create_date ,
            last_update_date
            )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get('cmte_id'),
            data.get('report_id'),
            data.get('transaction_type_identifier', ''),
            data.get('transaction_id'),
            data.get('back_ref_transaction_id ', ''),
            data.get('back_ref_sched_name ', ''),
            data.get('payee_entity_id ', ''),
            data.get('activity_event_identifier ', ''),
            data.get('expenditure_date ', None),
            data.get('fed_share_amount ', None),
            data.get('non_fed_share_amount ', None),
            data.get('total_amount ', None),
            data.get('activity_event_amount_ytd ', None),
            data.get('purpose ', ''),
            data.get('category_code ', ''),
            data.get('activity_event_type ', ''),
            data.get('memo_code ', ''),
            data.get('memo_text ', ''),
            datetime.datetime.now(),   
         )
        with connection.cursor() as cursor:
            # Insert data into schedH4 table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def get_schedH4(data):
    """
    load sched_H4 data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        if 'transaction_id' in data:
            transaction_id = check_transaction_id(data.get('transaction_id'))
            forms_obj = get_list_schedH4(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedH4(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedH4(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedH4 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            payee_entity_id,
            activity_event_identifier,
            expenditure_date,
            fed_share_amount,
            non_fed_share_amount,
            total_amount,
            activity_event_amount_ytd,
            purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_h4
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedH4_list = cursor.fetchone()[0]
            if schedH4_list is None:
                raise NoOPError('No sched_H4 transaction found for report_id {} and cmte_id: {}'.format(
                    report_id, cmte_id))
            merged_list = []
            for dictH4 in schedH4_list:
                merged_list.append(dictH4)
        return merged_list
    except Exception:
        raise


def get_list_schedH4(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH4 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            payee_entity_id,
            activity_event_identifier,
            expenditure_date,
            fed_share_amount,
            non_fed_share_amount,
            total_amount,
            activity_event_amount_ytd,
            purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_h4
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH4_list = cursor.fetchone()[0]
            if schedH4_list is None:
                raise NoOPError('No sched_H4 transaction found for transaction_id {}'.format(
                    transaction_id))
            merged_list = []
            for dictH4 in schedH4_list:
                merged_list.append(dictH4)
        return merged_list
    except Exception:
        raise


def delete_sql_schedH4(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_h4
            SET delete_ind = 'Y' 
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH4(data):
    """
    function for handling delete request for sh4
    """
    try:
        
        delete_sql_schedH4(data.get('cmte_id'), data.get(
            'report_id'), data.get('transaction_id'))
    except Exception as e:
        raise


@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedH4(request):
    
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
            datum = schedH4_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'transaction_id' in request.data and check_null_value(
                    request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
                data = put_schedH4(datum)
            else:
                print(datum)
                data = post_schedH4(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedH4(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH4 API - POST is throwing an exception: "
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
            datum = get_schedH4(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH4 API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
            delete_schedH4(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH4 API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            datum = schedH4_sql_dict(request.data)
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
            data = put_schedH4(datum)
            # output = get_schedA(data)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH4 API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    else:
        raise NotImplementedError



"""

************************************************** CRUD API FOR SCHEDULE_H5 ***********************************************************************************

"""
def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SH5"):
        raise Exception(
            'The Transaction ID: {} is not in the specified format.' +
            'Transaction IDs start with SH5 characters'.format(transaction_id))
    return transaction_id


def check_mandatory_fields_SH5(data):
    """
    validate mandatory fields for sched_H5 item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H5:
            if not(field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                'The following mandatory fields are required in order to save data to schedH5 table: {}'.format(','.join(errors)))
    except:
        raise


def schedH5_sql_dict(data):
    """
    filter out valid fileds for sched_H5

    """
    valid_fields = [

            'transaction_type_identifier',
            'account_name',
            'receipt_date',
            'total_amount_transferred',
            'voter_registration_amount',
            'voter_id_amount',
            'gotv_amount',
            'generic_campaign_amount',
            'memo_code',
            'memo_text',        
    ]
    try:
        return {k: v for k, v in data.items() if k in valid_fields}
    except:
        raise Exception('invalid request data.')


def put_schedH5(data):
    """
    update sched_H5 item
    
    """
    try:
        check_mandatory_fields_SH5(data)
        #check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedH5(data)
        except Exception as e:
            raise Exception(
                'The put_sql_schedH5 function is throwing an error: ' + str(e))
        return data
    except:
        raise


def put_sql_schedH5(data):
    """
    update a schedule_H5 item                    
            
    """
    _sql = """UPDATE public.sched_h5
              SET transaction_type_identifier= %s, 
                  account_name= %s,
                  receipt_date= %s,
                  total_amount_transferred= %s,
                  voter_registration_amount= %s,
                  voter_id_amount= %s,
                  gotv_amount= %s,
                  generic_campaign_amount= %s,
                  memo_code= %s,
                  memo_text = %s,
                  create_date= %s,
                  last_update_date= %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (  
           
            data.get('transaction_type_identifier', ''),
            data.get('account_name', ''),
            data.get('receipt_date', None),
            data.get('total_amount_transferred', None),
            data.get('voter_registration_amount', None),
            data.get('voter_id_amount', None),
            data.get('gotv_amount', None),
            data.get('generic_campaign_amount', None),
            data.get('memo_code', ''),
            data.get('memo_text', ''),
            datetime.datetime.now(),
            data.get('transaction_id'),
            data.get('report_id'),
            data.get('cmte_id'),
         )
    do_transaction(_sql, _v)


def validate_sh5_data(data):
    """
    validate sH5 json data
    """
    check_mandatory_fields_SH5(data)


def post_schedH5(data):
    """
    function for handling POST request for sH5, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SH5(datum, MANDATORY_FIELDS_SCHED_H5)
        data['transaction_id'] = get_next_transaction_id('SH5')
        print(data)
        validate_sh5_data(data)
        try:
            post_sql_schedH5(data)
        except Exception as e:
            raise Exception(
                'The post_sql_schedH5 function is throwing an error: ' + str(e))
        return data
    except:
        raise


def post_sql_schedH5(data):
    try:
        _sql = """
        INSERT INTO public.sched_h5 (
            cmte_id,
            report_id,
            transaction_type_identifier ,
            transaction_id,
            account_name,
            receipt_date,
            total_amount_transferred,
            voter_registration_amount,
            voter_id_amount,
            gotv_amount,
            generic_campaign_amount,
            memo_code,
            memo_text ,
            create_date,
            last_update_date
            )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get('cmte_id'),
            data.get('report_id'),
            data.get('transaction_type_identifier', ''),
            data.get('transaction_id'),
            data.get('account_name', ''),
            data.get('receipt_date', None),
            data.get('total_amount_transferred', None),
            data.get('voter_registration_amount', None),
            data.get('voter_id_amount', None),
            data.get('gotv_amount', None),
            data.get('generic_campaign_amount', None),
            data.get('memo_code', ''),
            data.get('memo_text', ''),
            datetime.datetime.now(),   
         )
        with connection.cursor() as cursor:
            # Insert data into schedH5 table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def get_schedH5(data):
    """
    load sched_H5 data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        if 'transaction_id' in data:
            transaction_id = check_transaction_id(data.get('transaction_id'))
            forms_obj = get_list_schedH5(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedH5(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedH5(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedH5 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier ,
            transaction_id,
            account_name,
            receipt_date,
            total_amount_transferred,
            voter_registration_amount,
            voter_id_amount,
            gotv_amount,
            generic_campaign_amount,
            memo_code,
            memo_text ,
            create_date,
            last_update_date
            FROM public.sched_h5
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedH5_list = cursor.fetchone()[0]
            if schedH5_list is None:
                raise NoOPError('No sched_H5 transaction found for report_id {} and cmte_id: {}'.format(
                    report_id, cmte_id))
            merged_list = []
            for dictH5 in schedH5_list:
                merged_list.append(dictH5)
        return merged_list
    except Exception:
        raise


def get_list_schedH5(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH5 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier ,
            transaction_id,
            account_name,
            receipt_date,
            total_amount_transferred,
            voter_registration_amount,
            voter_id_amount,
            gotv_amount,
            generic_campaign_amount,
            memo_code,
            memo_text ,
            create_date,
            last_update_date
            FROM public.sched_h5
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH5_list = cursor.fetchone()[0]
            if schedH5_list is None:
                raise NoOPError('No sched_H5 transaction found for transaction_id {}'.format(
                    transaction_id))
            merged_list = []
            for dictH5 in schedH5_list:
                merged_list.append(dictH5)
        return merged_list
    except Exception:
        raise


def delete_sql_schedH5(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_h5
            SET delete_ind = 'Y' 
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH5(data):
    """
    function for handling delete request for sh5
    """
    try:
        
        delete_sql_schedH5(data.get('cmte_id'), data.get(
            'report_id'), data.get('transaction_id'))
    except Exception as e:
        raise


@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedH5(request):
    
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
            datum = schedH5_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'transaction_id' in request.data and check_null_value(
                    request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
                data = put_schedH5(datum)
            else:
                print(datum)
                data = post_schedH5(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedH5(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH5 API - POST is throwing an exception: "
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
            datum = get_schedH5(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH5 API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
            delete_schedH5(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH5 API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            datum = schedH5_sql_dict(request.data)
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
            data = put_schedH5(datum)
            # output = get_schedA(data)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH5 API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    else:
        raise NotImplementedError












