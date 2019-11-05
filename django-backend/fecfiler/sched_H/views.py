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
                                 undo_delete_entities,
                                 check_calendar_year,
                                 )
from fecfiler.core.transaction_util import (
    get_line_number_trans_type,
    transaction_exists,
    update_sched_d_parent,
)
from fecfiler.sched_A.views import get_next_transaction_id
from fecfiler.sched_D.views import do_transaction



# Create your views here.
logger = logging.getLogger(__name__)

MANDATORY_FIELDS_SCHED_H1 = [
    'cmte_id', 
    'report_id', 
    'transaction_id', 
    'transaction_type_identifier',
    'federal_percent', 
    'non_federal_percent',
    ]
MANDATORY_FIELDS_SCHED_H2 = [
    'cmte_id', 
    'report_id', 
    'transaction_id',
    'transaction_type_identifier',
    'federal_percent', 
    'non_federal_percent',
    ]
MANDATORY_FIELDS_SCHED_H3 = ['cmte_id', 'report_id', 'transaction_id', 'transaction_type_identifier']
MANDATORY_FIELDS_SCHED_H4 = ['cmte_id', 'report_id', 'transaction_id', 'transaction_type_identifier']
MANDATORY_FIELDS_SCHED_H5 = ['cmte_id', 'report_id', 'transaction_id']
MANDATORY_FIELDS_SCHED_H6 = ['cmte_id', 'report_id', 'transaction_id']



def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SH"):
        raise Exception(
            'The Transaction ID: {} is not in the specified format.' +
            'Transaction IDs start with SH characters'.format(transaction_id))
    return transaction_id

"""
SCHED_H1:

Method of Allocation for:
- Allocated Administrative and Generic Voter Drive Costs
- Allocated Exempt Party Activity Costs (Party Committees Only)
- Allocated Public Communications that Refer to any Political Party (but not
a candidate) (Separate Segregated Funds and Nonconnected Committees
Only) 
"""

def schedH1_sql_dict(data):
    """
    filter out valid fileds for sched_H1

    """
    valid_h1_fields = [
            'line_number', 
            'transaction_type_identifier', 
            'transaction_type', 
            'presidential_only', 
            'presidential_and_senate', 
            'senate_only', 
            'non_pres_and_non_senate', 
            'federal_percent', 
            'non_federal_percent', 
            'adminstrative'
            'generic_voter_drive', 
            'public_communications',
    ]
    try:
        # return {k: v for k, v in data.items() if k in valid_h1_fields}
        datum = {k: v for k, v in data.items() if k in valid_h1_fields}
        datum['line_number'], datum['transaction_type'] = get_line_number_trans_type(
            data.get('transaction_type_identifier'))
        return datum
    except:
        raise Exception('invalid h1 request data.')

def check_mandatory_fields_SH1(data):
    """
    check madatroy frields for sh1
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H1:
            if not(field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                'The following mandatory fields are required in order to save data to schedH1 table: {}'.format(','.join(errors)))
    except:
        raise

def put_sql_schedH1(data):
    """
    sql and db_transaction for update sched_h1 item
    """
    _sql = """UPDATE public.sched_h1
                SET 
                line_number = %s, 
                transaction_type_identifier = %s, 
                transaction_type = %s, 
                presidential_only = %s, 
                presidential_and_senate = %s, 
                senate_only = %s, 
                non_pres_and_non_senate = %s, 
                federal_percent = %s, 
                non_federal_percent = %s, 
                adminstrative = %s,
                generic_voter_drive = %s, 
                public_communications = %s,
                last_update_date = %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (  
            data.get('line_number'),
            data.get('transaction_type_identifier'),
            data.get('transaction_type'),
            data.get('presidential_only'),
            data.get('presidential_and_senate'),
            data.get('senate_only'),
            data.get('non_pres_and_non_senate'),
            data.get('federal_percent'),
            data.get('non_federal_percent'),
            data.get('adminstrative'),
            data.get('generic_voter_drive'),
            data.get('public_communications'),
            datetime.datetime.now(),
            data.get('transaction_id'),
            data.get('report_id'),
            data.get('cmte_id'),
         )
    do_transaction(_sql, _v)


def put_schedH1(data):
    """
    save/update a sched_h1 item

    here we are assuming entity_id are always referencing something already in our DB
    """
    try:
        check_mandatory_fields_SH1(data)
        #check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedH1(data)
        except Exception as e:
            raise Exception(
                'The put_sql_schedH3 function is throwing an error: ' + str(e))
        return data
    except:
        raise
    
def validate_federal_nonfed_ratio(data):
    """
    validate fed and non_fed ratio add up:
    fed + non_fed == 100%
    e.g.
    0.45 + 0.55 == 1.00
    """
    if not (
        (float(data.get('federal_percent')) +
        float(data.get('non_federal_percent')) == float(1))
    ):
        raise Exception('Error: combined federal and non-federal value should be 100%.')

def validate_sh1_data(data):
    """
    validate sh1 request data for db transaction
    """
    check_mandatory_fields_SH1(data)
    validate_federal_nonfed_ratio(data)

def post_sql_schedH1(data):
    """
    save a new sched_h1 item
    """
    try:
        _sql = """
        INSERT INTO public.sched_h1 (
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            presidential_only, 
            presidential_and_senate, 
            senate_only, 
            non_pres_and_non_senate, 
            federal_percent, 
            non_federal_percent, 
            adminstrative,
            generic_voter_drive, 
            public_communications,
            create_date
            )
        VALUES ({}); 
        """.format(','.join(['%s']*16))
        _v = (
            data.get('cmte_id'),
            data.get('report_id'),
            data.get('line_number'),
            data.get('transaction_type_identifier'),
            data.get('transaction_type'),
            data.get('transaction_id'),
            data.get('presidential_only'),
            data.get('presidential_and_senate'),
            data.get('senate_only'),
            data.get('non_pres_and_non_senate'),
            data.get('federal_percent'),
            data.get('non_federal_percent'),
            data.get('adminstrative'),
            data.get('generic_voter_drive'),
            data.get('public_communications'),
            datetime.datetime.now(),   
         )
        with connection.cursor() as cursor:
            # Insert data into schedH3 table
            cursor.execute(_sql, _v)
    except Exception:
        raise

def post_schedH1(data):
    """
    save a new sched_h1 item
    """ 
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        data['transaction_id'] = get_next_transaction_id('SH')
        validate_sh1_data(data)
        try:
            post_sql_schedH1(data)
        except Exception as e:
            raise Exception(
                'The post_sql_schedH1 function is throwing an error: ' + str(e))
        return data
    except:
        raise

def get_schedH1(data):
    """
    load sched_h1 items
    """
 
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        if 'transaction_id' in data:
            transaction_id = check_transaction_id(data.get('transaction_id'))
            forms_obj = get_list_schedH1(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedH1(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedH1(report_id, cmte_id):
    """
    load all transactions for a report
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            presidential_only, 
            presidential_and_senate, 
            senate_only, 
            non_pres_and_non_senate, 
            federal_percent, 
            non_federal_percent, 
            adminstrative,
            generic_voter_drive, 
            public_communications,
            create_date ,
            last_update_date
            FROM public.sched_h1
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedH1_list = cursor.fetchone()[0]
            if schedH1_list is None:
                raise NoOPError('No sched_H1 transaction found for report_id {} and cmte_id: {}'.format(
                    report_id, cmte_id))
            merged_list = []
            for dictH1 in schedH1_list:
                merged_list.append(dictH1)
        return merged_list
    except Exception:
        raise


def get_list_schedH1(report_id, cmte_id, transaction_id):
    """
    load one transaction
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH3 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            presidential_only, 
            presidential_and_senate, 
            senate_only, 
            non_pres_and_non_senate, 
            federal_percent, 
            non_federal_percent, 
            adminstrative,
            generic_voter_drive, 
            public_communications,
            create_date ,
            last_update_date
            FROM public.sched_h1
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH1_list = cursor.fetchone()[0]
            if schedH1_list is None:
                raise NoOPError('No sched_H1 transaction found for transaction_id {}'.format(
                    transaction_id))
            merged_list = []
            for dictH1 in schedH1_list:
                merged_list.append(dictH1)
        return merged_list
    except Exception:
        raise



def delete_sql_schedH1(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """
    UPDATE public.sched_h1
    SET delete_ind = 'Y' 
    WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
    """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH1(data):
    """
    function for handling delete request for sh1
    """
    try:
        delete_sql_schedH1(data.get('cmte_id'), data.get(
            'report_id'), data.get('transaction_id'))
    except Exception as e:
        raise

@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedH1(request):
    
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
            datum = schedH1_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id

            if 'transaction_id' in request.data and check_null_value(
                    request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
                data = put_schedH1(datum)
            else:
                print(datum)
                data = post_schedH1(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedH1(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH1 API - POST is throwing an exception: "
                            + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
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
            datum = get_schedH1(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH1 API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
            delete_schedH1(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH1 API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            datum = schedH1_sql_dict(request.data)
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
            data = put_schedH1(datum)
            # output = get_schedA(data)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH1 API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    else:
        raise NotImplementedError

@api_view(['GET'])
def get_fed_nonfed_share(request):
    """
    get calendar year fed_nonfed share percentage, also query aggregation
    and update aggregation value.

    if event_name is available:
        go to h2 for ration
        grab event-based aggregation value from h4
    else:
        go to h1 for ratio
            if party, get election_year based fixed ratio
            if PAC, get activity based ratio
        grad event_type-based aggregation value from h4
    calculate fed and non-fed share based on ratio and update aggregate value
    """

    logger.debug('get_fed_nonfed_share with request:{}'.format(request.query_params))
    try:
        cmte_id = request.user.username
        cmte_type_category = request.query_params.get('cmte_type_category')
        total_amount = request.query_params.get('total_amount')
        calendar_year = check_calendar_year(request.query_params.get('calendar_year'))
        start_dt = datetime.date(int(calendar_year), 1, 1)
        end_dt = datetime.date(int(calendar_year), 12, 31)
        event_name = request.query_params.get('activity_event_identifier') 

        if event_name: # event-based, goes to h2
            _sql = """
            select federal_percent 
            from public.sched_h2 
            where cmte_id = %s 
            and activity_event_name = %s
            and create_date between %s and %s
            """
            with connection.cursor() as cursor:
                logger.debug('query with _sql:{}'.format(_sql))
                logger.debug('query with {}, {}, {}, {}'.format(cmte_id, event_name, start_dt, end_dt))
                cursor.execute(_sql, (cmte_id, event_name, start_dt, end_dt))
                if not cursor.rowcount:
                    raise Exception('Error: no h1 data found.')
                fed_percent = float(cursor.fetchone()[0])

            _sql = """
            select activity_event_amount_ytd 
            from public.sched_h4 
            where cmte_id = %s 
            and activity_event_identifier = %s
            and create_date between %s and %s
            order by create_date desc, last_update_date desc;
            """
            with connection.cursor() as cursor:
                cursor.execute(_sql, (cmte_id, event_name, start_dt, end_dt))
                if not cursor.rowcount:
                    aggregate_amount = 0 
                else:
                    aggregate_amount = float(cursor.fetchone()[0])

        else: # need to go to h1 for ratios
            activity_event_type = request.query_params.get('activity_event_type')

            # # TODO: need to db change to fix this typo
            # if activity_event_type == 'administrative':
            #     activity_event_type = 'adminstrative'

            if not activity_event_type:
                raise Exception('Error: event type is required.')
            
            if cmte_type_category == 'PTY':
                _sql = """
                select federal_percent from public.sched_h1
                where create_date between %s and %s
                and cmte_id = %s
                order by create_date desc, last_update_date desc
                """
                logger.debug('sql for query h1:{}'.format(_sql))
                with connection.cursor() as cursor:
                    cursor.execute(_sql, (start_dt, end_dt, cmte_id))
                    if not cursor.rowcount:
                        raise Exception('Error: no h1 data found.')
                    fed_percent = float(cursor.fetchone()[0])
            elif cmte_type_category == 'PAC':
                # activity_event_type = request.query_params.get('activity_event_type')
                # if not activity_event_type:
                    # return Response('Error: event type is required for this committee.')
                event_type_code = {
                    "AD" : "adminstrative", # TODO: need to fix this typo
                    "GV" : "generic_voter_drive",
                    "PC" : "public_communications",
                }
                h1_event_type = event_type_code.get(activity_event_type)
                if not h1_event_type:
                    return Response('Error: activity type not valid')
                _sql = """
                select federal_percent from public.sched_h1
                where create_date between %s and %s
                and cmte_id = %s
                """
                activity_part = """and {} = true """.format(h1_event_type)
                order_part = 'order by create_date desc, last_update_date desc'
                _sql = _sql + activity_part + order_part
                logger.debug('sql for query h1:{}'.format(_sql))
                with connection.cursor() as cursor:
                    cursor.execute(_sql, (start_dt, end_dt, cmte_id))
                    if not cursor.rowcount:
                        raise Exception('Error: no h1 data found.')
                    fed_percent = float(cursor.fetchone()[0])
            else:
                raise Exception('invalid cmte_type_category.')

            _sql = """
                select activity_event_amount_ytd 
                from public.sched_h4 
                where cmte_id = %s 
                and activity_event_type = %s
                and create_date between %s and %s
                order by create_date desc, last_update_date desc
            """
            with connection.cursor() as cursor:
                cursor.execute(_sql, (cmte_id, activity_event_type, start_dt, end_dt))
                if not cursor.rowcount:
                    aggregate_amount = 0
                else:
                    aggregate_amount = float(cursor.fetchone()[0])
        # fed_percent = float(cursor.fetchone()[0])
        fed_share = float(total_amount) * fed_percent
        nonfed_share = float(total_amount) - fed_share
        new_aggregate_amount = aggregate_amount + float(total_amount)
        return JsonResponse(
            {
                'fed_share': '{0:.2f}'.format(fed_share), 
                'nonfed_share': '{0:.2f}'.format(nonfed_share),
                'aggregate_amount': '{0:.2f}'.format(new_aggregate_amount),
            }, 
                status = status.HTTP_200_OK
        )
    except:
        raise


@api_view(['GET'])
def get_h1_percentage(request):
    """
    get calendar year fed_nonfed share percentage
    """
    logger.debug('get_h1_percentage with request:{}'.format(request.query_params))
    try:
        cmte_id = request.user.username

        # if not('report_id' in request.query_params and check_null_value(request.query_params.get('report_id'))):
            # raise Exception ('Missing Input: report_id is mandatory')

        if not('calendar_year' in request.query_params and check_null_value(request.query_params.get('calendar_year'))):
            raise Exception ('Missing Input: calendar_year is mandatory')
        calendar_year = check_calendar_year(request.query_params.get('calendar_year'))
        start_dt = datetime.date(int(calendar_year), 1, 1)
        end_dt = datetime.date(int(calendar_year), 12, 31)
        _sql = """
            select json_agg(t) from
            (select federal_percent, non_federal_percent from public.sched_h1
            where create_date between %s and %s
            and cmte_id = %s
            order by create_date desc, last_update_date desc) t
        """
        with connection.cursor() as cursor:
            cursor.execute(_sql, (start_dt, end_dt, cmte_id))
            # print('rows:{}'.format(cursor.rowcount))
            json_data = cursor.fetchone()[0]
            print(json_data)
            if not json_data:
                # raise Exception('Error: no h1 found.')
                return Response("The schedH1 API - PUT is throwing an error: no h1 data found.", 
                status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse(json_data[0], status = status.HTTP_200_OK)
    except:
        raise


"""
SCHED_H2:
Ratios for Allocable Fundraising Events and Direct Candidate Support 
"""

def schedH2_sql_dict(data):
    """
    filter out valid fileds for sched_H1
    """
    valid_h2_fields = [
        # "line_number",
        "transaction_type_identifier",
        # "transaction_type",
        "activity_event_name",
        "fundraising",
        "direct_cand_support",
        "ratio_code",
        "federal_percent",
        "non_federal_percent",
    ]
    try:
        # return {k: v for k, v in data.items() if k in valid_h2_fields}
        datum = {k: v for k, v in data.items() if k in valid_h2_fields}
        datum['line_number'], datum['transaction_type'] = get_line_number_trans_type(
            data.get('transaction_type_identifier'))
        return datum
    except:
        raise Exception('invalid h2 request data.')

def check_mandatory_fields_SH2(data):
    """
    check madatroy frields for sh1
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H2:
            if not(field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                'The following mandatory fields are required in order to save data to schedH2 table: {}'.format(','.join(errors)))
    except:
        raise

def put_sql_schedH2(data):
    """
    sql and db_transaction for update sched_h1 item
    """
    _sql = """UPDATE public.sched_h2
            SET 
                line_number = %s, 
                transaction_type_identifier = %s, 
                transaction_type = %s,
                activity_event_name = %s,
                fundraising = %s,
                direct_cand_support = %s,
                ratio_code = %s,
                federal_percent = %s,
                non_federal_percent = %s,
                last_update_date = %s
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
            AND delete_ind is distinct from 'Y';
        """
    _v = (  
            data.get('line_number'),
            data.get('transaction_type_identifier'),
            data.get('transaction_type'),
            data.get('activity_event_name'),
            data.get('fundraising'),
            data.get('direct_cand_support'),
            data.get('ratio_code'),
            data.get('federal_percent'),
            data.get('non_federal_percent'),
            datetime.datetime.now(),
            data.get('transaction_id'),
            data.get('report_id'),
            data.get('cmte_id'),
         )
    do_transaction(_sql, _v)


def put_schedH2(data):
    """
    save/update a sched_h2 item

    here we are assuming entity_id are always 
    referencing something already in our DB
    """
    try:
        # check_mandatory_fields_SH2(data)
        validate_sh2_data(data)
        #check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedH2(data)
        except Exception as e:
            raise Exception(
                'The put_sql_schedH2 function is throwing an error: ' + str(e))
        return data
    except:
        raise
    
def validate_sh2_data(data):
    """
    validate sh1 request data for db transaction
    """
    check_mandatory_fields_SH2(data)
    validate_federal_nonfed_ratio(data)

def post_sql_schedH2(data):
    """
    save a new sched_h1 item
    """
    try:
        _sql = """
        INSERT INTO public.sched_h2 (
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            activity_event_name,
            fundraising,
            direct_cand_support,
            ratio_code,
            federal_percent,
            non_federal_percent,
            create_date
            )
        VALUES ({}); 
        """.format(','.join(['%s']*13))
        _v = (
            data.get('cmte_id'),
            data.get('report_id'),
            data.get('line_number'),
            data.get('transaction_type_identifier'),
            data.get('transaction_type'),
            data.get('transaction_id'),
            data.get('activity_event_name'),
            data.get('fundraising'),
            data.get('direct_cand_support'),
            data.get('ratio_code'),
            data.get('federal_percent'),
            data.get('non_federal_percent'),
            datetime.datetime.now() 
         )
        with connection.cursor() as cursor:
            # Insert data into schedH3 table
            cursor.execute(_sql, _v)
    except Exception:
        raise

def post_schedH2(data):
    """
    save a new sched_h1 item
    """ 
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        data['transaction_id'] = get_next_transaction_id('SH')
        validate_sh2_data(data)
        try:
            post_sql_schedH2(data)
        except Exception as e:
            raise Exception(
                'The post_sql_schedH2 function is throwing an error: ' + str(e))
        return data
    except:
        raise

def get_schedH2(data):
    """
    load sched_h1 items
    """
 
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        if 'transaction_id' in data:
            transaction_id = check_transaction_id(data.get('transaction_id'))
            forms_obj = get_list_schedH2(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedH2(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedH2(report_id, cmte_id):
    """
    load all transactions for a report
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            activity_event_name,
            fundraising,
            direct_cand_support,
            ratio_code,
            federal_percent,
            non_federal_percent,
            create_date ,
            last_update_date
            FROM public.sched_h2
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedH_list = cursor.fetchone()[0]
            if schedH_list is None:
                raise NoOPError('No sched_H2 transaction found for report_id {} and cmte_id: {}'.format(
                    report_id, cmte_id))
            merged_list = []
            for dictH in schedH_list:
                merged_list.append(dictH)
        return merged_list
    except Exception:
        raise


def get_list_schedH2(report_id, cmte_id, transaction_id):
    """
    load one transaction
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH3 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            activity_event_name,
            fundraising,
            direct_cand_support,
            ratio_code,
            federal_percent,
            non_federal_percent,
            create_date ,
            last_update_date
            FROM public.sched_h2
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH_list = cursor.fetchone()[0]
            if schedH_list is None:
                raise NoOPError('No sched_H2 transaction found for transaction_id {}'.format(
                    transaction_id))
            merged_list = []
            for dictH in schedH_list:
                merged_list.append(dictH)
        return merged_list
    except Exception:
        raise



def delete_sql_schedH2(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """
    UPDATE public.sched_h2
    SET delete_ind = 'Y' 
    WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
    """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH2(data):
    """
    function for handling delete request for sh1
    """
    try:
        delete_sql_schedH2(data.get('cmte_id'), data.get(
            'report_id'), data.get('transaction_id'))
    except Exception as e:
        raise

@api_view(['GET'])
def get_h2_type_events(request):
    """
    load all event names for each category(direct cand support or 
    fundraising) to populate events dropdown list
    """
    logger.debug('get_h2_type_events with request:{}'.format(request.query_params))
    cmte_id = request.user.username
    event_type = request.query_params.get('activity_event_type').strip()
    if event_type not in ['fundraising', 'direct_cand_support']:
        raise Exception('missing or non-valid event type value')
    if event_type == 'findraising':
        _sql = """
        SELECT json_agg(t) from (
        SELECT activity_event_name 
        FROM   public.sched_h2 
        WHERE  cmte_id = '{}'
            AND fundraising = true) t;
        """.format(cmte_id)
    else:
        _sql = """
        SELECT json_agg(t) from(
        SELECT activity_event_name 
        FROM   public.sched_h2 
        WHERE  cmte_id = '{}'
            AND direct_cand_support = true) t;
        """.format(cmte_id)
    try:
        with connection.cursor() as cursor:
            logger.debug('query with _sql:{}'.format(_sql))
            cursor.execute(_sql)
            json_res = cursor.fetchone()[0]
            # print(json_res)
            if not json_res:
                return Response([], status = status.HTTP_200_OK)
        # calendar_year = check_calendar_year(request.query_params.get('calendar_year'))
        # start_dt = datetime.date(int(calendar_year), 1, 1)
        # end_dt = datetime.date(int(calendar_year), 12, 31)
        return Response( json_res, status = status.HTTP_200_OK)
    except:
        raise

@api_view(['GET'])
def get_h2_summary_table(request):
    """
    h2 summary need to be h4 transaction-based:
    all the calendar-year based h2 need to show up for current report as long as
    a live h4 transaction refering this h2 exist:
    h2 report goes with h4, not h2 report_id

    update: all h2 items with current report_id need to show up
    """
    logger.debug('get_h2_summary_table with request:{}'.format(request.query_params))
    _sql = """
    SELECT json_agg(t) from(
    SELECT activity_event_name, 
        ( CASE fundraising 
            WHEN true THEN 'fundraising' 
            ELSE 'direct_cand_suppot' 
            END )  AS event_type, 
        DATE(create_date) AS date, 
        ratio_code, 
        federal_percent, 
        non_federal_percent 
    FROM   public.sched_h2 
    WHERE  cmte_id = %s AND delete_ind is distinct from 'Y'
        AND activity_event_name IN (
            SELECT activity_event_identifier 
            FROM   public.sched_h4 
            WHERE  report_id = %s
            AND cmte_id = %s)
    UNION SELECT activity_event_name, 
        ( CASE fundraising 
            WHEN true THEN 'fundraising' 
            ELSE 'direct_cand_suppot' 
            END )  AS event_type, 
        DATE(create_date) AS date, 
        ratio_code, 
        federal_percent, 
        non_federal_percent 
    FROM   public.sched_h2 
    WHERE  cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'
            ) t;
    """
    try:
        cmte_id = request.user.username
        report_id = request.query_params.get('report_id')
        with connection.cursor() as cursor:
            logger.debug('query with _sql:{}'.format(_sql))
            logger.debug('query with cmte_id:{}, report_id:{}'.format(cmte_id, report_id))
            cursor.execute(_sql, (cmte_id, report_id, cmte_id, cmte_id, report_id))
            json_res = cursor.fetchone()[0]
            print(json_res)
            if not json_res:
                return Response('Error: no valid h2 data found for this report.')
        # calendar_year = check_calendar_year(request.query_params.get('calendar_year'))
        # start_dt = datetime.date(int(calendar_year), 1, 1)
        # end_dt = datetime.date(int(calendar_year), 12, 31)
        return Response( json_res, status = status.HTTP_200_OK)
    except:
        raise

@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedH2(request):
    
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
            datum = schedH2_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id

            if 'transaction_id' in request.data and check_null_value(
                    request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
                data = put_schedH2(datum)
            else:
                print(datum)
                data = post_schedH2(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedH2(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH2 API - POST is throwing an exception: "
                            + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
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
            datum = get_schedH2(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH2 API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
            delete_schedH2(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH2 API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            datum = schedH2_sql_dict(request.data)
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

            data = put_schedH2(datum)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH2 API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    else:
        raise NotImplementedError


"""
************************************************************************
SCHED_H3
Transfers from Nonfederal Accounts for Allocated Federal/Nonfederal Activity
***********************************************************************
"""
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
            'cmte_id',
            'report_id',
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
            data.get('transaction_type_identifier'),
            data.get('transaction_id'),
            data.get('back_ref_transaction_id'),
            data.get('back_ref_sched_name'),
            data.get('account_name'),
            data.get('activity_event_type'),
            data.get('activity_event_name'),
            data.get('receipt_date'),
            data.get('total_amount_transferred'),
            data.get('transferred_amount'),
            data.get('memo_code'),
            data.get('memo_text'),
            datetime.datetime.now(), 
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
            for _obj in forms_obj:
                child_list = get_child_schedH3(transaction_id, report_id, cmte_id)
                _obj['child'] = child_list
        else:
            forms_obj = get_list_all_schedH3(report_id, cmte_id)
            for _obj in forms_obj:
                transaction_id = _obj.get('transaction_id')
                child_list = get_child_schedH3(transaction_id, report_id, cmte_id)
                _obj['child'] = child_list
        return forms_obj
    except:
        raise

def get_child_schedH3(transaction_id, report_id, cmte_id):
    """
    load all child transaction for each parent H3
    """
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
            WHERE report_id = %s 
            AND cmte_id = %s
            AND back_ref_transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH3_list = cursor.fetchone()[0]
            if schedH3_list is None:
                raise NoOPError('No sched_H3 transaction found for report_id {} and cmte_id: {}'.format(
                    report_id, cmte_id))
            # merged_list = []
            # for dictH3 in schedH3_list:
            #     merged_list.append(dictH3)
        return schedH3_list
    except Exception:
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

@api_view(['GET'])
def get_sched_h3_breakdown(request):
    _sql = """
    SELECT json_agg(t) FROM(
    SELECT activity_event_type, sum(total_amount_transferred) 
    FROM public.sched_h3 
    WHERE report_id = %s 
    AND cmte_id = %s
    AND delete_ind is distinct from 'Y'
    GROUP BY activity_event_type
    union 
	SELECT 'total', sum(total_amount_transferred) 
    FROM public.sched_h3 
    WHERE report_id = %s 
    AND cmte_id = %s
    AND delete_ind is distinct from 'Y') t
    """
    try:
        cmte_id = request.user.username
        if not('report_id' in request.query_params):
            raise Exception('Missing Input: Report_id is mandatory')
        # handling null,none value of report_id
        if not (check_null_value(request.query_params.get('report_id'))):
            report_id = "0"
        else:
            report_id = check_report_id(request.query_params.get('report_id'))
        with connection.cursor() as cursor:
            cursor.execute(_sql, [report_id, cmte_id, report_id, cmte_id])
            result = cursor.fetchone()[0]
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        raise Exception('Error on fetching h3 break down')
        

@api_view(['GET'])
def get_h3_total_amount(request):
    """
    get h3 total_amount for editing purpose
    if a event_name is provided, will get the total amount based on event name
    if a event_type is provided, will get the total amount based on event type
    """
    try:
        cmte_id = request.user.username
        logger.debug('get_h3_total_amount with request:{}'.format(request.query_params))
        if 'activity_event_name' in request.query_params: 
            event_name = request.query_params.get('activity_event_name') 
            _sql = """
            SELECT json_agg(t) from(
            SELECT total_amount_transferred
            FROM   public.sched_h3 
            WHERE  cmte_id = %s
                AND activity_event_name = %s
            ORDER BY receipt_date desc, create_date desc) t
            """
            with connection.cursor() as cursor:
                logger.debug('query with _sql:{}'.format(_sql))
                # logger.debug('query with cmte_id:{}, report_id:{}'.format(cmte_id, report_id))
                cursor.execute(_sql, (cmte_id, event_name))
                json_res = cursor.fetchone()[0]
        else:
            event_type = request.query_params.get('activity_event_type') 
            if not event_type:
                raise Exception("event name or event type is required for this api")
            _sql = """
            SELECT json_agg(t) from(
            SELECT total_amount_transferred
            FROM   public.sched_h3 
            WHERE  cmte_id = %s
                AND activity_event_type = %s
            ORDER BY receipt_date desc, create_date desc) t
            """ 
            with connection.cursor() as cursor:
                logger.debug('query with _sql:{}'.format(_sql))
                # logger.debug('query with cmte_id:{}, report_id:{}'.format(cmte_id, report_id))
                cursor.execute(_sql, (cmte_id, event_type))
                json_res = cursor.fetchone()[0]
        
            # print(json_res)
        if not json_res:
            return Response(
                {
                    "total_amount_transferred": 0
                }, 
                    status = status.HTTP_200_OK)
        # calendar_year = check_calendar_year(request.query_params.get('calendar_year'))
        # start_dt = datetime.date(int(calendar_year), 1, 1)
        # end_dt = datetime.date(int(calendar_year), 12, 31)
        return Response( json_res[0], status = status.HTTP_200_OK)
    except:
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
                if 'child' in request.data:
                    for _c in request.data['child']:
                        parent_data = data 
                        _c.update(parent_data)
                        _c['back_ref_transaction_id'] = parent_data['transaction_id']
                        _c = schedH3_sql_dict(request.data)
                        put_schedH3(_c) 
            else:
                # print(datum)
                logger.debug('saving h3 with data {}'.format(datum))
                data = post_schedH3(datum)
                logger.debug('parent data saved:{}'.format(data))
                if 'child' in request.data:
                    for _c in request.data['child']:
                        child_data = data 
                        child_data.update(_c)
                        child_data['back_ref_transaction_id'] = data['transaction_id']
                        child_data = schedH3_sql_dict(child_data)
                        logger.debug('saving child transaction with data {}'.format(child_data))
                        post_schedH3(child_data) 
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
            if 'report_id' in request.query_params and check_null_value(request.query_params.get('report_id')):
                data['report_id'] = check_report_id(
                    request.query_params.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            if 'transaction_id' in request.query_params and check_null_value(request.query_params.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(
                    request.query_params.get('transaction_id'))
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

Disbursements for Allocated Federal/Nonfederal Activity
some check points:
1. when h4 activity is submitted, make sure an h1 or h2 is there to calcualte 
   the fed and non-fed amount
2. when a memo transaction is submitted, need to verify the parent transaction exist

"""
SCHED_H4_CHILD_TRANSACTIONS = [
    'ALLOC_EXP_CC_PAY_MEMO',
    'ALLOC_EXP_STAF_REIM_MEMO',
    'ALLOC_EXP_PMT_TO_PROL_MEMO'
]

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
    logger.debug('request data:{}'.format(data))
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
                    # entity_data
            "entity_id",
            "entity_type",
            "entity_name",
            "first_name",
            "last_name",
            "middle_name",
            "preffix",
            "suffix",
            "street_1",
            "street_2",
            "city",
            "state",
            "zip_code",
            "occupation",
            "employer",
            "ref_cand_cmte_id",
            "cand_office",
            "cand_office_state",
            "cand_office_district",
            "cand_election_year",
            "phone_number",     
    ]
    try:
        # return {k: v for k, v in data.items() if k in valid_fields}
        valid_data = {k: v for k, v in data.items() if k in valid_fields}
        line_num, tran_tp = get_line_number_trans_type(
            data["transaction_type_identifier"]
        )

        valid_data["line_number"] = line_num
        valid_data['transaction_type'] = tran_tp
        # TODO: this is a temp code change, we need to update h4,h6 
        # to unify the field names
        if 'expenditure_purpose' in data:
            valid_data['purpose'] = data.get('expenditure_purpose', '')
        return valid_data
    except:
        raise Exception('invalid request data.')

def get_existing_h4_total(cmte_id, transaction_id):
    """
    fetch existing close balance in the db for current transaction
    """
    _sql = """
    select total_amount
    from public.sched_h4
    where cmte_id = %s
    and transaction_id = %s
    """
    _v = (cmte_id, transaction_id)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, _v)
            return cursor.fetchone()[0]
    except:
        raise


def put_schedH4(data):
    """
    update sched_H4 item
    
    """
    try:
        check_mandatory_fields_SH4(data)
        if "entity_id" in data:
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"

            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(data)
            roll_back = True
        else:
            entity_data = post_entities(data)
            roll_back = False

        # continue to save transaction
        entity_id = entity_data.get("entity_id")
        data["entity_id"] = entity_id
        data['payee_entity_id'] = entity_id
        #check_transaction_id(data.get('transaction_id'))

        existing_total = get_existing_h4_total(
            data.get('cmte_id'),
            data.get('transaction_id')
        )
        try:
            put_sql_schedH4(data)
            update_activity_event_amount_ytd(data)
                        
            # if debt payment, update parent sched_d
            if data.get('transaction_type_identifier') == 'ALLOC_EXP_DEBT':
                if float(existing_total) != float(data.get('total_amount')):
                    update_sched_d_parent(
                        data.get('cmte_id'),
                        data.get('back_ref_transaction_id'),
                        data.get('total_amount'),
                        existing_total
                    )
        except Exception as e:
            if roll_back:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": data.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
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
                  line_number = %s, 
                  transaction_type = %s,
                  last_update_date= %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y'
        """
    _v = (  
           
            data.get('transaction_type_identifier'),
            data.get('back_ref_transaction_id'),
            data.get('back_ref_sched_name'),
            data.get('payee_entity_id'),
            data.get('activity_event_identifier'),
            data.get('expenditure_date'),
            data.get('fed_share_amount'),
            data.get('non_fed_share_amount'),
            data.get('total_amount'),
            data.get('activity_event_amount_ytd'),
            data.get('purpose'),
            data.get('category_code'),
            data.get('activity_event_type'),
            data.get('memo_code'),
            data.get('memo_text'),
            data.get('line_number'),
            data.get('transaction_type'),
            datetime.datetime.now(),
            data.get('transaction_id'),
            data.get('report_id'),
            data.get('cmte_id'),
         )
    do_transaction(_sql, _v)


def validate_parent_transaction_exist(data):
    """
    validate parent transaction exsit if saving a child transaction
    """
    # if data.get("transaction_type_identifier") in SCHED_H4_CHILD_TRANSACTIONS:
    if not data.get("back_ref_transaction_id"):
        raise Exception("Error: parent transaction id missing.")
    elif not transaction_exists(
        data.get("back_ref_transaction_id"), "sched_h4"
    ):
        raise Exception("Error: parent transaction not found.")
    else:
        pass

def validate_fed_nonfed_share(data):
    if (float(data.get('fed_share_amount')) + 
        float(data.get('non_fed_share_amount')) != float(data.get('total_amount'))):
        raise Exception('Error: fed_amount and non_fed_amount should sum to total amount.')

def validate_sh4_data(data):
    """
    validate sH4 json data
    """
    check_mandatory_fields_SH4(data)
    validate_fed_nonfed_share(data)
    if data.get("transaction_type_identifier") in SCHED_H4_CHILD_TRANSACTIONS:
        validate_parent_transaction_exist(data)


def list_all_transactions_event_type(start_dt, end_dt, activity_event_type, cmte_id):
    """
    load all transactions with the specified activity event type
    need to check
    """
    logger.debug('load ttransactionsransactions with activity_event_type:{}'.format(activity_event_type))
    # logger.debug('load ttransactionsransactions with start:{}, end {}'.format(start_dt, end_dt))
    # logger.debug('load ttransactionsransactions with cmte-id:{}'.format(cmte_id))
    _sql = """
            SELECT t1.total_amount, 
                t1.transaction_id
            FROM public.sched_h4 t1 
            WHERE activity_event_type = %s 
            AND cmte_id = %s
            AND expenditure_date >= %s
            AND expenditure_date <= %s 
            AND back_ref_transaction_id is null
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY expenditure_date ASC, create_date ASC
    """
    # .format(activity_event_type, cmte_id, start_dt, end_dt)
    logger.debug(_sql)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (activity_event_type, cmte_id, start_dt, end_dt))
            # , [
            #         activity_event_type, 
            #         cmte_id, 
            #         start_dt, 
            #         end_dt,
            #     ])
            transactions_list = cursor.fetchall()
            logger.debug('transaction fetched:{}'.format(transactions_list))
        return transactions_list
    except Exception as e:
        raise Exception(
            'The list_all_transactions_event_type function is throwing an error: ' + str(e))

def list_all_transactions_event_identifier(start_dt, end_dt, activity_event_identifier, cmte_id):
    """
    load all transactions with the specified activity event type
    need to check
    """
    logger.debug('load ttransactionsransactions with activity_event_identifier:{}'.format(activity_event_identifier))
    # logger.debug('load ttransactionsransactions with start:{}, end {}'.format(start_dt, end_dt))
    # logger.debug('load ttransactionsransactions with cmte-id:{}'.format(cmte_id))
    _sql = """
            SELECT t1.total_amount, 
                t1.transaction_id
            FROM public.sched_h4 t1 
            WHERE activity_event_identifier = %s 
            AND cmte_id = %s
            AND expenditure_date >= %s
            AND expenditure_date <= %s 
            AND back_ref_transaction_id is null
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY expenditure_date ASC, create_date ASC
    """
    # .format(activity_event_type, cmte_id, start_dt, end_dt)
    logger.debug(_sql)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (activity_event_identifier, cmte_id, start_dt, end_dt))
            # , [
            #         activity_event_type, 
            #         cmte_id, 
            #         start_dt, 
            #         end_dt,
            #     ])
            transactions_list = cursor.fetchall()
            logger.debug('transaction fetched:{}'.format(transactions_list))
        return transactions_list
    except Exception as e:
        raise Exception(
            'The list_all_transactions_event_identifier function is throwing an error: ' + str(e))

def update_transaction_ytd_amount(cmte_id, transaction_id, aggregate_amount):

    """
    update h4 ytd amount
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """ UPDATE public.sched_h4
                    SET activity_event_amount_ytd = %s 
                    WHERE transaction_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'
                    """,
                    [aggregate_amount, transaction_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception(
                    'Error: The Transaction ID: {} does not exist in schedH4 table'.format(transaction_id))
    except Exception:
        raise    

def update_activity_event_amount_ytd(data):
    """
    aggregate and update 'activity_event_amount_ytd' for all h4 transactions
    if event_identifier is provided, will do event-based aggregation;
    else will do event_type-based aggregation
    """
    try:

        logger.debug('updating ytd amount:')
        # make sure transaction list comes back sorted by contribution_date ASC
        expenditure_dt = date_format(data.get('expenditure_date'))
        aggregate_start_date = datetime.date(expenditure_dt.year, 1, 1)
        aggregate_end_date = datetime.date(expenditure_dt.year, 12, 31)
        if data.get('activity_event_identifier'):
            transactions_list = list_all_transactions_event_identifier(
                aggregate_start_date, 
                aggregate_end_date, 
                data.get('activity_event_identifier'), 
                data.get('cmte_id') 
            )
        else:
            transactions_list = list_all_transactions_event_type(
                aggregate_start_date, 
                aggregate_end_date, 
                data.get('activity_event_type'), 
                data.get('cmte_id')
                )
        aggregate_amount = 0
        for transaction in transactions_list:
            aggregate_amount += transaction[0]
            transaction_id = transaction[1]
            update_transaction_ytd_amount(data.get('cmte_id'), transaction_id, aggregate_amount)

    except Exception as e:
        raise Exception(
            'The update_activity_event_amount_ytd function is throwing an error: ' + str(e))


def post_schedH4(data):
    """
    function for handling POST request for sH4, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        if "entity_id" in data:
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"

            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(data)
            roll_back = True
        else:
            entity_data = post_entities(data)
            roll_back = False

        # continue to save transaction
        entity_id = entity_data.get("entity_id")
        data['entity_id'] = entity_id
        data["payee_entity_id"] = entity_id
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_H4)
        data['transaction_id'] = get_next_transaction_id('SH4')
        logger.debug('saving a new h4 transaction with data:{}'.format(data))
        validate_sh4_data(data)
        try:
            post_sql_schedH4(data)
            update_activity_event_amount_ytd(data)

            # sched_d debt payment, need to update parent
            if data.get('transaction_type_identifier') == 'ALLOC_EXP_DEBT':
                update_sched_d_parent(
                    data.get('cmte_id'),
                    data.get('back_ref_transaction_id'),
                    data.get('total_amount')
                )
        except Exception as e:
            if roll_back:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": data.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
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
            line_number,
            transaction_type,
            create_date
            )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get('cmte_id'),
            data.get('report_id'),
            data.get('transaction_type_identifier'),
            data.get('transaction_id'),
            data.get('back_ref_transaction_id'),
            data.get('back_ref_sched_name'),
            data.get('payee_entity_id'),
            data.get('activity_event_identifier'),
            data.get('expenditure_date'),
            data.get('fed_share_amount'),
            data.get('non_fed_share_amount'),
            data.get('total_amount'),
            data.get('activity_event_amount_ytd'),
            data.get('purpose'),
            data.get('category_code'),
            data.get('activity_event_type'),
            data.get('memo_code'),
            data.get('memo_text'),
            data.get('line_number'),
            data.get('transaction_type'),
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

        # TODO: temp change, need to reove this code when h4, h6 schedma updated  
        for obj in forms_obj:
            obj['expenditure_purpose'] = obj.get('purpose', '')

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
            line_number,
            transaction_type,
            create_date ,
            last_update_date
            FROM public.sched_h4
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            tran_list = cursor.fetchone()[0]
            if tran_list is None:
                raise NoOPError('No sched_H4 transaction found for report_id {} and cmte_id: {}'.format(
                    report_id, cmte_id))
            merged_list = []
            for tran in tran_list:
                entity_id = tran.get("payee_entity_id")
                q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
                dictEntity = get_entities(q_data)[0]
                merged_list.append({**tran, **dictEntity})
                # merged_list.append(dictH4)
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
            line_number,
            transaction_type,
            create_date,
            last_update_date
            FROM public.sched_h4
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            tran_list = cursor.fetchone()[0]
            if not tran_list:
                raise NoOPError('No sched_H4 transaction found for transaction_id {}'.format(
                    transaction_id))
            merged_list = []
            for tran in tran_list:
                entity_id = tran.get("payee_entity_id")
                q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
                dictEntity = get_entities(q_data)[0]
                merged_list.append({**tran, **dictEntity})
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
                # print(datum)
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
            if 'report_id' in request.query_params and check_null_value(request.query_params.get('report_id')):
                data['report_id'] = check_report_id(
                    request.query_params.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            if 'transaction_id' in request.query_params and check_null_value(request.query_params.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(
                    request.query_params.get('transaction_id'))
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
            output = get_schedH4(data)[0]
            # output = get_schedA(data)
            return JsonResponse(output, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH4 API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    else:
        raise NotImplementedError



"""

************************************************** CRUD API FOR SCHEDULE_H5 ***********************************************************************************

"""

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


@api_view(['GET'])
def get_sched_h5_breakdown(request):
    """
    api to get h5 sum values group by activity categories
    request parameters: cmte_id, report_id
    retrun:

    """
    _sql = """
    SELECT json_agg(t) FROM(
        select sum(total_amount_transferred) as total,
        sum(voter_id_amount) as voter_id,
        sum(voter_registration_amount) as voter_registration,
        sum(gotv_amount) as gotv,
        sum(generic_campaign_amount) as generic_campaign
        from public.sched_h5
        where report_id = %s
        and cmte_id = %s
        and delete_ind is distinct from 'Y'
    ) t
    """
    try:
        cmte_id = request.user.username
        if not('report_id' in request.query_params):
            raise Exception('Missing Input: Report_id is mandatory')
        # handling null,none value of report_id
        if not (check_null_value(request.query_params.get('report_id'))):
            report_id = "0"
        else:
            report_id = check_report_id(request.query_params.get('report_id'))
        with connection.cursor() as cursor:
            cursor.execute(_sql, [report_id, cmte_id])
            result = cursor.fetchone()[0]
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        raise Exception('Error on fetching h3 break down')


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
            if 'report_id' in request.query_params and check_null_value(request.query_params.get('report_id')):
                data['report_id'] = check_report_id(
                    request.query_params.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            if 'transaction_id' in request.query_params and check_null_value(request.query_params.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(
                    request.query_params.get('transaction_id'))
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

"""


**********************************************************CRUD API FOR SCHEDULE_H6*********************************************************************************
"""

def check_mandatory_fields_SH6(data):
    """
    validate mandatory fields for sched_H6 item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H6:
            if not(field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                'The following mandatory fields are required in order to save data to schedH6 table: {}'.format(','.join(errors)))
    except:
        raise


def schedH6_sql_dict(data):
    """
    filter out valid fileds for sched_H6

    """
    valid_fields = [
            'line_number',
            'transaction_type_identifier',
            'transaction_type',
            'back_ref_transaction_id',
            'back_ref_sched_name',
            'entity_id',
            'account_event_identifier',
            'expenditure_date',
            'total_fed_levin_amount',
            'federal_share',
            'levin_share',
            'activity_event_total_ytd',
            'expenditure_purpose',
            'category_code',
            'activity_event_type',
            'memo_code',
            'memo_text',
            # 'create_date',
            # 'last_update_date',
                    # entity_data
            "entity_id",
            "entity_type",
            "entity_name",
            "first_name",
            "last_name",
            "middle_name",
            "preffix",
            "suffix",
            "street_1",
            "street_2",
            "city",
            "state",
            "zip_code",
            "occupation",
            "employer",
            "ref_cand_cmte_id",
            "cand_office",
            "cand_office_state",
            "cand_office_district",
            "cand_election_year",
            "phone_number",
    ]
    try:
        valid_data = {k: v for k, v in data.items() if k in valid_fields}
        line_num, tran_tp = get_line_number_trans_type(
            data["transaction_type_identifier"]
        )
        valid_data["line_number"] = line_num
        valid_data['transaction_type'] = tran_tp

        # TODO; tmp chagne, need to remove those code when db schema corrected
        if 'total_amount' in data:
            valid_data['total_fed_levin_amount'] = data.get('total_amount')
        if 'fed_share_amount' in data:
            valid_data['federal_share'] = data.get('fed_share_amount')
        if 'non_fed_share_amount' in data:
            valid_data['levin_share'] = data.get('non_fed_share_amount')
        if 'activity_event_amount_ytd' in data:
            valid_data['activity_event_total_ytd'] = data.get('activity_event_amount_ytd')
     

        return valid_data
    except:
        raise Exception('invalid request data.')


def get_existing_h6_total(cmte_id, transaction_id):
    """
    fetch existing close balance in the db for current transaction
    """
    _sql = """
    select total_fed_levin_amount
    from public.sched_h6
    where cmte_id = %s
    and transaction_id = %s
    """
    _v = (cmte_id, transaction_id)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, _v)
            return cursor.fetchone()[0]
    except:
        raise

def put_schedH6(data):
    """
    update sched_H6 item
    """
    try:
        check_mandatory_fields_SH6(data)
        if "entity_id" in data:
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"

            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(data)
            roll_back = True
        else:
            entity_data = post_entities(data)
            roll_back = False
        #check_transaction_id(data.get('transaction_id'))
        existing_total = get_existing_h6_total(
            data.get('cmte_id'),
            data.get('transaction_id')
        )
        try:
            put_sql_schedH6(data)
            update_activity_event_amount_ytd_h6(data)

            # if debt payment, update parent sched_d
            if data.get('transaction_type_identifier') == 'ALLOC_FEA_DISB_DEBT':
                if float(existing_total) != float(data.get('total_fed_levin_amount')):
                    update_sched_d_parent(
                        data.get('cmte_id'),
                        data.get('back_ref_transaction_id'),
                        data.get('total_fed_levin_amount'),
                        existing_total
                    )

        except Exception as e:
            if roll_back:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": data.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data) 
            raise Exception(
                'The put_sql_schedH6 function is throwing an error: ' + str(e))
        return data
    except:
        raise


def put_sql_schedH6(data):
    """
    update a schedule_H6 item                    
            
    """
    _sql = """UPDATE public.sched_h6
              SET line_number = %s,
                  transaction_type_identifier= %s,
                  transaction_type = %s,
                  back_ref_transaction_id = %s,
                  back_ref_sched_name = %s,
                  entity_id = %s,
                  account_event_identifier = %s,
                  expenditure_date = %s,
                  total_fed_levin_amount = %s,
                  federal_share  = %s,
                  levin_share  = %s,
                  activity_event_total_ytd = %s,
                  expenditure_purpose = %s,
                  category_code = %s,
                  activity_event_type = %s,
                  memo_code = %s,
                  memo_text = %s,
                  last_update_date= %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (  
            data.get('line_number'),
            data.get('transaction_type_identifier'),
            data.get('transaction_type'),
            data.get('back_ref_transaction_id'),
            data.get('back_ref_sched_name'),
            data.get('entity_id'),
            data.get('account_event_identifier'),
            data.get('expenditure_date'),
            data.get('total_fed_levin_amount'),
            data.get('federal_share'),
            data.get('levin_share'),
            data.get('activity_event_total_ytd'),
            data.get('expenditure_purpose'),
            data.get('category_code'),
            data.get('activity_event_type'),
            data.get('memo_code'),
            data.get('memo_text'),
            datetime.datetime.now(),
            data.get('transaction_id'),
            data.get('report_id'),
            data.get('cmte_id'),
         )
    do_transaction(_sql, _v)


def validate_sh6_data(data):
    """
    validate sH6 json data
    """
    check_mandatory_fields_SH6(data)


def post_sql_schedH6(data):
    try:
        _sql = """
        INSERT INTO public.sched_h6 ( 
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            entity_id,
            account_event_identifier,
            expenditure_date,
            total_fed_levin_amount,
            federal_share,
            levin_share,
            activity_event_total_ytd,
            expenditure_purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            create_date
         )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get('cmte_id'),
            data.get('report_id'),
            data.get('line_number'),
            data.get('transaction_type_identifier'),
            data.get('transaction_type'),
            data.get('transaction_id'),
            data.get('back_ref_transaction_id'),
            data.get('back_ref_sched_name'),
            data.get('entity_id'),
            data.get('account_event_identifier'),
            data.get('expenditure_date'),
            data.get('total_fed_levin_amount'),
            data.get('federal_share'),
            data.get('levin_share'),
            data.get('activity_event_total_ytd'),
            data.get('expenditure_purpose'),
            data.get('category_code'),
            data.get('activity_event_type'),
            data.get('memo_code'),
            data.get('memo_text'),
            datetime.datetime.now()
         )
        with connection.cursor() as cursor:
            # Insert data into schedH6 table
            cursor.execute(_sql, _v)
    except Exception:
        raise

def list_all_transactions_event_type_h6(start_dt, end_dt, activity_event_type, cmte_id):
    """
    load all transactions with the specified activity event type
    need to check
    """
    logger.debug('load transactions with activity_event_type:{}'.format(activity_event_type))
    # logger.debug('load ttransactionsransactions with start:{}, end {}'.format(start_dt, end_dt))
    # logger.debug('load ttransactionsransactions with cmte-id:{}'.format(cmte_id))
    _sql = """
            SELECT t1.total_fed_levin_amount, 
                t1.transaction_id
            FROM public.sched_h6 t1 
            WHERE activity_event_type = %s 
            AND cmte_id = %s
            AND expenditure_date >= %s
            AND expenditure_date <= %s 
            AND back_ref_transaction_id is null
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY expenditure_date ASC, create_date ASC
    """
    # .format(activity_event_type, cmte_id, start_dt, end_dt)
    # logger.debug(_sql)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (activity_event_type, cmte_id, start_dt, end_dt))
            # , [
            #         activity_event_type, 
            #         cmte_id, 
            #         start_dt, 
            #         end_dt,
            #     ])
            transactions_list = cursor.fetchall()
            logger.debug('transaction fetched:{}'.format(transactions_list))
        return transactions_list
    except Exception as e:
        raise Exception(
            'The list_all_transactions_event_type function is throwing an error: ' + str(e))


def update_transaction_ytd_amount_h6(cmte_id, transaction_id, aggregate_amount):

    """
    update h4 ytd amount
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """ UPDATE public.sched_h6
                    SET activity_event_total_ytd = %s 
                    WHERE transaction_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'
                    """,
                    [aggregate_amount, transaction_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception(
                    'Error: The Transaction ID: {} does not exist in sched_h6 table'.format(transaction_id))
    except Exception:
        raise    

def update_activity_event_amount_ytd_h6(data):
    """
    aggregate and update 'activity_event_amount_ytd' for all h6 transactions
    """
    try:

        logger.debug('updating ytd amount h6:')
        # make sure transaction list comes back sorted by contribution_date ASC
        expenditure_dt = date_format(data.get('expenditure_date'))
        aggregate_start_date = datetime.date(expenditure_dt.year, 1, 1)
        aggregate_end_date = datetime.date(expenditure_dt.year, 12, 31)
        transactions_list = list_all_transactions_event_type_h6(
            aggregate_start_date, aggregate_end_date, data.get('activity_event_type'), data.get('cmte_id'))
        aggregate_amount = 0
        for transaction in transactions_list:
            aggregate_amount += transaction[0]
            transaction_id = transaction[1]
            update_transaction_ytd_amount_h6(data.get('cmte_id'), transaction_id, aggregate_amount)
    except Exception as e:
        raise Exception(
            'The update_activity_event_amount_ytd function is throwing an error: ' + str(e))

def post_schedH6(data):
    """
    function for handling POST request for sH6, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SH6(datum, MANDATORY_FIELDS_SCHED_H6o)
        if "entity_id" in data:
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"

            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(data)
            roll_back = True
        else:
            entity_data = post_entities(data)
            roll_back = False

        # continue to save transaction
        entity_id = entity_data.get("entity_id")
        data['entity_id'] = entity_id
        data['transaction_id'] = get_next_transaction_id('SH6')
        
        validate_sh6_data(data)
        try:
            post_sql_schedH6(data)
            update_activity_event_amount_ytd_h6(data)
            if data.get('transaction_type_identifier') == 'ALLOC_FEA_DISB_DEBT':
                update_sched_d_parent(
                    data.get('cmte_id'),
                    data.get('back_ref_transaction_id'),
                    data.get('total_fed_levin_amount')
                )
        except Exception as e:
            if roll_back:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": data.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                'The post_sql_schedH6 function is throwing an error: ' + str(e))
        return data
    except:
        raise

def get_schedH6(data):
    """
    load sched_H6 data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        
        if 'transaction_id' in data:
            transaction_id = check_transaction_id(data.get('transaction_id'))
            # print('get_schedH6')
            forms_obj = get_list_schedH6(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedH6(report_id, cmte_id)
        
        # TODO: need to remove this when db correction done
        for obj in forms_obj:
            obj['fed_share_amount'] = obj.get('federal_share')
            obj['non_fed_share_amount'] = obj.get('levin_share')
            obj['total_amount'] = obj.get('total_fed_levin_amount')
            obj['activity_event_amount_ytd'] = obj.get('activity_event_total_ytd')

        return forms_obj
    except:
        raise


def get_list_all_schedH6(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedH6 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id ,
            back_ref_transaction_id,
            back_ref_sched_name,
            entity_id,
            account_event_identifier,
            expenditure_date,
            total_fed_levin_amount,
            federal_share,
            levin_share,
            activity_event_total_ytd,
            expenditure_purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            create_date,
            last_update_date
            FROM public.sched_h6
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedH6_list = cursor.fetchone()[0]
            if schedH6_list is None:
                raise NoOPError('No sched_H6 transaction found for report_id {} and cmte_id: {}'.format(
                    report_id, cmte_id))
            merged_list = []
            for tran in schedH6_list:
                entity_id = tran.get("entity_id")
                q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
                dictEntity = get_entities(q_data)[0]
                merged_list.append({**tran, **dictEntity})
        return merged_list
    except Exception:
        raise


def get_list_schedH6(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH6 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id ,
            back_ref_transaction_id,
            back_ref_sched_name,
            entity_id,
            account_event_identifier,
            expenditure_date,
            total_fed_levin_amount,
            federal_share,
            levin_share,
            activity_event_total_ytd,
            expenditure_purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            create_date,
            last_update_date
            FROM public.sched_h6
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH6_list = cursor.fetchone()[0]
            if schedH6_list is None:
                raise NoOPError('No sched_H6 transaction found for transaction_id {}'.format(
                    transaction_id))
            merged_list = []
            for tran in schedH6_list:
                entity_id = tran.get("entity_id")
                q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
                dictEntity = get_entities(q_data)[0]
                merged_list.append({**tran, **dictEntity})
        return merged_list
    except Exception:
        raise


def delete_sql_schedH6(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_h6
            SET delete_ind = 'Y' 
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH6(data):
    """
    function for handling delete request for sh6
    """
    try:
        
        delete_sql_schedH6(data.get('cmte_id'), data.get(
            'report_id'), data.get('transaction_id'))
    except Exception as e:
        raise


@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedH6(request):
    
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
            datum = schedH6_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'transaction_id' in request.data and check_null_value(
                    request.data.get('transaction_id')):
                datum['transaction_id'] = check_transaction_id(
                    request.data.get('transaction_id'))
                data = put_schedH6(datum)
            else:
                print(datum)
                data = post_schedH6(datum)
            # Associating child transactions to parent and storing them to DB
            output = get_schedH6(data)
          
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH6 API - POST is throwing an exception: "
                            + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        try:
            data = {
                'cmte_id': request.user.username
            }
            # make sure we get query parameters from both
            # request.data.update(request.query_params)
            if 'report_id' in request.query_params and check_null_value(request.query_params.get('report_id')):
                data['report_id'] = check_report_id(
                    request.query_params.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            if 'transaction_id' in request.query_params and check_null_value(request.query_params.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(
                    request.query_params.get('transaction_id'))
            datum = get_schedH6(data)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH6 API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
            delete_schedH6(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedH6 API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            datum = schedH6_sql_dict(request.data)
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
            data = put_schedH6(datum)
            output = get_schedH6(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response("The schedH6 API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    else:
        raise NotImplementedError










