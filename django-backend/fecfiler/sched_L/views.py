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

MANDATORY_FIELDS_SCHED_L = ['cmte_id', 'report_id', 'transaction_id','record_id']




def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SL"):
        raise Exception(
            'The Transaction ID: {} is not in the specified format.' +
            'Transaction IDs start with SL characters'.format(transaction_id))
    return transaction_id


def check_mandatory_fields_SL(data):
    """
    validate mandatory fields for sched_L item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_L:
            if not(field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                'The following mandatory fields are required in order to save data to schedL table: {}'.format(','.join(errors)))
    except:
        raise


def schedL_sql_dict(data):
    """
    filter out valid fileds for sched_L

    """
    valid_fields = [

            'transaction_type_identifier',
            'record_id',
            'account_name',
            'cvg_from_date',
            'cvg_end_date',
            'item_receipts',
            'unitem_receipts',
            'ttl_receipts',
            'other_receipts',
            'total_receipts',
            'voter_reg_disb_amount',
            'voter_id_disb_amount',
            'gotv_disb_amount',
            'generic_campaign_disb_amount',
            'total_disb_sub',
            'other_disb',
            'total_disb',
            'coh_bop',
            'receipts',
            'subtotal',
            'disbursements',
            'coh_cop',
            'item_receipts_ytd',
            'unitem_receipts_ytd',
            'total_reciepts_ytd',
            'other_receipts_ytd',
            'total_receipts_ytd',
            'voter_reg_disb_amount_ytd',
            'voter_id_disb_amount_ytd',
            'gotv_disb_amount_ytd',
            'generic_campaign_disb_amount_ytd',
            'total_disb_sub_ytd',
            'other_disb_ytd',
            'total_disb_ytd',
            'coh_coy',
            'receipts_ytd',
            'sub_total_ytd',
            'disbursements_ytd',
            'coh_cop_ytd',        
    ]
    try:
        return {k: v for k, v in data.items() if k in valid_fields}
    except:
        raise Exception('invalid request data.')


def put_schedL(data):
    """
    update sched_L item
    here we are assuming entity_id are always referencing something already in our DB
    """
    try:
        check_mandatory_fields_SL(data)
        #check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedL(data)
        except Exception as e:
            raise Exception(
                'The put_sql_schedL function is throwing an error: ' + str(e))
        return data
    except:
        raise


def put_sql_schedL(data):
    """
    update a schedule_L item                    
            
    """
    _sql = """UPDATE public.sched_l
              SET transaction_type_identifier= %s, 
                  record_id =%s,
                  account_name =%s,
                  cvg_from_date =%s,
                  cvg_end_date =%s,
                  item_receipts =%s,
                  unitem_receipts =%s,
                  ttl_receipts =%s,
                  other_receipts =%s,
                  total_receipts =%s,
                  voter_reg_disb_amount =%s,
                  voter_id_disb_amount =%s,
                  gotv_disb_amount =%s,
                  generic_campaign_disb_amount =%s,
                  total_disb_sub =%s,
                  other_disb =%s,
                  total_disb =%s,
                  coh_bop =%s,
                  receipts =%s,
                  subtotal =%s,
                  disbursements =%s,
                  coh_cop =%s,
                  item_receipts_ytd =%s,
                  unitem_receipts_ytd =%s,
                  total_reciepts_ytd =%s,
                  other_receipts_ytd =%s,
                  total_receipts_ytd =%s,
                  voter_reg_disb_amount_ytd =%s,
                  voter_id_disb_amount_ytd =%s,
                  gotv_disb_amount_ytd =%s,
                  generic_campaign_disb_amount_ytd =%s,
                  total_disb_sub_ytd =%s,
                  other_disb_ytd =%s,
                  total_disb_ytd =%s,
                  coh_coy =%s,
                  receipts_ytd =%s,
                  sub_total_ytd =%s,
                  disbursements_ytd =%s,
                  coh_cop_ytd =%s,
                  create_date =%s,
                  last_update_date= %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (  
           
            data.get('transaction_type_identifier', ''),
            data.get('record_id', ''),
            data.get('account_name', ''),
            data.get('cvg_from_date', None),
            data.get('cvg_end_date', None),
            data.get('item_receipts', None),
            data.get('unitem_receipts', None),
            data.get('ttl_receipts', None),
            data.get('other_receipts', None),
            data.get('total_receipts', None),
            data.get('voter_reg_disb_amount', None),
            data.get('voter_id_disb_amount', None),
            data.get('gotv_disb_amount', None),
            data.get('generic_campaign_disb_amount', None),
            data.get('total_disb_sub', None),
            data.get('other_disb', None),
            data.get('total_disb', None),
            data.get('coh_bop', None),
            data.get('receipts', None),
            data.get('subtotal', None),
            data.get('disbursements', None),
            data.get('coh_cop', None),
            data.get('item_receipts_ytd', None),
            data.get('unitem_receipts_ytd', None),
            data.get('total_reciepts_ytd', None),
            data.get('other_receipts_ytd', None),
            data.get('total_receipts_ytd', None),
            data.get('voter_reg_disb_amount_ytd', None),
            data.get('voter_id_disb_amount_ytd', None),
            data.get('gotv_disb_amount_ytd', None),
            data.get('generic_campaign_disb_amount_ytd', None),
            data.get('total_disb_sub_ytd', None),
            data.get('other_disb_ytd', None),
            data.get('total_disb_ytd', None),
            data.get('coh_coy', None),
            data.get('receipts_ytd', None),
            data.get('sub_total_ytd', None),
            data.get('disbursements_ytd', None),
            data.get('coh_cop_ytd', None),
            datetime.datetime.now(),
            datetime.datetime.now(),
            data.get('transaction_id'),
            data.get('report_id'),
            data.get('cmte_id'),
         )
    do_transaction(_sql, _v)


def validate_sl_data(data):
    """
    validate sL json data
    """
    check_mandatory_fields_SL(data)


def post_schedL(data):
    """
    function for handling POST request for sL, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SL(datum, MANDATORY_FIELDS_SCHED_L)
        data['transaction_id'] = get_next_transaction_id('SL')
        print(data)
        validate_sl_data(data)
        try:
            post_sql_schedL(data)
        except Exception as e:
            raise Exception(
                'The post_sql_schedL function is throwing an error: ' + str(e))
        return data
    except:
        raise


def post_sql_schedL(data):
    try:
        _sql = """
        INSERT INTO public.sched_l (
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            record_id,
            account_name,
            cvg_from_date,
            cvg_end_date,
            item_receipts,
            unitem_receipts,
            ttl_receipts,
            other_receipts,
            total_receipts,
            voter_reg_disb_amount,
            voter_id_disb_amount,
            gotv_disb_amount,
            generic_campaign_disb_amount,
            total_disb_sub,
            other_disb,
            total_disb,
            coh_bop,
            receipts,
            subtotal,
            disbursements,
            coh_cop,
            item_receipts_ytd,
            unitem_receipts_ytd,
            total_reciepts_ytd,
            other_receipts_ytd,
            total_receipts_ytd,
            voter_reg_disb_amount_ytd,
            voter_id_disb_amount_ytd,
            gotv_disb_amount_ytd,
            generic_campaign_disb_amount_ytd,
            total_disb_sub_ytd,
            other_disb_ytd,
            total_disb_ytd,
            coh_coy,
            receipts_ytd,
            sub_total_ytd,
            disbursements_ytd,
            coh_cop_ytd,
            create_date ,
            last_update_date 
            )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get('cmte_id'),
            data.get('report_id'),
            data.get('transaction_type_identifier', ''),
            data.get('transaction_id'),
            data.get('record_id', ''),
            data.get('account_name', ''),
            data.get('cvg_from_date', None),
            data.get('cvg_end_date', None),
            data.get('item_receipts', None),
            data.get('unitem_receipts', None),
            data.get('ttl_receipts', None),
            data.get('other_receipts', None),
            data.get('total_receipts', None),
            data.get('voter_reg_disb_amount', None),
            data.get('voter_id_disb_amount', None),
            data.get('gotv_disb_amount', None),
            data.get('generic_campaign_disb_amount', None),
            data.get('total_disb_sub', None),
            data.get('other_disb', None),
            data.get('total_disb', None),
            data.get('coh_bop', None),
            data.get('receipts', None),
            data.get('subtotal', None),
            data.get('disbursements', None),
            data.get('coh_cop', None),
            data.get('item_receipts_ytd', None),
            data.get('unitem_receipts_ytd', None),
            data.get('total_reciepts_ytd', None),
            data.get('other_receipts_ytd', None),
            data.get('total_receipts_ytd', None),
            data.get('voter_reg_disb_amount_ytd', None),
            data.get('voter_id_disb_amount_ytd', None),
            data.get('gotv_disb_amount_ytd', None),
            data.get('generic_campaign_disb_amount_ytd', None),
            data.get('total_disb_sub_ytd', None),
            data.get('other_disb_ytd', None),
            data.get('total_disb_ytd', None),
            data.get('coh_coy', None),
            data.get('receipts_ytd', None),
            data.get('sub_total_ytd', None),
            data.get('disbursements_ytd', None),
            data.get('coh_cop_ytd', None),
            datetime.datetime.now(),
            datetime.datetime.now(),    
         )
        with connection.cursor() as cursor:
            # Insert data into schedL table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def get_schedL(data):
    """
    load sched_L data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        if 'transaction_id' in data:
            transaction_id = check_transaction_id(data.get('transaction_id'))
            forms_obj = get_list_schedL(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedL(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedL(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedL table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            record_id,
            account_name,
            cvg_from_date,
            cvg_end_date,
            item_receipts,
            unitem_receipts,
            ttl_receipts,
            other_receipts,
            total_receipts,
            voter_reg_disb_amount,
            voter_id_disb_amount,
            gotv_disb_amount,
            generic_campaign_disb_amount,
            total_disb_sub,
            other_disb,
            total_disb,
            coh_bop,
            receipts,
            subtotal,
            disbursements,
            coh_cop,
            item_receipts_ytd,
            unitem_receipts_ytd,
            total_reciepts_ytd,
            other_receipts_ytd,
            total_receipts_ytd,
            voter_reg_disb_amount_ytd,
            voter_id_disb_amount_ytd,
            gotv_disb_amount_ytd,
            generic_campaign_disb_amount_ytd,
            total_disb_sub_ytd,
            other_disb_ytd,
            total_disb_ytd,
            coh_coy,
            receipts_ytd,
            sub_total_ytd,
            disbursements_ytd,
            coh_cop_ytd,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_l
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedl_list = cursor.fetchone()[0]
            if schedl_list is None:
                raise NoOPError('No sched_L transaction found for report_id {} and cmte_id: {}'.format(
                    report_id, cmte_id))
            merged_list = []
            for dictL in schedL_list:
                merged_list.append(dictL)
        return merged_list
    except Exception:
        raise


def get_list_schedL(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedL table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            record_id,
            account_name,
            cvg_from_date,
            cvg_end_date,
            item_receipts,
            unitem_receipts,
            ttl_receipts,
            other_receipts,
            total_receipts,
            voter_reg_disb_amount,
            voter_id_disb_amount,
            gotv_disb_amount,
            generic_campaign_disb_amount,
            total_disb_sub,
            other_disb,
            total_disb,
            coh_bop,
            receipts,
            subtotal,
            disbursements,
            coh_cop,
            item_receipts_ytd,
            unitem_receipts_ytd,
            total_reciepts_ytd,
            other_receipts_ytd,
            total_receipts_ytd,
            voter_reg_disb_amount_ytd,
            voter_id_disb_amount_ytd,
            gotv_disb_amount_ytd,
            generic_campaign_disb_amount_ytd,
            total_disb_sub_ytd,
            other_disb_ytd,
            total_disb_ytd,
            coh_coy,
            receipts_ytd,
            sub_total_ytd,
            disbursements_ytd,
            coh_cop_ytd,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_l
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedL_list = cursor.fetchone()[0]
            if schedL_list is None:
                raise NoOPError('No sched_L transaction found for transaction_id {}'.format(
                    transaction_id))
            merged_list = []
            for dictL in schedL_list:
                merged_list.append(dictL)
        return merged_list
    except Exception:
        raise


def delete_sql_schedL(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_l
            SET delete_ind = 'Y' 
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedL(data):
    """
    function for handling delete request for sl
    """
    try:
        
        delete_sql_schedL(data.get('cmte_id'), data.get(
            'report_id'), data.get('transaction_id'))
    except Exception as e:
        raise


@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedL(request):
    
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
            datum = schedL_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'transaction_id' in request.data and check_null_value(
                    request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
                data = put_schedL(datum)
            else:
                print(datum)
                data = post_schedL(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedL(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedL API - POST is throwing an exception: "
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
            datum = get_schedL(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedL API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
            delete_schedL(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedL API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            datum = schedL_sql_dict(request.data)
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
            data = put_schedL(datum)
            # output = get_schedA(data)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedL API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    else:
        raise NotImplementedError
