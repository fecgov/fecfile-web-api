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
from fecfiler.sched_B.views import (delete_parent_child_link_sql_schedB,
                                    delete_schedB, get_list_child_schedB,
                                    get_schedB, post_schedB, put_schedB,
                                    schedB_sql_dict, put_sql_schedB, post_sql_schedB)

# TODO: adding earmarked transactions: one sched_a and one generated sched_b transactions

# Create your views here.
logger = logging.getLogger(__name__)


"""
some questions to discuss:
1. remove line_number, trsaction_type from mandatory fields.
2. expenditure purpose = ? 
3. one sched_a each request ?
4. one sched_a one entity each request ?
"""

"""
********************************************************************************************************************************
SCHEDULE A TRANSACTION API - SCHED_A APP - SPRINT 7 - FNE 552 - BY PRAVEEN JINKA
********************************************************************************************************************************
"""

"""
**************************************************** FUNCTIONS - TRANSACTION IDS **********************************************************
"""
# mandatory fields for shcedule_a records
MANDATORY_FIELDS_SCHED_A = ['report_id', 'cmte_id', 'line_number',
                            'transaction_type', 'contribution_date', 
                            'contribution_amount']

# madatory fields for aggregate amount api call
MANDATORY_FIELDS_AGGREGATE = ['transaction_type_identifier']

# list of transaction_type for child sched_b items
CHILD_SCHED_B_TYPES = []

# list of valid line numbers - this list will grow as we add more types
VALID_TRANSACTION_TYPES = ['15', '18G', '17Z']

# map if transaction_type to line_numbers -
# this list will grow as we add more types
TRANSACTION_TYPES_LINE_NUM_MAP = {
    '15': ['11AI', '11AII'],
    '18G': ['12'],
    '17Z': ['16'],
}

TRANSACTION_TYPE_IDENTIFIER_LINE_NUM_TRANS_CODE_MAP = {
    'INDV_REC': ['11A', '15'],
    'OTH_REC': ['17', '15O'],
    'IND_RECNT': ['17', '15R'],
    'PTY_RCNT': ['17', '18R'],
    'PAC_RCNT': ['17', '18R'],
    'TRI_RCNT': ['17', '11R'],
    'IND_NP_RECNT': ['17', '32'],
    'TRI_NP_RCNT': ['17', '32T'],
    'PTY_NP_RCNT': ['17', '32K'],
    'PAC_NP_RCNT': ['17', '32K'],
    'IND_HQ_ACCNT': ['17', '31'],
    'TRI_HQ_ACCNT': ['17', None],
    'PTY_HQ_ACCNT': ['17', '31K'],
    'PAC_HQ_ACCNT': ['17', '31K'],
    'IND_CO_ACCNT': ['17', '30'],
    'TRI_CO_ACCNT': ['17', None],
    'PTY_CO_ACCNT': ['17', '30K'],
    'PAC_CO_ACCNT': ['17', '30K'],
    'IND_CAREY': ['17', '10'],
    'OT_COM_CAREY': ['17', '10K'],
    'BU_LAB_CAREY': ['17', '10B'],
    'PAR_CON': ['11A', '15P'],
    'PAR_MEMO': ['11A', '15PM'],
    'REATT_FROM': ['11A', None],
    'REATT_TO': ['11A', '15M'],
    'JF_TRAN': ['12', '14G'],
    'IND_JF_MEM': ['12', '14JM'],
    'PTY_JF_MEM': ['12', '14KM'],
    'PAC_JF_MEM': ['12', '14KM'],
    'TRI_JF_MEM': ['12', '14TM'],
    'JF_TRAN_R': ['17', '32G'],
    'IND_JF_R_MEM': ['17', '32JM'],
    'PAC_JF_R_MEM': ['17', '32KM'],
    'TRI_JF_R_MEM': ['17', '32TM'],
    'JF_TRAN_C': ['17', '30G'],
    'IND_JF_C_MEM': ['17', '30JM'],
    'PAC_JF_C_MEM': ['17', '30KM'],
    'TRI_JF_C_MEM': ['17', '30TM'],
    'JF_TRAN_H': ['17', '31G'],
    'IND_JF_H_MEM': ['17', '31JM'],
    'PAC_JF_H_MEM': ['17', '31KM'],
    'TRI_JF_H_MEM': ['17', '31TM'],
    'IK_TRAN': ['12', '18Z'],
    'IK_TF_OUT': ['21B', '20K'],
    'IK_TRAN_FEA': ['12', '18F'],
    'IK_OUT_FEA': ['30B', '20K'],
    'IK_REC_PTY': ['11B', '15Z'],
    'IK_OUT_PTY': ['21B', '20K'],
    'IK_REC_PAC': ['11C', '15Z'],
    'IK_OUT_PAC': ['21B', '20K'],
    'IK_REC': ['11A', '15K'],
    'IK_OUT': ['21B', '20K'],
    'CON_EM': ['11A', '15I'],
    'EM_OUT': ['23', '24T'],
    'CON_EM_MEMO': ['11A', '15IM'],
    'EM_OUT_MEMO': ['23', '24IM'],
    'PAC_EM': ['11C', '18I'],
    'PAC_EM_MEMO': ['11C', '18IM'],
    'CON_EM_RT': ['11A', '15E'],
    'CON_EM_RT_M': ['11A', '15EM'],
    'PAC_EM_RT': ['11C', '18E'],
    'PAC_EM_RT_M': ['11C', '18EM']
}

# list of all transaction type identifiers that should
# have single column storage in DB
SINGLE_TRANSACTION_SCHEDA_LIST = ['INDV_REC',
                                  'OTH_REC',
                                  'IND_RECNT',
                                  'PTY_RCNT',
                                  'PAC_RCNT',
                                  'TRI_RCNT',
                                  'IND_NP_RECNT',
                                  'TRI_NP_RCNT',
                                  'PTY_NP_RCNT',
                                  'PAC_NP_RCNT',
                                  'IND_HQ_ACCNT',
                                  'TRI_HQ_ACCNT',
                                  'PTY_HQ_ACCNT',
                                  'PAC_HQ_ACCNT',
                                  'IND_CO_ACCNT',
                                  'TRI_CO_ACCNT',
                                  'PTY_CO_ACCNT',
                                  'PAC_CO_ACCNT',
                                  'IND_CAREY',
                                  'OT_COM_CAREY',
                                  'BU_LAB_CAREY',
                                  'PAR_CON',
                                  'PAR_MEMO',
                                  'REATT_FROM',
                                  'REATT_TO',
                                  'JF_TRAN',
                                  'IND_JF_MEM',
                                  'PTY_JF_MEM',
                                  'PAC_JF_MEM',
                                  'TRI_JF_MEM',
                                  'JF_TRAN_R',
                                  'IND_JF_R_MEM',
                                  'PAC_JF_R_MEM',
                                  'TRI_JF_R_MEM',
                                  'JF_TRAN_C',
                                  'IND_JF_C_MEM',
                                  'PAC_JF_C_MEM',
                                  'TRI_JF_C_MEM',
                                  'JF_TRAN_H',
                                  'IND_JF_H_MEM',
                                  'PAC_JF_H_MEM',
                                  'TRI_JF_H_MEM']

#list of all transaction type identifiers that should auto generate sched_b item in DB
AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT = {"IK_TRAN": "IK_TF_OUT", 
                                                    "IK_TRAN_FEA": "IK_OUT_FEA",
                                                    "IK_REC_PTY": "IK_OUT_PTY",
                                                    "IK_REC_PAC": "IK_OUT_PAC", 
                                                    "IK_REC": "IK_OUT",
                                                    "CON_EM": "EM_OUT",
                                                    "CON_EM_MEMO": "EM_OUT_MEMO",
                                                    "PAC_EM": "EM_OUT",
                                                    "PAC_EM_MEMO": "EM_OUT_MEMO"
                                                    }

#list of all transaction type identifiers that have itemization rule applied to it
itemization_transaction_type_identifier_list = ['INDV_REC', 'PAR_CON', 'PAR_MEMO', 'IK_REC', 'REATT_FROM', 'REATT_TO']

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


def check_transaction_id(transaction_id):
    """validate transaction id against trsaction types, e.g. SA20190627000000094"""
    try:
        transaction_type_list = ["SA", ]
        transaction_type = transaction_id[0:2]
        if not (transaction_type in transaction_type_list):
            raise Exception(
                'The Transaction ID: {} is not in the specified format. Transaction IDs start with SA characters'.format(transaction_id))
        return transaction_id
    except Exception:
        raise


def validate_sa_data(data):
    """
    validate: 1. mandatory sa fields; 2. valid line number and transaction types
    """
    check_mandatory_fields_SA(data, MANDATORY_FIELDS_SCHED_A)
    # validate_transaction_type(data)


def validate_transaction_type(data):
    """
    check line number and transaction types are both valid and compatible
    """
    if not data.get('transaction_type') in VALID_TRANSACTION_TYPES:
        raise Exception('Invalid transaction type detected.')
    elif not data.get('line_number') in TRANSACTION_TYPES_LINE_NUM_MAP.get(
            data.get('transaction_type')):
        raise Exception('Line number does not match transaction type.')
    else:
        pass


def check_mandatory_fields_SA(data, list_mandatory_fields):
    """
    validate mandatory fields for sched_a item
    """
    try:
        errors = []
        for field in list_mandatory_fields:
            if not(field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                'The following mandatory fields are required in order to save data to schedA table: {}'.format(','.join(errors)))
    except:
        raise


def check_decimal(value):
    """
    validate a value is decimal
    """
    try:
        Decimal(value)
        return value
    except:
        raise Exception(
            'Invalid Input: Expecting a decimal value like 18.11, 24.07. Input received: {}'.format(value))


"""
**************************************************** FUNCTIONS - SCHED A TRANSACTION *************************************************************
"""

# TODO: update this function to take one argument of data_dic


def post_sql_schedA(cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, donor_cmte_id, donor_cmte_name, transaction_type_identifier):
    """persist one sched_a item."""
    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute("""INSERT INTO public.sched_a (cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", [cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, datetime.datetime.now(), donor_cmte_id, donor_cmte_name, transaction_type_identifier])
    except Exception:
        raise


def get_list_all_schedA(report_id, cmte_id):
    """
    load sched_a items from DB
    """
    return get_list_schedA(report_id, cmte_id)
    # try:
    #     with connection.cursor() as cursor:
    #         # GET all rows from schedA table
    #         query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
    #                         FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""

    #         cursor.execute("""SELECT json_agg(t) FROM (""" +
    #                        query_string + """) t""", [report_id, cmte_id])
    #         # charlieSun: josn_agg function is returning one record with a list of row_dics
    #         # something like ([{c1:v1},{c1:v2},{c1:v3}])
    #         schedA_list = cursor.fetchone()[0]
    #         # for row in cursor.fetchall():
    #         # forms_obj.append(data_row)
    #         # data_row = list(row)
    #         # schedA_list = data_row[0]

    #         if schedA_list is None:
    #             raise NoOPError(
    #                 'The Report id:{} does not have any schedA transactions'.format(report_id))
    #         merged_list = []
    #         for dictA in schedA_list:
    #             entity_id = dictA.get('entity_id')
    #             data = {
    #                 'entity_id': entity_id,
    #                 'cmte_id': cmte_id
    #             }
    #             entity_list = get_entities(data)
    #             dictEntity = entity_list[0]
    #             merged_dict = {**dictA, **dictEntity}
    #             merged_list.append(merged_dict)
    #     return merged_list
    # except Exception:
    #     raise

def get_list_schedA(report_id, cmte_id, transaction_id = None):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            if transaction_id:
                query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                                FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s AND delete_ind is distinct from 'Y'"""

                cursor.execute("""SELECT json_agg(t) FROM (""" + query_string +
                            """) t""", [report_id, cmte_id, transaction_id])
            else:
                query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                            FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""

                cursor.execute("""SELECT json_agg(t) FROM (""" +
                           query_string + """) t""", [report_id, cmte_id])           
 
            schedA_list = cursor.fetchone()[0]
            if not schedA_list:
                raise NoOPError(
                    'No transaction found for cmte_id {} and report_id {}'.format(cmte_id, report_id))
            merged_list = []
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
    """
    load all child scjed_a items for this transaction
    """
    try:
        with connection.cursor() as cursor:

            # GET child rows from schedA table

            query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                            FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s AND delete_ind is distinct from 'Y'"""

            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string +
                           """) t""", [report_id, cmte_id, transaction_id])

            for row in cursor.fetchall():
                # forms_obj.append(data_row)
                data_row = list(row)
                schedA_list = data_row[0]
            merged_list = []
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


def put_sql_schedA(cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, donor_cmte_id, donor_cmte_name, transaction_type_identifier):
    """
    uopdate a schedule_a item
    """
    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute("""UPDATE public.sched_a SET line_number = %s, transaction_type = %s, back_ref_transaction_id = %s, back_ref_sched_name = %s, entity_id = %s, contribution_date = %s, contribution_amount = %s, purpose_description = %s, memo_code = %s, memo_text = %s, election_code = %s, election_other_description = %s, donor_cmte_id = %s, donor_cmte_name = %s, transaction_type_identifier = %s WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
                           [line_number, transaction_type, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, donor_cmte_id, donor_cmte_name, transaction_type_identifier, transaction_id, report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception(
                    'The Transaction ID: {} does not exist in schedA table'.format(transaction_id))
    except Exception:
        raise


def delete_sql_schedA(transaction_id, report_id, cmte_id):
    """delete a sched_a item
    """
    try:
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from Sched_A table
            cursor.execute("""UPDATE public.sched_a SET delete_ind = 'Y' WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [
                           transaction_id, report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception(
                    'The Transaction ID: {} is either already deleted or does not exist in schedA table'.format(transaction_id))
    except Exception:
        raise


def delete_parent_child_link_sql_schedA(transaction_id, report_id, cmte_id):
    """delete parent child link in sched_a
    """
    try:
        with connection.cursor() as cursor:

            # UPDATE back_ref_transaction_id value to null in sched_a table
            value = None
            cursor.execute("""UPDATE public.sched_a SET back_ref_transaction_id = %s WHERE back_ref_transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [
                           value, transaction_id, report_id, cmte_id])

    except Exception:
        raise


def find_form_type(report_id, cmte_id):
    """
    load form type based on report_id and cmte_id
    """
    try:
        # handling cases where report_id is reported as 0
        if report_id in ["0", '0', 0]:
            return "F3X"
        # end of error handling
        with connection.cursor() as cursor:
            cursor.execute("""SELECT form_type FROM public.reports WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [
                           report_id, cmte_id])
            form_types = cursor.fetchone()
        if (cursor.rowcount == 0):
            raise Exception(
                'The Report ID: {} is either already deleted or does not exist in reports table'.format(report_id))
        else:
            return form_types[0]
    except Exception as e:
        raise Exception(
            'The form_type function is throwing an error:' + str(e))


def find_aggregate_date(form_type, contribution_date):
    """
    calculate aggregate start, end dates
    # TODO: do we need checking form_type here.
    """
    try:
        aggregate_start_date = None
        if form_type == "F3X":
            year = contribution_date.year
            aggregate_start_date = datetime.date(year, 1, 1)
            aggregate_end_date = datetime.date(year, 12, 31)
        return aggregate_start_date, aggregate_end_date
    except Exception as e:
        raise Exception(
            'The aggregate_start_date function is throwing an error: ' + str(e))


def func_aggregate_amount(aggregate_start_date, aggregate_end_date, transaction_type_identifier, entity_id, cmte_id):
    """
    query aggregate amount based on start/end date, transaction_type, entity_id and cmte_id
    """
    try:
        with connection.cursor() as cursor:

            cursor.execute("""SELECT COALESCE(SUM(contribution_amount),0) FROM public.sched_a WHERE entity_id = %s AND transaction_type_identifier = %s AND cmte_id = %s AND contribution_date >= %s AND contribution_date <= %s AND delete_ind is distinct FROM 'Y'""", [
                           entity_id, transaction_type_identifier, cmte_id, aggregate_start_date, aggregate_end_date])

            aggregate_amt = cursor.fetchone()[0]
        return aggregate_amt
    except Exception as e:
        raise Exception(
            'The aggregate_amount function is throwing an error: ' + str(e))


def list_all_transactions_entity(aggregate_start_date, aggregate_end_date, transaction_type_identifier, entity_id, cmte_id):
    """
    load all transactions for an entity within a time window
    return value: a list of transction_records [
       (contribution_amount, transaction_id, report_id, line_number, contribution_date),
       ....
    ]
    return items are sorted by contribution_date in ASC order
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT contribution_amount, transaction_id, report_id, line_number, contribution_date FROM public.sched_a WHERE entity_id = %s AND transaction_type_identifier = %s AND cmte_id = %s AND contribution_date >= %s AND contribution_date <= %s AND delete_ind is distinct FROM 'Y' ORDER BY contribution_date ASC, create_date ASC""", [
                           entity_id, transaction_type_identifier, cmte_id, aggregate_start_date, aggregate_end_date])
            transactions_list = cursor.fetchall()
        return transactions_list
    except Exception as e:
        raise Exception(
            'The list_all_transactions_entity function is throwing an error: ' + str(e))


def update_linenumber_aggamt_transactions_SA(contribution_date, transaction_type_identifier, entity_id, cmte_id, report_id):
    """
    helper function for updating private contribution line number based on aggrgate amount
    the aggregate amount is a contribution_date-based on incremental update, the line number
    is updated accordingly:

    e.g.
    date, contribution_amount, aggregate_amount, line_number
    1/1/2018, 50, 50, 11AII
    2/1/2018, 60, 110, 11AII
    3/1/2018, 100, 210, 11AI (aggregate_amount > 200, update line number)
    """
    try:
        
        itemization_value = 200
        itemized_transaction_list = []
        unitemized_transaction_list = []
        form_type = find_form_type(report_id, cmte_id)
        aggregate_start_date, aggregate_end_date = find_aggregate_date(
            form_type, contribution_date)
        # make sure transaction list comes back sorted by contribution_date ASC
        transactions_list = list_all_transactions_entity(
            aggregate_start_date, aggregate_end_date, transaction_type_identifier, entity_id, cmte_id)
        aggregate_amount = 0
        for transaction in transactions_list:
            aggregate_amount += transaction[0]
            if str(report_id) == str(transaction[2]):
                if contribution_date <= transaction[4]:
                    if transaction_type_identifier in itemization_transaction_type_identifier_list:
                        if aggregate_amount <= itemization_value:
                            put_sql_linenumber_schedA(
                                cmte_id, report_id, "11AII", transaction[1], entity_id, aggregate_amount)
                        else:
                            put_sql_linenumber_schedA(
                                cmte_id, report_id, "11AI", transaction[1], entity_id, aggregate_amount)
                    else:
                        put_sql_linenumber_schedA(
                                cmte_id, report_id, transaction[3], transaction[1], entity_id, aggregate_amount)
    except Exception as e:
        raise Exception(
            'The update_linenumber_aggamt_transactions_SA function is throwing an error: ' + str(e))


def put_sql_linenumber_schedA(cmte_id, report_id, line_number, transaction_id, entity_id, aggregate_amount):
    """
    update line number
    """
    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute("""UPDATE public.sched_a SET line_number = %s, aggregate_amt = %s WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s AND entity_id = %s AND delete_ind is distinct from 'Y'""",
                           [line_number, aggregate_amount, transaction_id, report_id, cmte_id, entity_id])
            if (cursor.rowcount == 0):
                raise Exception(
                    'put_sql_linenumber_schedA function: The Transaction ID: {} does not exist in schedA table'.format(transaction_id))
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
    """save sched_a item and the associated entities."""
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        validate_sa_data(datum)

        # save entities first
        if 'entity_id' in datum:
            get_data = {
                'cmte_id': datum.get('cmte_id'),
                'entity_id': datum.get('entity_id')
            }
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
        else:
            entity_data = post_entities(datum)

        # continue to save transaction
        entity_id = entity_data.get('entity_id')
        datum['entity_id'] = entity_id
        # datum['line_number'] = disclosure_rules(datum.get('line_number'), datum.get('report_id'), datum.get('transaction_type'), datum.get('contribution_amount'), datum.get('contribution_date'), entity_id, datum.get('cmte_id'))
        trans_char = "SA"
        transaction_id = get_next_transaction_id(trans_char)
        datum['transaction_id'] = transaction_id
        try:
            post_sql_schedA(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get(
                'contribution_amount'), datum.get('purpose_description'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), datum.get('donor_cmte_name'), datum.get('transaction_type_identifier'))
            if datum.get('transaction_type_identifier') in AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.keys():
                child_transaction_id = get_next_transaction_id("SB")
                expenditure_purpose = "In-Kind #" + transaction_id
                child_transaction_type_identifier = AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.get(datum.get('transaction_type_identifier'))
                child_line_number, child_transaction_type = get_line_number_trans_type(child_transaction_type_identifier)
                if datum.get('transaction_type_identifier') in ['IK_TRAN', 'IK_TRAN_FEA']:
                    datum['donor_cmte_id'] = None
                    datum['donor_cmte_name'] = None
                post_sql_schedB(datum.get('cmte_id'), datum.get('report_id'), child_line_number, child_transaction_type, child_transaction_id, transaction_id, datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), '0.00', expenditure_purpose, None, None, None, datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), None, datum.get('donor_cmte_name'), None, None, None, None, None, None, child_transaction_type_identifier)
        except Exception as e:
            if 'entity_id' in datum:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {
                    'cmte_id': datum.get(cmte_id),
                    'entity_id': entity_id
                }
                remove_entities(get_data)
            raise Exception(
                'The post_sql_schedA function is throwing an error: ' + str(e))
            
        # update line number based on aggregate amount info
        update_linenumber_aggamt_transactions_SA(datum.get('contribution_date'), datum.get(
            'transaction_type_identifier'), entity_id, datum.get('cmte_id'), datum.get('report_id'))
        return datum
    except:
        raise


def get_schedA(data):
    """load sched_a and the child sched_a and sched_b transactions."""
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        if 'transaction_id' in data:
            transaction_id = check_transaction_id(data.get('transaction_id'))

        # CharlieSun: I think check_transaction_id should validate transaction_id
        # flag = False
        # if 'transaction_id' in data:
        #     try:
        #         transaction_id = check_transaction_id(data.get('transaction_id'))
        #         flag = True
        #     except Exception:
        #         flag = False

        # if flag:
            forms_obj = get_list_schedA(report_id, cmte_id, transaction_id)
            childA_forms_obj = get_list_child_schedA(
                report_id, cmte_id, transaction_id)
            childB_forms_obj = get_list_child_schedB(
                report_id, cmte_id, transaction_id)
            child_forms_obj = childA_forms_obj + childB_forms_obj
            if len(child_forms_obj) > 0:
                forms_obj[0]['child'] = child_forms_obj
        else:
            forms_obj = get_list_all_schedA(report_id, cmte_id)
        return forms_obj

    except:
        raise


def put_schedA(datum):
    """update sched_a item
    """
    try:
        check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
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
            put_sql_schedA(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get(
                'contribution_amount'), datum.get('purpose_description'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), datum.get('donor_cmte_name'), datum.get('transaction_type_identifier'))
            if datum.get('transaction_type_identifier') in AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.keys():
                child_transaction_id = get_child_transaction_schedB(datum.get('cmte_id'), datum.get('report_id'), transaction_id)
                expenditure_purpose = "In-Kind #" + transaction_id
                child_transaction_type_identifier = AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.get(datum.get('transaction_type_identifier'))
                child_line_number, child_transaction_type = get_line_number_trans_type(child_transaction_type_identifier)
                if datum.get('transaction_type_identifier') in ['IK_TRAN', 'IK_TRAN_FEA']:
                    datum['donor_cmte_id'] = None
                    datum['donor_cmte_name'] = None
                if child_transaction_id is None:
                    child_transaction_id = get_next_transaction_id("SB")
                    post_sql_schedB(datum.get('cmte_id'), datum.get('report_id'), child_line_number, child_transaction_type, child_transaction_id, transaction_id, datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), '0.00', expenditure_purpose, None, None, None, datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), None, datum.get('donor_cmte_name'), None, None, None, None, None, None, child_transaction_type_identifier)
                else:
                    put_sql_schedB(datum.get('cmte_id'), datum.get('report_id'), child_line_number, child_transaction_type, child_transaction_id, transaction_id, datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), '0.00', expenditure_purpose, None, None, None, datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), None, datum.get('donor_cmte_name'), None, None, None, None, None, None, child_transaction_type_identifier)
        except Exception as e:
            if flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {
                    'cmte_id': datum.get('cmte_id'),
                    'entity_id': entity_id
                }
                remove_entities(get_data)
            raise Exception(
                'The put_sql_schedA function is throwing an error: ' + str(e))
            
        # update line number based on aggregate amount info
        update_linenumber_aggamt_transactions_SA(datum.get('contribution_date'), datum.get(
            'transaction_type_identifier'), entity_id, datum.get('cmte_id'), datum.get('report_id'))
        return datum
    except:
        raise


def delete_schedA(data):
    """delete sched_a item and update all associcated items
    """
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        transaction_id = check_transaction_id(data.get('transaction_id'))
        datum = get_list_schedA(report_id, cmte_id, transaction_id)[0]
        delete_sql_schedA(transaction_id, report_id, cmte_id)
        # delete_parent_child_link_sql_schedA(transaction_id, report_id, cmte_id)
        # delete_parent_child_link_sql_schedB(transaction_id, report_id, cmte_id)
        update_linenumber_aggamt_transactions_SA(datetime.datetime.strptime(datum.get('contribution_date'), '%Y-%m-%d').date(
        ), datum.get('transaction_type_identifier'), datum.get('entity_id'), datum.get('cmte_id'), datum.get('report_id'))
    except:
        raise

# TODO: refactor this function
# something like: if isinstance(data, collections.Iterable):

def check_type_list(data):
    try:
        if not type(data) is list:
            raise Exception(
                'The child transactions have to be sent in as an array or list. Input received: {}'.format(data))
        else:
            return data
    except:
        raise

# TODO: refactor this functon using dictioanry comprehension


def schedA_sql_dict(data):
    """
    filter data, validate fields and build sched_a item dic
    """
    try:
        datum = {
            # 'line_number': data.get('line_number'),
            # 'transaction_type': data.get('transaction_type'),
            'transaction_type_identifier': data.get('transaction_type_identifier'),
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
            'donor_cmte_id': data.get('donor_cmte_id'),
            'donor_cmte_name': data.get('donor_cmte_name')
        }
        return datum
    except:
        raise

def get_line_number_trans_type(transaction_type_identifier):
    try:
        if transaction_type_identifier in TRANSACTION_TYPE_IDENTIFIER_LINE_NUM_TRANS_CODE_MAP.keys():
            list_value = TRANSACTION_TYPE_IDENTIFIER_LINE_NUM_TRANS_CODE_MAP.get(transaction_type_identifier)
            line_number = list_value[0]
            transaction_type = list_value[1]
            return line_number, transaction_type
        else:
            raise Exception('The transaction type identifier is not in the specified list. Input received: {}. Valid Inputs: {}'.format(transaction_type_identifier, ','.join(TRANSACTION_TYPE_IDENTIFIER_LINE_NUM_TRANS_CODE_MAP.keys())))
    except:
        raise

def get_child_transaction_schedB(cmte_id, report_id, back_ref_transaction_id):
    try:
        with connection.cursor() as cursor:
            query_string = """SELECT transaction_id FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s AND delete_ind is distinct from 'Y'"""
            cursor.execute(query_string, [report_id, cmte_id, back_ref_transaction_id])
            if cursor.rowcount == 0:
                return None
            else:
                return cursor.fetchone()[0]
    except:
        raise
"""
***************************************************** SCHED A - POST API CALL STARTS HERE **********************************************************
"""
@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def schedA(request):
    """
    sched_a api supporting POST, GET, DELETE, PUT
    """

    # create new transactions and children transactions if any
    if request.method == 'POST':
        try:
            if not('transaction_type_identifier' in request.data and check_null_value(request.data.get('transaction_type_identifier'))):
                raise Exception('Missing Input: transaction_type_identifier is mandatory')
            cmte_id = request.user.username
            if not('report_id' in request.data):
                raise Exception('Missing Input: Report_id is mandatory')
            # handling null,none value of report_id
            if not (check_null_value(request.data.get('report_id'))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get('report_id'))
            # end of handling
            # To check if the report id exists in reports table
            form_type = find_form_type(report_id, cmte_id)
            datum = schedA_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                datum['entity_id'] = request.data.get('entity_id')
            datum['line_number'], datum['transaction_type'] = get_line_number_trans_type(request.data.get('transaction_type_identifier'))
            # if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
            #     datum['transaction_id'] = check_transaction_id(
            #         request.data.get('transaction_id'))
            #     data = put_schedA(datum)
            # else:
            data = post_schedA(datum)
            # Associating child transactions to parent and storing them to DB
            # if 'child' in request.data:
            #     children = check_type_list(request.data.get('child'))
            #     if len(children) > 0:
            #         child_output = []
            #         for child in children:
            #             transaction_type = child.get('transaction_type')
            #             if transaction_type in CHILD_SCHED_B_TYPES:
            #                 child_datum = schedB_sql_dict(child)
            #             else:
            #                 child_datum = schedA_sql_dict(child)

            #             child_datum['back_ref_transaction_id'] = data.get(
            #                 'transaction_id')
            #             child_datum['report_id'] = report_id
            #             child_datum['cmte_id'] = cmte_id
            #             if 'entity_id' in child and check_null_value(child.get('entity_id')):
            #                 child_datum['entity_id'] = child.get('entity_id')
            #             if 'transaction_id' in child and check_null_value(child.get('transaction_id')):
            #                 child_datum['transaction_id'] = check_transaction_id(
            #                     child.get('transaction_id'))
            #                 if transaction_type in CHILD_SCHED_B_TYPES:
            #                     child_data = put_schedB(child_datum)
            #                 else:
            #                     child_data = put_schedA(child_datum)
            #             else:
            #                 if transaction_type in CHILD_SCHED_B_TYPES:
            #                     child_data = post_schedB(child_datum)
            #                 else:
            #                     child_data = post_schedA(child_datum)
            output = get_schedA(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedA API - POST is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    """
    *********************************************** SCHED A - GET API CALL STARTS HERE **********************************************************
    """
    # Get records from schedA table
    if request.method == 'GET':

        try:
            data = {
                'cmte_id': request.user.username
            }
            if 'report_id' in request.query_params and check_null_value(request.query_params.get('report_id')):
                data['report_id'] = check_report_id(
                    request.query_params.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            # To check if the report id exists in reports table
            form_type = find_form_type(data.get('report_id'), data.get('cmte_id'))
            if 'transaction_id' in request.query_params and check_null_value(request.query_params.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(
                    request.query_params.get('transaction_id'))
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
            if not('transaction_type_identifier' in request.data and check_null_value(request.data.get('transaction_type_identifier'))):
                raise Exception('Missing Input: transaction_type_identifier is mandatory')

            # if request.data.get('transaction_type') in CHILD_SCHED_B_TYPES:
            #     datum = schedB_sql_dict(request.data)
            # else:
            datum = schedA_sql_dict(request.data)

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
            # To check if the report id exists in reports table
            form_type = find_form_type(report_id, datum.get('cmte_id'))
            datum['line_number'], datum['transaction_type'] = get_line_number_trans_type(request.data.get('transaction_type_identifier'))
            if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                datum['entity_id'] = request.data.get('entity_id')
            # if request.data.get('transaction_type') in CHILD_SCHED_B_TYPES:
            #     data = put_schedB(datum)
            #     output = get_schedB(data)
            # else:
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
                data['report_id'] = check_report_id(
                    request.query_params.get('report_id'))
            else:
                raise Exception('Missing Input: report_id is mandatory')
            # To check if the report id exists in reports table
            form_type = find_form_type(data.get('report_id'), data.get('cmte_id'))
            if 'transaction_id' in request.query_params and check_null_value(request.query_params.get('transaction_id')):
                data['transaction_id'] = check_transaction_id(
                    request.query_params.get('transaction_id'))
            else:
                raise Exception('Missing Input: transaction_id is mandatory')
            delete_schedA(data)
            return Response("The Transaction ID: {} has been successfully deleted".format(data.get('transaction_id')), status=status.HTTP_201_CREATED)
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
@api_view(['GET'])
def contribution_aggregate(request):
    """
    contribution_aggregate api with GET request
    """
    if request.method == 'GET':
        try:
            check_mandatory_fields_SA(
                request.query_params, MANDATORY_FIELDS_AGGREGATE)
            cmte_id = request.user.username
            if not('report_id' in request.query_params):
                raise Exception('Missing Input: Report_id is mandatory')
            # handling null,none value of report_id
            if check_null_value(request.query_params.get('report_id')):
                report_id = check_report_id(request.query_params.get('report_id'))
            else:
                report_id = "0"
            # end of handling
            if report_id == "0":
                aggregate_date = datetime.datetime.today()
            else:
                aggregate_date = report_end_date(report_id, cmte_id)
            transaction_type_identifier = request.query_params.get('transaction_type_identifier')
            if 'entity_id' in request.query_params and check_null_value(request.query_params.get('entity_id')):
                entity_id = request.query_params.get('entity_id')
            else:
                entity_id = "0"
            if 'contribution_amount' in request.query_params and check_null_value(request.query_params.get('contribution_amount')):
                contribution_amount = check_decimal(
                    request.query_params.get('contribution_amount'))
            else:
                contribution_amount = "0"
            form_type = find_form_type(report_id, cmte_id)
            aggregate_start_date, aggregate_end_date = find_aggregate_date(
                form_type, aggregate_date)
            aggregate_amt = func_aggregate_amount(
                aggregate_start_date, aggregate_end_date, transaction_type_identifier, entity_id, cmte_id)
            total_amt = aggregate_amt + Decimal(contribution_amount)
            return JsonResponse({"contribution_aggregate": total_amt}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response('The contribution_aggregate API is throwing an error: ' + str(e), status=status.HTTP_400_BAD_REQUEST)


def report_end_date(report_id, cmte_id):
    """
    query report end date
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT cvg_end_date FROM public.reports WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct FROM 'Y'""", [
                           report_id, cmte_id])
            if (cursor.rowcount == 0):
                raise Exception(
                    'The Report ID: {} does not exist in reports table'.format(report_id))
            cvg_end_date = cursor.fetchone()[0]
        return cvg_end_date
    except Exception as e:
        raise Exception(
            'The report_end_date function is throwing an error: ' + str(e))


"""
******************************************************************************************************************************
END - AGGREGATE AMOUNT API - SCHED_A APP
******************************************************************************************************************************
"""
