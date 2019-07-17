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
# from fecfiler.sched_B.views import (delete_parent_child_link_sql_schedB,
#                                     delete_schedB, get_list_child_schedB,
#                                     get_schedB, post_schedB, put_schedB,
#                                     schedB_sql_dict)

# Create your views here.
logger = logging.getLogger(__name__)


# Create your views here.

@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedD(request):
    """
    sched_a api supporting POST, GET, DELETE, PUT
    """

    # create new sched_d transaction
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
            datum = schedD_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'creditor_entity_id' in request.data and check_null_value(request.data.get('creditor_entity_id')):
                datum['creditor_entity_id'] = request.data.get(
                    'creditor_entity_id')
            if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
                data = put_schedD(datum)
            else:
                data = post_schedD(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedD(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedA API - POST is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)
        pass

    elif reqiuest.method == 'GET':
        pass

    elif request.method == 'DELETE':
        pass

    elif request.method == 'PUT':
        pass

    else:
        raise NotImplementedError


def schedD_sql_dict(data):
    """
    filter data and build sched_d dictionary
    """
    valid_fields = [
        'cmte_id',
        'report_id',
        'transaction_type_identifier',
        'transaction_id',
        'creditor_entity_id',
        'purpose',
        'beginning_balance',
        'incurred_amount',
        'payment_amount',
        'balance_at_close',
        'delete_ind',
        'create_date',
        'last_update_date'
    ]
    try:
        return {k: v for k, v in data.items if k in valid_fields}
    except:
        raise Exception('invalid request data detected.')


def put_schedD(data):
    pass


def validate_sd_data(data):
    pass


def post_schedD(data):
    """save sched_d item and the associated entities."""
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        validate_sd_data(datum)

        # save entities rirst
        if 'creditor_entity_id' in datum:
            get_data = {
                'cmte_id': datum.get('cmte_id'),
                'creditor_entity_id': datum.get('creditor_entity_id')
            }
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
        else:
            entity_data = post_entities(datum)

        # continue to save transaction
        creditor_entity_id = entity_data.get('creditor_entity_id')
        datum['creditor_entity_id'] = creditor_entity_id
        # datum['line_number'] = disclosure_rules(datum.get('line_number'), datum.get('report_id'), datum.get('transaction_type'), datum.get('contribution_amount'), datum.get('contribution_date'), entity_id, datum.get('cmte_id'))
        trans_char = "SD"
        transaction_id = get_next_transaction_id(trans_char)
        datum['transaction_id'] = transaction_id
        try:
            post_sql_schedD(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get(
                'contribution_amount'), datum.get('purpose_description'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), datum.get('donor_cmte_name'))
        except Exception as e:
            if 'creditor_entity_id' in datum:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {
                    'cmte_id': datum.get(cmte_id),
                    'creditor_entity_id': creditor_entity_id
                }
                remove_entities(get_data)
            raise Exception(
                'The post_sql_schedD function is throwing an error: ' + str(e))
        # update line number based on aggregate amount info
        # update_linenumber_aggamt_transactions_SA(datum.get('contribution_date'), datum.get(
        #     'transaction_type'), entity_id, datum.get('cmte_id'), datum.get('report_id'))
        return datum
    except:
        raise


def get_schedD(data):
    pass
