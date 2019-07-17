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
# from fecfiler.sched_B.views import (delete_parent_child_link_sql_schedB,
#                                     delete_schedB, get_list_child_schedB,
#                                     get_schedB, post_schedB, put_schedB,
#                                     schedB_sql_dict)

# Create your views here.
logger = logging.getLogger(__name__)


def check_transaction_id(data):
    if not (transaction_id[0:2] == "SC"):
        raise Exception(
            'The Transaction ID: {} is not in the specified format.' +
            'Transaction IDs start with SD characters'.format(transaction_id))
    return transaction_id


def put_schedC2(data):
    """
    update sched_c2 item
    here we are assuming guarantor_entoty_id are always referencing something already in our DB
    """
    try:
        check_mandatory_fields_SC2(datum)
        transaction_id = check_transaction_id(datum.get('transaction_id'))
        try:
            put_sql_schedD(datum)
        except Exception as e:
            raise Exception(
                'The put_sql_schedD function is throwing an error: ' + str(e))
        return datum
    except:
        raise


def put_sql_schedC2(data):
    pass


def post_schedC2(data):
    pass


def get_schedC2(data):
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        if 'transaction_id' in data:
            transaction_id = check_transaction_id(data.get('transaction_id'))
            forms_obj = get_list_schedC2(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedC2(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedC2(report_id, cmte_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            guarantor_entity_id,
            guaranteed_amount,
            last_update_date
            FROM public.sched_c2
            WHERE report_id = ? AND cmte_id = ?
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedC2_list = cursor.fetchone()[0]
            if schedC2_list is None:
                raise NoOPError(
                    'No sched_c2 transaction found for report_id {} and cmte_id: {}'.format(report_id, cmte_id))
            merged_list = []
            for dictC2 in schedC2_list:
                merged_list.append(dictC2)
        return merged_list
    except Exception:
        raise


def get_list_schedC2(report_id, cmte_id, transaction_id):
    """
        cmte_id = models.CharField(max_length=9)
    report_id = models.BigIntegerField()
    transaction_type_identifier = models.CharField(
        max_length=12, blank=True, null=True)
    transaction_id = models.CharField(primary_key=True, max_length=20)
    guarantor_entity_id = models.CharField(
        max_length=20, blank=True, null=True)
    guaranteed_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    delete_ind = models.CharField(max_length=1, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)
    """

    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            guarantor_entity_id,
            guaranteed_amount,
            last_update_date
            FROM public.sched_c2
            WHERE report_id = ? AND cmte_id = ? AND transaction_id = ?
            AND delete_ind is distinct from 'Y') t
            """

            cursor.execute(_sql, (report_id, cmte_id, transaction_id))

            schedC2_list = cursor.fetchone()[0]

            if schedC2_list is None:
                raise NoOPError(
                    'The transaction id: {} does not exist or is deleted'.format(transaction_id))
            merged_list = []
            for dictC2 in schedC2_list:
                merged_list.append(dictC2)
        return merged_list
    except Exception:
        raise


def schedC2_sql_dict(data):
    valid_fields = [
        'transaction_type_identifier',
        'guarantor_entity_id',
        'guaranteed_amount',
    ]
    try:
        return {k: v for k, v in data.items if k in valid_fields}
    except:
        raise Exception('invalid request data.')


# Create your views here.
#
@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedC2(request):
    """
    sched_c2 api supporting POST, GET, DELETE, PUT
    """

    # create new sched_c2 transaction
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
            datum = schedC2_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'transaction_id' in request.data and check_null_value(
                    request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
                data = put_schedC2(datum)
            else:
                data = post_schedC2(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedC2(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedA API - POST is throwing an exception: "
                            + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        try:
            data = {
                'cmte_id': request.user.username
            }
            if 'report_id' in request.data and check_null_value(request.data.get('report_id')):
                data['report_id'] = check_report_id(
                    request.query_params.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
            datum = get_schedC2(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedC2 API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            data = {
                'cmte_id': request.user.username
            }
            if 'report_id' in request.query_params and check_null_value(request.query_params.get('report_id')):
                data['report_id'] = check_report_id(
                    request.query_params.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            if 'transaction_id' in request.query_params and check_null_value(request.query_params.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(
                    request.query_params.get('transaction_id'))
            else:
                raise Exception('Missing Input: transaction_id is mandatory')
            delete_schedD(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedD API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
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
            data = put_schedA(datum)
            # output = get_schedA(data)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedA API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    else:
        raise NotImplementedError
