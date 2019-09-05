import datetime
import json
import logging
import os
from decimal import Decimal

import requests
from functools import lru_cache
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

from fecfiler.core.transaction_util import get_line_number_trans_type

from fecfiler.sched_B.views import (delete_parent_child_link_sql_schedB,
                                    delete_schedB, get_list_child_schedB,
                                    get_schedB, post_schedB, put_schedB,
                                    schedB_sql_dict, put_sql_schedB, post_sql_schedB,
                                    put_sql_agg_amount_schedB, get_list_child_transactionId_schedB)


# Create your views here.
logger = logging.getLogger(__name__)

# mandatory fields for shcedule_a records
MANDATORY_FIELDS_SCHED_A = ['report_id', 'transaction_type_identifier', 'contribution_date', 
                            'contribution_amount', 'entity_type']

MANDATORY_CHILD_FIELDS_SCHED_A = ['report_id', 'child_transaction_type_identifier', 'child_contribution_date', 
                            'child_contribution_amount', 'child_entity_type']

# madatory fields for aggregate amount api call
MANDATORY_FIELDS_AGGREGATE = ['transaction_type_identifier', 'contribution_date']

# list of transaction_type for child sched_b items
CHILD_SCHED_B_TYPES = []


# list of all transaction type identifiers that should
# have single column storage in DB
# TODO: no sure this list is used in this module
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
AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT = {
                                    "IK_REC" : "IK_OUT",
                                    "IK_BC_REC" : "IK_BC_OUT",
                                    "REATT_FROM" : "REATT_MEMO",
                                    #"CON_EAR_DEP" : "CON_EAR_DEP_MEMO",
                                    # "CON_EAR_UNDEP" : "CON_EAR_UNDEP_MEMO",
                                    "PARTY_IK_REC" : "PARTY_IK_OUT",
                                    "PARTY_IK_BC_REC" : "PARTY_IK_BC_OUT",
                                    "PAC_IK_REC" : "PAC_IK_OUT",
                                    "PAC_IK_BC_REC" : "PAC_IK_BC_OUT",
                                    # "PAC_CON_EAR_DEP" : "PAC_CON_EAR_DEP_OUT",
                                    # "PAC_CON_EAR_UNDEP" : "PAC_CON_EAR_UNDEP_MEMO",
                                    "IK_TRAN" : "IK_TRAN_OUT",
                                    "IK_TRAN_FEA" : "IK_TRAN_FEA_OUT"
}

# list of all transaction type identifiers that have itemization rule applied to it
# TODO: need to update this list: PAR_CON?, PAR_MEMO?, REATT_TO?
itemization_transaction_type_identifier_list = ['INDV_REC', 'PAR_CON', 'PAR_MEMO', 'IK_REC', 'REATT_FROM', 'REATT_TO']

# DICTIONARY OF ALL TRANSACTIONS TYPE IDENTIFIERS THAT ARE IMPLEMENTED AS 2 TRANSACTIONS IN 1 SCREEN FOR SCHED_A TO SCHED_A TABLE
# TODO: need to decide if we need add "EAR_REC:EAR_REC_MEMO, PAC_EAR_REC:PAC_EAR_MEMO" to this list
TWO_TRANSACTIONS_ONE_SCREEN_SA_SA_TRANSTYPE_DICT = { 
                                            "EAR_REC_RECNT_ACC": "EAR_REC_RECNT_ACC_MEMO",
                                            "EAR_REC_CONVEN_ACC": "EAR_REC_CONVEN_ACC_MEMO",
                                            "EAR_REC_HQ_ACC": "EAR_REC_HQ_ACC_MEMO",
                                            "EAR_REC": "EAR_MEMO",
                                            "PAC_EAR_REC": "PAC_EAR_MEMO" 
                                        }

TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT = { 
                                            "CON_EAR_DEP": "CON_EAR_OUT_DEP",
                                            "CON_EAR_UNDEP" : "CON_EAR_UNDEP_MEMO",
                                            "PAC_CON_EAR_DEP" : "PAC_CON_EAR_DEP_OUT",
                                            "PAC_CON_EAR_UNDEP" : "PAC_CON_EAR_UNDEP_MEMO",
                                        }

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
                """The Transaction ID: {} is not in the specified format. 
                Transaction IDs start with SA characters""".format(transaction_id))
        return transaction_id
    except Exception:
        raise


def validate_sa_data(data):
    """
    validate: mandatory sa fields
    """
    check_mandatory_fields_SA(data, MANDATORY_FIELDS_SCHED_A)

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
                """The following mandatory fields are required in order to
                 save data to schedA table: {}""".format(','.join(errors)))
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
            """Invalid Input: Expecting a decimal value like 18.11, 24.07. 
            Input received: {}""".format(value))



# TODO: update this function to take one argument of data_dic
def post_sql_schedA(cmte_id, 
                    report_id, 
                    line_number, 
                    transaction_type, 
                    transaction_id, 
                    back_ref_transaction_id, 
                    back_ref_sched_name, 
                    entity_id, 
                    contribution_date, 
                    contribution_amount, 
                    purpose_description, 
                    memo_code, 
                    memo_text, 
                    election_code, 
                    election_other_description, 
                    donor_cmte_id, 
                    donor_cmte_name, 
                    transaction_type_identifier):
    """persist one sched_a item."""
    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute("""
            INSERT INTO public.sched_a 
            (cmte_id, report_id, line_number, transaction_type, 
            transaction_id, back_ref_transaction_id, back_ref_sched_name, 
            entity_id, contribution_date, contribution_amount, purpose_description, 
            memo_code, memo_text, election_code, election_other_description, 
            create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, [cmte_id, report_id, line_number, transaction_type, 
            transaction_id, back_ref_transaction_id, back_ref_sched_name, 
            entity_id, contribution_date, contribution_amount, purpose_description, 
            memo_code, memo_text, election_code, election_other_description, 
            datetime.datetime.now(), donor_cmte_id, donor_cmte_name, 
            transaction_type_identifier])
    except Exception:
        raise


# def get_list_all_schedA(report_id, cmte_id):
#     """
#     load sched_a items from DB
#     """
#     return get_list_schedA(report_id, cmte_id)

def get_list_schedA(report_id, cmte_id, transaction_id = None, include_deleted_trans_flag = False):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            if transaction_id:
                if not include_deleted_trans_flag:
                    query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                                    FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s AND delete_ind is distinct from 'Y'"""
                else:
                    query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                                    FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s"""

                cursor.execute("""SELECT json_agg(t) FROM (""" + query_string +
                            """) t""", [report_id, cmte_id, transaction_id])
            else:
                if not include_deleted_trans_flag:
                    query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                                FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""
                else:
                    query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                                FROM public.sched_a WHERE report_id = %s AND cmte_id = %s ORDER BY transaction_id DESC"""

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
            query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
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

def remove_sql_schedA(transaction_id, report_id, cmte_id):
    """delete a sched_a item
    """
    try:
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from Sched_A table
            cursor.execute("""DELETE FROM public.sched_a WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s""", [
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
            cursor.execute("""UPDATE public.sched_a SET back_ref_transaction_id = %s WHERE back_ref_transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [
                           None, transaction_id, report_id, cmte_id])
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


def func_aggregate_amount(contribution_date, transaction_type_identifier, entity_id, cmte_id):
    """
    query aggregate amount based on start/end date, transaction_type, entity_id and cmte_id
    """
    try:
        with connection.cursor() as cursor:

            cursor.execute("""SELECT aggregate_amt FROM sched_a  WHERE entity_id = %s AND transaction_type_identifier = %s AND cmte_id = %s 
AND extract('year' FROM contribution_date) = extract('year' FROM %s::date)
AND contribution_date <= %s::date
AND memo_code IS NULL 
AND delete_ind is distinct FROM 'Y' 
ORDER BY contribution_date DESC;""", [entity_id, transaction_type_identifier, cmte_id, contribution_date, contribution_date])

            # cursor.execute("""SELECT COALESCE(SUM(contribution_amount),0) FROM public.sched_a WHERE entity_id = %s AND transaction_type_identifier = %s 
            # AND cmte_id = %s AND contribution_date >= %s AND contribution_date <= %s AND delete_ind is distinct FROM 'Y'""", [
            #                entity_id, transaction_type_identifier, cmte_id, aggregate_start_date, aggregate_end_date])
            # print(cursor.query)
            result = cursor.fetchone()
            # print(result)
        if result is None:
          aggregate_amt = 0
        elif result[0] is None:
          aggregate_amt = 0
        else:
          aggregate_amt = result[0]
        return aggregate_amt
    except Exception as e:
        raise Exception('The aggregate_amount function is throwing an error: ' + str(e))


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
            cursor.execute("""SELECT t1.contribution_amount, t1.transaction_id, t1.report_id, t1.line_number, t1.contribution_date, 
(SELECT t2.delete_ind FROM public.reports t2 WHERE t2.report_id = t1.report_id), t1.memo_code
FROM public.sched_a t1 
WHERE entity_id = %s AND transaction_type_identifier = %s AND cmte_id = %s AND contribution_date >= %s 
AND contribution_date <= %s AND delete_ind is distinct FROM 'Y' 
ORDER BY contribution_date ASC, create_date ASC""", [
                           entity_id, transaction_type_identifier, cmte_id, aggregate_start_date, aggregate_end_date])
            transactions_list = cursor.fetchall()
        return transactions_list
    except Exception as e:
        raise Exception(
            'The list_all_transactions_entity function is throwing an error: ' + str(e))

def get_linenumber_itemization(transaction_type_identifier, aggregate_amount, itemization_value, line_number):
    try:
        if transaction_type_identifier in itemization_transaction_type_identifier_list:
            if aggregate_amount <= itemization_value:
                return "11AII"
            else:
                return "11AI" 
        else:
            return line_number
    except Exception as e:
        raise Exception('The get_linenumber_itemization function is throwing an error: ' + str(e))

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
        child_flag = False
        itemization_value = 200
        itemized_transaction_list = []
        unitemized_transaction_list = []
        form_type = find_form_type(report_id, cmte_id)
        aggregate_start_date, aggregate_end_date = find_aggregate_date(form_type, contribution_date)
        # checking for child tranaction identifer for updating auto generated SB transactions
        if transaction_type_identifier in AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.keys():
            child_flag = True
            child_transaction_type_identifier = AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.get(transaction_type_identifier)
        # make sure transaction list comes back sorted by contribution_date ASC
        transactions_list = list_all_transactions_entity(
            aggregate_start_date, aggregate_end_date, transaction_type_identifier, entity_id, cmte_id)
        aggregate_amount = 0
        for transaction in transactions_list:
            if transaction[5] != 'Y':
                if transaction[6] != 'X':
                    aggregate_amount += transaction[0]
                # Removed report_id constraint as we have to modify aggregate amount irrespective of report_id
                # if str(report_id) == str(transaction[2]):
                if contribution_date <= transaction[4]:
                    line_number = get_linenumber_itemization(transaction_type_identifier, aggregate_amount, itemization_value, transaction[3])
                    put_sql_linenumber_schedA(cmte_id, line_number, transaction[1], entity_id, aggregate_amount)
                    
                #Updating aggregate amount to child auto generate sched B transactions
                if child_flag:
                    child_SB_transaction_list = get_list_child_transactionId_schedB(cmte_id, transaction[1])
                    for child_SB_transaction in child_SB_transaction_list:
                        put_sql_agg_amount_schedB(cmte_id, child_SB_transaction[0], aggregate_amount)

    except Exception as e:
        raise Exception(
            'The update_linenumber_aggamt_transactions_SA function is throwing an error: ' + str(e))


def put_sql_linenumber_schedA(cmte_id, line_number, transaction_id, entity_id, aggregate_amount):
    """
    update line number
    """
    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute("""UPDATE public.sched_a SET line_number = %s, aggregate_amt = %s WHERE transaction_id = %s AND cmte_id = %s AND entity_id = %s AND delete_ind is distinct from 'Y'""",
                           [line_number, aggregate_amount, transaction_id, cmte_id, entity_id])
            if (cursor.rowcount == 0):
                raise Exception(
                    'put_sql_linenumber_schedA function: The Transaction ID: {} does not exist in schedA table'.format(transaction_id))
    except Exception:
        raise

"""
**************************************************** API FUNCTIONS - SCHED A TRANSACTION *************************************************************
"""
def post_schedA(datum):
    """save sched_a item and the associated entities."""
    try:
        # save entities first
        if 'entity_id' in datum:
            # print('entity_id passed:{}'.format(datum.get('entity_id')))
            # print(datum.get('cmte_id'))
            get_data = {
                'cmte_id': datum.get('cmte_id'),
                'entity_id': datum.get('entity_id')
            }

            # need this update for FEC entity
            if get_data['entity_id'].startswith('FEC'):
                get_data['cmte_id'] = 'C00000000'
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
            entity_flag = True
        else:
            entity_data = post_entities(datum)
            entity_flag = False

        # continue to save transaction
        entity_id = entity_data.get('entity_id')
        # print('post_scheda {}'.format(entity_id))
        datum['entity_id'] = entity_id
        trans_char = "SA"
        transaction_id = get_next_transaction_id(trans_char)
        datum['transaction_id'] = transaction_id
        try:
            post_sql_schedA(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), check_decimal(datum.get(
                'contribution_amount')), datum.get('purpose_description'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), datum.get('donor_cmte_name'), datum.get('transaction_type_identifier'))
            try:
                if datum.get('transaction_type_identifier') in AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT:
                    child_datum = AUTO_parent_SA_to_child_SB_dict(datum)
                    child_datum['expenditure_purpose'] = "In-Kind #" + transaction_id
                    if datum.get('transaction_type_identifier') in ['IK_TRAN', 'IK_TRAN_FEA']:
                        child_datum['beneficiary_cmte_id'] = None
                        child_datum['other_name'] = None
                    child_data = post_schedB(child_datum)
                elif datum.get('transaction_type_identifier') in TWO_TRANSACTIONS_ONE_SCREEN_SA_SA_TRANSTYPE_DICT:
                    check_mandatory_fields_SA(datum, MANDATORY_CHILD_FIELDS_SCHED_A)
                    child_datum = child_SA_to_parent_schedA_dict(datum)
                    child_data = post_schedA(child_datum)
                elif datum.get('transaction_type_identifier') in TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT:
                    if not 'child_datum' in datum:
                        raise Exception('child data missing!!!') 
                    child_datum = datum.get('child_datum')
                    # update some filds and ensure the parent-child relationaship
                    child_datum['cmte_id'] = datum.get('cmte_id')
                    child_datum['report_id'] = datum.get('report_id')
                    child_datum['transaction_type_identifier'] = TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT.get(
                        datum.get('transaction_type_identifier'))
                    child_datum['line_number'], child_datum['transaction_type'] = get_line_number_trans_type(
                        child_datum.get('transaction_type_identifier')
                    )
                    child_datum['back_ref_transaction_id'] = transaction_id
                    child_data = post_schedB(child_datum)
                else:
                    pass
            except:
                remove_schedA(datum)
                raise
        except Exception as e:
            if entity_flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {
                    'cmte_id': datum.get('cmte_id'),
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
            forms_obj = get_list_schedA(report_id, cmte_id, transaction_id)
            for obj in forms_obj:
                obj.update({'api_call' : 'sa/schedA'})

            childA_forms_obj = get_list_child_schedA(
                report_id, cmte_id, transaction_id)
            for obj in childA_forms_obj:
                obj.update({'api_call' : 'sa/schedA'})

            childB_forms_obj = get_list_child_schedB(
                report_id, cmte_id, transaction_id)
            for obj in childB_forms_obj:
                obj.update({'api_call' : 'sb/schedB'})

            child_forms_obj = childA_forms_obj + childB_forms_obj
            # for obj in childB_forms_obj:
            #     obj.update({'api_call':''})
            if len(child_forms_obj) > 0:
                forms_obj[0]['child'] = child_forms_obj
        else:
            forms_obj = get_list_schedA(report_id, cmte_id)
            for obj in forms_obj:
                obj.update({'api_call' : 'sa/schedA'})

        return forms_obj
    except:
        raise


def put_schedA(datum):
    """update sched_a item
    """
    try:
        check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        transaction_id = check_transaction_id(datum.get('transaction_id'))

        # TODO: need to discuss biz logic behind prev_transation_data???
        prev_transaction_data = get_schedA(datum)[0]
        entity_flag = False
        if 'entity_id' in datum:
            entity_flag = True
            get_data = {
                'cmte_id': datum.get('cmte_id'),
                'entity_id': datum.get('entity_id')
            }
            # need this update for FEC entity
            if get_data['entity_id'].startswith('FEC'):
                get_data['cmte_id'] = 'C00000000'
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
        else:
            entity_data = post_entities(datum)
        entity_id = entity_data.get('entity_id')
        datum['entity_id'] = entity_id
        try:
            put_sql_schedA(datum.get('cmte_id'), datum.get('report_id'), datum.get('line_number'), datum.get('transaction_type'), transaction_id, datum.get('back_ref_transaction_id'), datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get(
                'contribution_amount'), datum.get('purpose_description'), datum.get('memo_code'), datum.get('memo_text'), datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), datum.get('donor_cmte_name'), datum.get('transaction_type_identifier'))
            try:
                if datum.get('transaction_type_identifier') in AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.keys():
                    child_datum = AUTO_parent_SA_to_child_SB_dict(datum)
                    child_datum['expenditure_purpose'] = "In-Kind #" + transaction_id
                    if datum.get('transaction_type_identifier') in ['IK_TRAN', 'IK_TRAN_FEA']:
                        child_datum['beneficiary_cmte_id'] = None
                        child_datum['other_name'] = None
                    child_transaction_id = get_child_transaction_schedB(datum.get('cmte_id'), datum.get('report_id'), transaction_id)
                    if child_transaction_id is None:
                        child_data = post_schedB(child_datum)
                        # child_transaction_id = get_next_transaction_id("SB")
                        # post_sql_schedB(datum.get('cmte_id'), datum.get('report_id'), child_line_number, child_transaction_type, child_transaction_id, transaction_id, datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), '0.00', expenditure_purpose, None, None, None, datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), None, datum.get('donor_cmte_name'), None, None, None, None, None, None, child_transaction_type_identifier)
                    else:
                        child_datum['transaction_id'] = child_transaction_id
                        child_data = put_schedB(child_datum)
                        # put_sql_schedB(datum.get('cmte_id'), datum.get('report_id'), child_line_number, child_transaction_type, child_transaction_id, transaction_id, datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), '0.00', expenditure_purpose, None, None, None, datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), None, datum.get('donor_cmte_name'), None, None, None, None, None, None, child_transaction_type_identifier)
                    child_SA_transaction_id = get_child_transaction_schedA(datum.get('cmte_id'), datum.get('report_id'), transaction_id)
                    if child_SA_transaction_id is not None:
                        delete_sql_schedA(child_SA_transaction_id, datum.get('report_id'), datum.get('cmte_id'))
                elif datum.get('transaction_type_identifier') in TWO_TRANSACTIONS_ONE_SCREEN_SA_SA_TRANSTYPE_DICT.keys():
                    child_datum = child_SA_to_parent_schedA_dict(datum)
                    check_mandatory_fields_SA(datum, MANDATORY_CHILD_FIELDS_SCHED_A)
                    child_transaction_id = get_child_transaction_schedA(datum.get('cmte_id'), datum.get('report_id'), transaction_id)
                    if child_transaction_id is None:
                        child_data = post_schedA(child_datum)
                    else:
                        child_datum['transaction_id'] = child_transaction_id
                        child_data = put_schedA(child_datum)
                    # TODO: not sure why we need to delete a sched_b item here?    
                    child_SB_transaction_id = get_child_transaction_schedB(datum.get('cmte_id'), datum.get('report_id'), transaction_id)
                    if child_SB_transaction_id is not None:
                        delete_sql_schedB(child_SB_transaction_id, datum.get('report_id'), datum.get('cmte_id'))
                elif datum.get('transaction_type_identifier') in TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT:
                    if not 'child_datum' in datum:
                        raise Exception('child data missing!!!') 
                    child_datum = datum.get('child_datum')
                    # update some filds and ensure the parent-child relationaship
                    child_datum['cmte_id'] = datum.get('cmte_id')
                    child_datum['report_id'] = datum.get('report_id')
                    child_datum['transaction_type_identifier'] = TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT.get(
                        datum.get('transaction_type_identifier'))
                    child_datum['line_number'], child_datum['transaction_type'] = get_line_number_trans_type(
                        child_datum.get('transaction_type_identifier')
                    )
                    child_datum['back_ref_transaction_id'] = transaction_id
                    if not 'transaction_id' in child_datum:
                        child_SB_transaction_id = get_child_transaction_schedB(datum.get('cmte_id'), datum.get('report_id'), transaction_id)
                        if not child_SB_transaction_id:
                            child_data = post_schedB(child_datum)
                        else:
                            child_datum['transaction_id'] = child_SB_transaction_id
                            child_data = put_schedB(child_datum)
                    else:
                        child_data = put_schedB(child_datum)
            except:
                put_sql_schedA(prev_transaction_data.get('cmte_id'), prev_transaction_data.get('report_id'), prev_transaction_data.get('line_number'), prev_transaction_data.get('transaction_type'), transaction_id, prev_transaction_data.get('back_ref_transaction_id'), prev_transaction_data.get('back_ref_sched_name'), entity_id, prev_transaction_data.get('contribution_date'), prev_transaction_data.get(
                'contribution_amount'), prev_transaction_data.get('purpose_description'), prev_transaction_data.get('memo_code'), prev_transaction_data.get('memo_text'), prev_transaction_data.get('election_code'), prev_transaction_data.get('election_other_description'), prev_transaction_data.get('donor_cmte_id'), prev_transaction_data.get('donor_cmte_name'), prev_transaction_data.get('transaction_type_identifier'))
                raise
        except Exception as e:
            if entity_flag:
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

def remove_schedA(data):
    try:
        cmte_id = data.get('cmte_id')
        report_id = data.get('report_id')
        transaction_id = check_transaction_id(data.get('transaction_id'))
        remove_sql_schedA(transaction_id, report_id, cmte_id)
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
        if 'entity_id' in data and check_null_value(data.get('entity_id')):
            datum['entity_id'] = data.get('entity_id')
        datum['line_number'], datum['transaction_type'] = get_line_number_trans_type(data.get('transaction_type_identifier'))

        if data.get('transaction_type_identifier') in TWO_TRANSACTIONS_ONE_SCREEN_SA_SA_TRANSTYPE_DICT.keys():

            child_datum = {
            'child_transaction_type_identifier': TWO_TRANSACTIONS_ONE_SCREEN_SA_SA_TRANSTYPE_DICT.get(data.get('transaction_type_identifier')),
            'child_back_ref_sched_name': data.get('child*back_ref_sched_name'),
            'child_contribution_date': data.get('child*contribution_date'),
            'child_contribution_amount': data.get('child*contribution_amount'),
            'child_purpose_description': data.get('child*purpose_description'),
            'child_memo_code': data.get('child*memo_code'),
            'child_memo_text': data.get('child*memo_text'),
            'child_election_code': data.get('election_code'),
            'child_election_other_description': data.get('election_other_description'),
            'child_entity_type': data.get('child*entity_type'),
            'child_entity_name': data.get('child*entity_name'),
            'child_first_name': data.get('child*first_name'),
            'child_last_name': data.get('child*last_name'),
            'child_middle_name': data.get('child*middle_name'),
            'child_preffix': data.get('child*prefix'),
            'child_suffix': data.get('child*suffix'),
            'child_street_1': data.get('child*street_1'),
            'child_street_2': data.get('child*street_2'),
            'child_city': data.get('child*city'),
            'child_state': data.get('child*state'),
            'child_zip_code': data.get('child*zip_code'),
            'child_occupation': data.get('child*occupation'),
            'child_employer': data.get('child*employer'),
            'child_ref_cand_cmte_id': data.get('child*ref_cand_cmte_id'),
            'child_donor_cmte_id': data.get('child*donor_cmte_id'),
            'child_donor_cmte_name': data.get('child*donor_cmte_name')
            }
            if 'child*entity_id' in data and check_null_value(data.get('child*entity_id')):
                child_datum['child_entity_id'] = data.get('child*entity_id')
            child_datum['child_line_number'], child_datum['child_transaction_type'] = get_line_number_trans_type(child_datum.get('child_transaction_type_identifier'))
            datum = {**datum, **child_datum}
      
        if data.get('transaction_type_identifier') in TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT:
            child_datum = {k.split('*')[1]:v for k,v in data.items() if k.startswith('child')}
            datum['child_datum'] = child_datum

        return datum
    except:
        raise

def child_SA_to_parent_schedA_dict(data):
    try:
        datum = {
            'report_id': data.get('report_id'),
            'cmte_id': data.get('cmte_id'),
            'transaction_type_identifier': data.get('child_transaction_type_identifier'),
            'back_ref_sched_name': data.get('child_back_ref_sched_name'),
            'contribution_date': date_format(data.get('child_contribution_date')),
            'contribution_amount': check_decimal(data.get('child_contribution_amount')),
            'purpose_description': data.get('child_purpose_description'),
            'memo_code': data.get('child_memo_code'),
            'memo_text': data.get('child_memo_text'),
            'election_code': data.get('child_election_code'),
            'election_other_description': data.get('child_election_other_description'),
            'entity_type': data.get('child_entity_type'),
            'entity_name': data.get('child_entity_name'),
            'first_name': data.get('child_first_name'),
            'last_name': data.get('child_last_name'),
            'middle_name': data.get('child_middle_name'),
            'preffix': data.get('child_preffix'),
            'suffix': data.get('child_suffix'),
            'street_1': data.get('child_street_1'),
            'street_2': data.get('child_street_2'),
            'city': data.get('child_city'),
            'state': data.get('child_state'),
            'zip_code': data.get('child_zip_code'),
            'occupation': data.get('child_occupation'),
            'employer': data.get('child_employer'),
            'ref_cand_cmte_id': data.get('child_ref_cand_cmte_id'),
            'donor_cmte_id': data.get('child_donor_cmte_id'),
            'donor_cmte_name': data.get('child_donor_cmte_name'),
            'line_number': data.get('child_line_number'),
            'transaction_type': data.get('child_transaction_type'),
            'back_ref_transaction_id': data.get('transaction_id'),
            }
        if 'child_entity_id' in data and check_null_value(data.get('child_entity_id')):
            datum['entity_id'] = data.get('child_entity_id')

        return datum
    except:
        raise

def AUTO_parent_SA_to_child_SB_dict(data):
    try:
        datum = {
            'report_id': data.get('report_id'),
            'cmte_id': data.get('cmte_id'),
            'transaction_type_identifier': AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.get(data.get('transaction_type_identifier')),
            'back_ref_sched_name': data.get('back_ref_sched_name'),
            'expenditure_date': data.get('contribution_date'),
            'expenditure_amount': check_decimal(data.get('contribution_amount')),
            'semi_annual_refund_bundled_amount': check_decimal(
                data.get('semi_annual_refund_bundled_amount', '0.0')
            ),
            'category_code': None,
            'memo_code': data.get('memo_code'),
            'memo_text': data.get('memo_text'),
            'election_code': data.get('election_code'),
            'election_other_description': data.get('election_other_description'),
            'beneficiary_cmte_id': data.get('donor_cmte_id'),
            'beneficiary_cand_id': None,
            'other_name': data.get('donor_cmte_name'),
            'other_street_1': None,
            'other_street_2': None,
            'other_city': None,
            'other_state': None,
            'other_zip': None,
            'nc_soft_account': None,
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
            'back_ref_transaction_id': data.get('transaction_id'),
            'entity_id': data.get('entity_id')
            }
        datum['line_number'], datum['transaction_type'] = get_line_number_trans_type(datum.get('transaction_type_identifier'))

        return datum
    except:
        raise

def get_child_transaction_schedB(cmte_id, report_id, back_ref_transaction_id):
    """
    load child sched_b transaction_id
    """
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

def get_child_transaction_schedA(cmte_id, report_id, back_ref_transaction_id):
    """
    load child sched_a transaction_id
    """
    try:
        with connection.cursor() as cursor:
            query_string = """SELECT transaction_id FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s AND delete_ind is distinct from 'Y'"""
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

    # POST api: create new transactions and children transactions if any
    if request.method == 'POST':
        try:
            validate_sa_data(request.data)
            cmte_id = request.user.username
            report_id = check_report_id(request.data.get('report_id'))
            # To check if the report id exists in reports table
            form_type = find_form_type(report_id, cmte_id)
            datum = schedA_sql_dict(request.data)
            datum['report_id'] = report_id
            datum['cmte_id'] = cmte_id
            data = post_schedA(datum)
            output = get_schedA(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedA API - POST is throwing an exception: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
            for obj in datum:
                obj.update({'api_call' : 'sa/schedA'})
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response("The schedA API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    # PUT api call handled here
    if request.method == 'PUT':
        try:
            validate_sa_data(request.data)
            datum = schedA_sql_dict(request.data)
            if 'transaction_id' in request.data and check_null_value(request.data.get('transaction_id')):
                datum['transaction_id'] = request.data.get('transaction_id')
            else:
                raise Exception('Missing Input: transaction_id is mandatory')
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
            data = put_schedA(datum)
            output = get_schedA(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response("The schedA API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    # delete api call handled here
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
            # if not('report_id' in request.query_params):
            #     raise Exception('Missing Input: Report_id is mandatory')
            # # handling null,none value of report_id
            # if check_null_value(request.query_params.get('report_id')):
            #     report_id = check_report_id(request.query_params.get('report_id'))
            # else:
            #     report_id = "0"
            # # end of handling
            # if report_id == "0":
            #     aggregate_date = datetime.datetime.today()
            # else:
            #     aggregate_date = report_end_date(report_id, cmte_id)
            transaction_type_identifier = request.query_params.get('transaction_type_identifier')
            contribution_date = date_format(request.query_params.get('contribution_date'))
            if 'entity_id' in request.query_params and check_null_value(request.query_params.get('entity_id')):
                entity_id = request.query_params.get('entity_id')
            else:
                entity_id = "0"
            if 'contribution_amount' in request.query_params and check_null_value(request.query_params.get('contribution_amount')):
                contribution_amount = check_decimal(
                    request.query_params.get('contribution_amount'))
            else:
                contribution_amount = "0"
            # form_type = find_form_type(report_id, cmte_id)
            # aggregate_start_date, aggregate_end_date = find_aggregate_date(form_type, aggregate_date)
            aggregate_amt = func_aggregate_amount(contribution_date, transaction_type_identifier, entity_id, cmte_id)
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
        raise Exception('The report_end_date function is throwing an error: ' + str(e))


"""
******************************************************************************************************************************
END - AGGREGATE AMOUNT API - SCHED_A APP
******************************************************************************************************************************
"""
"""
******************************************************************************************************************************
TRASH RESTORE TRANSACTIONS API - SCHED_A APP (MOVED FROM CORE APP TO AVOID FUNCTION USAGE RESTRICTIONS) - PRAVEEN
******************************************************************************************************************************
"""
def trash_restore_sql_transaction(report_id, transaction_id, _delete='Y'):
    """trash or restore sched_a transaction by updating delete_ind"""
    try:
        with connection.cursor() as cursor:
            # UPDATE delete_ind flag to Y in DB
            _sql = """
            UPDATE public.sched_a 
            SET delete_ind = '{}'
            WHERE report_id = '{}'
                    AND transaction_id = '{}'
            """.format(_delete, report_id, transaction_id)
            cursor.execute(_sql)
            if not cursor.rowcount:
                raise Exception(
                    """The transaction ID: {} is either already deleted
                     or does not exist in SCHEDULE A table""".format(transaction_id))
    except Exception:
        raise

@api_view(['PUT'])
def trash_restore_transactions(request):
    """api for trash and resore transactions. 
       we are doing soft-delete only, mark delete_ind to 'Y'
       
       request payload in this format:
        {
            "actions": [
                {
                    "action": "restore",
                    "report_id": "123",
                    "transaction_id": "SA20190610000000087"
                },
                {
                    "action": "trash",
                    "report_id": "456",
                    "transaction_id": "SA20190610000000087"
                }
            ]
        }
 
    """
    for _action in request.data.get('actions', []):
        report_id = _action.get('report_id', '')
        transaction_id = _action.get('transaction_id', '')
        # print(transaction_id[0:2])
        cmte_id = request.user.username

        action = _action.get('action', '')
        _delete = 'Y' if action == 'trash' else ''
        # get_schedA data, do sql transaction, update aggregation
        try:
            datum = get_list_schedA(report_id, cmte_id, transaction_id, True)[0]
            trash_restore_sql_transaction( 
                report_id,
                transaction_id, 
                _delete)
            update_linenumber_aggamt_transactions_SA(datetime.datetime.strptime(datum.get('contribution_date'), '%Y-%m-%d').date(
            ), datum.get('transaction_type_identifier'), datum.get('entity_id'), datum.get('cmte_id'), datum.get('report_id'))
        except Exception as e:
            return Response("The trash_restore_transactions API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

    return Response({"result":"success"}, status=status.HTTP_200_OK)
"""
******************************************************************************************************************************
END - TRASH RESTORE TRANSACTIONS API - SCHED_A APP (MOVED FROM CORE APP)
******************************************************************************************************************************
"""

