import datetime
import json
import logging
import os
from decimal import Decimal
from django.utils import timezone
import requests
import copy
from functools import lru_cache
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from fecfiler.core.views import (
    NoOPError,
    check_null_value,
    check_report_id,
    date_format,
    delete_entities,
    get_entities,
    post_entities,
    put_entities,
    remove_entities,
    undo_delete_entities,
    superceded_report_id_list,
    get_sched_h_transaction_table,
)

from fecfiler.core.transaction_util import (
    get_line_number_trans_type,
    update_earmark_parent_purpose,
    cmte_type,
    get_sched_b_transactions,
    get_transaction_type_descriptions,
)

from fecfiler.core.aggregation_helper import (
    update_activity_event_amount_ytd_h4,
    update_activity_event_amount_ytd_h6,
    load_schedH4,
    load_schedH6,
    update_aggregate_sf,
    update_aggregate_se,
    load_schedF,
    load_schedE,
    update_aggregate_sl,
)

from fecfiler.core.report_helper import renew_report_update_date

from fecfiler.sched_B.views import (
    delete_schedB,
    get_list_child_schedB,
    get_schedB,
    post_schedB,
    put_schedB,
    schedB_sql_dict,
    put_sql_schedB,
    post_sql_schedB,
    put_sql_agg_amount_schedB,
    get_list_child_transactionId_schedB,
    delete_sql_schedB,
)

from fecfiler.sched_L.views import update_sl_summary
from fecfiler.core.report_helper import new_report_date

# from fecfile.core.aggregation_helper import
# from fecfiler.sched_H.views import get_list_schedH4, get_list_schedH6

# Create your views here.
logger = logging.getLogger(__name__)

# mandatory fields for shcedule_a records
MANDATORY_FIELDS_SCHED_A = [
    "report_id",
    "transaction_type_identifier",
    "contribution_date",
    "contribution_amount",
    "entity_type",
]

MANDATORY_CHILD_FIELDS_SCHED_A = [
    "report_id",
    "child_transaction_type_identifier",
    "child_contribution_date",
    "child_contribution_amount",
    "child_entity_type",
]

# madatory fields for aggregate amount api call
MANDATORY_FIELDS_AGGREGATE = ["transaction_type_identifier", "contribution_date"]

# list of transaction_type for child sched_b items
CHILD_SCHED_B_TYPES = []

PTY_AGGREGATE_TYPES_HQ = [
    "IND_NP_HQ_ACC",
    "PARTY_NP_HQ_ACC",
    "PAC_NP_HQ_ACC",
    "TRIB_NP_HQ_ACC",
    "EAR_REC_HQ_ACC",
    "JF_TRAN_NP_HQ_IND_MEMO",
    "JF_TRAN_NP_HQ_PAC_MEMO",
    "JF_TRAN_NP_HQ_TRIB_MEMO",
    "OPEXP_HQ_ACC_REG_REF",
    "OPEXP_HQ_ACC_IND_REF",
    "OPEXP_HQ_ACC_TRIB_REF",
]

PTY_AGGREGATE_TYPES_CO = [
    "IND_NP_CONVEN_ACC",
    "PARTY_NP_CONVEN_ACC",
    "PAC_NP_CONVEN_ACC",
    "TRIB_NP_CONVEN_ACC",
    "EAR_REC_CONVEN_ACC",
    "JF_TRAN_NP_CONVEN_IND_MEMO",
    "JF_TRAN_NP_CONVEN_PAC_MEMO",
    "JF_TRAN_NP_CONVEN_TRIB_MEMO",
    "OPEXP_CONV_ACC_REG_REF",
    "OPEXP_CONV_ACC_TRIB_REF",
    "OPEXP_CONV_ACC_IND_REF",
]

PTY_AGGREGATE_TYPES_NPRE = [
    "IND_NP_RECNT_ACC",
    "TRIB_NP_RECNT_ACC",
    "PARTY_NP_RECNT_ACC",
    "PAC_NP_RECNT_ACC",
    "EAR_REC_RECNT_ACC",
    "JF_TRAN_NP_RECNT_IND_MEMO",
    "JF_TRAN_NP_RECNT_PAC_MEMO",
    "JF_TRAN_NP_RECNT_TRIB_MEMO",
    "OTH_DISB_NP_RECNT_REG_REF",
    "OTH_DISB_NP_RECNT_TRIB_REF",
    "OTH_DISB_NP_RECNT_IND_REF",
]

PTY_AGGREGATE_TYPES_RE = [
    "IND_RECNT_REC",
    "PARTY_RECNT_REC",
    "PAC_RECNT_REC",
    "TRIB_RECNT_REC",
]

PAC_AGGREGATE_TYPES_1 = [
    "IND_REC_NON_CONT_ACC",
    "OTH_CMTE_NON_CONT_ACC",
    "BUS_LAB_NON_CONT_ACC",
]

# list of all transaction type identifiers that should
# have single column storage in DB
# TODO: no sure this list is used in this module
SINGLE_TRANSACTION_SCHEDA_LIST = [
    "INDV_REC",
    "OTH_REC",
    "OTH_REC_DEBT",
    "IND_RECNT",
    "PTY_RCNT",
    "PAC_RCNT",
    "TRI_RCNT",
    "IND_NP_RECNT",
    "TRI_NP_RCNT",
    "PTY_NP_RCNT",
    "PAC_NP_RCNT",
    "IND_HQ_ACCNT",
    "TRI_HQ_ACCNT",
    "PTY_HQ_ACCNT",
    "PAC_HQ_ACCNT",
    "IND_CO_ACCNT",
    "TRI_CO_ACCNT",
    "PTY_CO_ACCNT",
    "PAC_CO_ACCNT",
    "IND_CAREY",
    "OT_COM_CAREY",
    "BU_LAB_CAREY",
    "PAR_CON",
    "PAR_MEMO",
    "REATT_FROM",
    "REATT_TO",
    "JF_TRAN",
    "IND_JF_MEM",
    "PTY_JF_MEM",
    "PAC_JF_MEM",
    "TRI_JF_MEM",
    "JF_TRAN_R",
    "IND_JF_R_MEM",
    "PAC_JF_R_MEM",
    "TRI_JF_R_MEM",
    "JF_TRAN_C",
    "IND_JF_C_MEM",
    "PAC_JF_C_MEM",
    "TRI_JF_C_MEM",
    "JF_TRAN_H",
    "IND_JF_H_MEM",
    "PAC_JF_H_MEM",
    "TRI_JF_H_MEM",
]

# list of all transaction type identifiers that should auto generate sched_b item in DB
AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT = {
    "IK_REC": "IK_OUT",
    "IK_BC_REC": "IK_BC_OUT",
    # "CON_EAR_DEP" : "CON_EAR_DEP_MEMO",
    # "CON_EAR_UNDEP" : "CON_EAR_UNDEP_MEMO",
    "PARTY_IK_REC": "PARTY_IK_OUT",
    "PARTY_IK_BC_REC": "PARTY_IK_BC_OUT",
    "PAC_IK_REC": "PAC_IK_OUT",
    "PAC_IK_BC_REC": "PAC_IK_BC_OUT",
    # "PAC_CON_EAR_DEP" : "PAC_CON_EAR_DEP_OUT",
    # "PAC_CON_EAR_UNDEP" : "PAC_CON_EAR_UNDEP_MEMO",
    "IK_TRAN": "IK_TRAN_OUT",
    "IK_TRAN_FEA": "IK_TRAN_FEA_OUT",
}

# list of all transaction type identifiers that should auto generate sched_b item in DB
# AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT = {
#                                     "REATT_FROM" : "REATT_MEMO",
# }
AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT = {}

# CHILD_SCHEDA_AUTO_UPDATE_PARENT_SCHEDA_DICT = {"REATT_MEMO": "REATT_FROM"}
CHILD_SCHEDA_AUTO_UPDATE_PARENT_SCHEDA_DICT = {}
# list of all transaction type identifiers that have itemization rule applied to it
# TODO: need to update this list: PAR_CON?, PAR_MEMO?, REATT_TO?
ITEMIZATION_TRANSACTION_TYPE_IDENTIFIER_LIST = [
    "INDV_REC",
    "PAR_CON",
    "PAR_MEMO",
    "IK_REC",
    "REATT_FROM",
    "REATT_TO",
]

# Updating itemized_ind for the below list
ITEMIZED_IND_UPDATE_TRANSACTION_TYPE_IDENTIFIER = [
    "INDV_REC",
    "PARTN_REC",
    "IK_REC",
    "REATT_FROM",
    "RET_REC",
    "TRIB_REC",
    "IND_NP_HQ_ACC",
    "TRIB_NP_HQ_ACC",
    "IND_NP_CONVEN_ACC",
    "TRIB_NP_CONVEN_ACC",
    "EAR_REC_RECNT_ACC",
    "EAR_REC_CONVEN_ACC",
    "EAR_REC_HQ_ACC",
    "IND_REC_NON_CONT_ACC",
    "BUS_LAB_NON_CONT_ACC",
    "OFFSET_TO_OPEX",
    "TRIB_NP_RECNT_ACC",
    "IND_NP_RECNT_ACC",
    "IND_RECNT_REC",
    "OTH_REC",
    "OTH_REC_DEBT",
]

# DICTIONARY OF ALL TRANSACTIONS TYPE IDENTIFIERS THAT ARE IMPLEMENTED AS 2 TRANSACTIONS IN 1 SCREEN FOR SCHED_A TO SCHED_A TABLE
# the earmark list is emptied becuase the parent and child are saved with different api calls
# TODO: need to clean up the earmark-related code when the decision is final
TWO_TRANSACTIONS_ONE_SCREEN_SA_SA_TRANSTYPE_DICT = {
    # "EAR_REC_RECNT_ACC": "EAR_REC_RECNT_ACC_MEMO",
    # "EAR_REC_CONVEN_ACC": "EAR_REC_CONVEN_ACC_MEMO",
    # "EAR_REC_HQ_ACC": "EAR_REC_HQ_ACC_MEMO",
    # "EAR_REC": "EAR_MEMO",
    # "PAC_EAR_REC": "PAC_EAR_MEMO"
}
EARMARK_SA_CHILD_LIST = [
    "EAR_REC_RECNT_ACC_MEMO",
    "EAR_REC_CONVEN_ACC_MEMO",
    "EAR_REC_HQ_ACC_MEMO",
    "EAR_MEMO",
    "PAC_EAR_MEMO",
]
# "EAR_REC_RECNT_ACC": "EAR_REC_RECNT_ACC_MEMO",

TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT = {
    # "CON_EAR_DEP": "CON_EAR_OUT_DEP",
    # "CON_EAR_UNDEP" : "CON_EAR_UNDEP_MEMO",
    # "PAC_CON_EAR_DEP" : "PAC_CON_EAR_DEP_OUT",
    # "PAC_CON_EAR_UNDEP" : "PAC_CON_EAR_UNDEP_MEMO",
}

API_CALL_SA = {"api_call": "/sa/schedA"}
API_CALL_SB = {"api_call": "/sb/schedB"}
REQ_ELECTION_YR = ""
ELECTION_YR = {"election_year": REQ_ELECTION_YR}

# a list of treansaction types for sched_l(levin funds report) contribuitions
SCHED_L_A_TRAN_TYPES = [
    "LEVIN_PAC_REC",
    "LEVIN_TRIB_REC",
    # "LEVIN_PARTN_MEMO",
    "LEVIN_PARTN_REC",
    "LEVIN_ORG_REC",
    "LEVIN_INDV_REC",
    "LEVIN_NON_FED_REC",
    "LEVIN_NON_FED_REC",
]

SCHEDULE_TO_TABLE_DICT = {
    "SA": ["sched_a"],
    "LA": ["sched_a"],
    "SB": ["sched_b"],
    "LB": ["sched_b"],
    "SC": ["sched_c", "sched_c1", "sched_c2"],
    "SD": ["sched_d"],
    "SE": ["sched_e"],
    "SF": ["sched_f"],
    "SH": ["sched_h1", "sched_h2", "sched_h3", "sched_h4", "sched_h5", "sched_h6"],
    "SL": ["sched_l"],
}


def get_next_transaction_id(trans_char):
    """get next transaction_id with seeding letter, like 'SA' """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT public.get_next_transaction_id(%s)""", [trans_char]
            )
            transaction_id = cursor.fetchone()[0]
            # transaction_id = transaction_ids[0]
        return transaction_id
    except Exception:
        raise


def check_transaction_id(transaction_id):
    """validate transaction id against trsaction types, e.g. SA20190627000000094"""
    try:
        transaction_type_list = ["SA", "LA"]
        transaction_type = transaction_id[0:2]
        if not (transaction_type in transaction_type_list):
            raise Exception(
                """The Transaction ID: {} is not in the specified format. 
                Transaction IDs start with SA characters""".format(
                    transaction_id
                )
            )
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
            if not (field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                """The following mandatory fields are required in order to
                 save data to schedA table: {}""".format(
                    ",".join(errors)
                )
            )
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
            Input received: {}""".format(
                value
            )
        )


# @api_view(['GET'])
# def date_print(request):
#   print(datetime.datetime.now())
#   print(timezone.now())
#   return Response('SUCCESS', status=status.HTTP_200_OK)

# TODO: update this function to take one argument of data_dic
def post_sql_schedA(
    cmte_id,
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
    transaction_type_identifier,
    levin_account_id,
):
    """persist one sched_a item."""
    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute(
                """
            INSERT INTO public.sched_a 
            (
                cmte_id, 
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
                create_date, 
                last_update_date, 
                donor_cmte_id, 
                donor_cmte_name, 
                levin_account_id, 
                transaction_type_identifier
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
                [
                    cmte_id,
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
                    datetime.datetime.now(),
                    datetime.datetime.now(),
                    donor_cmte_id,
                    donor_cmte_name,
                    levin_account_id,
                    transaction_type_identifier,
                ],
            )
            if cursor.rowcount != 1:
                logger.debug("post_sql_schedA failed.")

    except Exception:
        raise


# def get_list_all_schedA(report_id, cmte_id):
#     """
#     load sched_a items from DB
#     """
#     return get_list_schedA(report_id, cmte_id)


def get_list_schedA(
    report_id, cmte_id, transaction_id=None, include_deleted_trans_flag=False
):

    try:
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:
            # GET single row from schedA table
            if transaction_id:
                if not include_deleted_trans_flag:
                    query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier, levin_account_id, itemized_ind
                                    FROM public.sched_a WHERE report_id in ('{}') AND cmte_id = %s AND transaction_id = %s AND delete_ind is distinct from 'Y'""".format(
                        "', '".join(report_list)
                    )
                else:
                    query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier, levin_account_id, itemized_ind
                                    FROM public.sched_a WHERE report_id in ('{}') AND cmte_id = %s AND transaction_id = %s""".format(
                        "', '".join(report_list)
                    )

                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [cmte_id, transaction_id],
                )
            else:
                if not include_deleted_trans_flag:
                    query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier, levin_account_id, itemized_ind
                                FROM public.sched_a WHERE report_id in ('{}') AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC""".format(
                        "', '".join(report_list)
                    )
                else:
                    query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier, levin_account_id, itemized_ind
                                FROM public.sched_a WHERE report_id in ('{}') AND cmte_id = %s ORDER BY transaction_id DESC""".format(
                        "', '".join(report_list)
                    )

                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [cmte_id],
                )
            schedA_list = cursor.fetchone()[0]
            if not schedA_list:
                raise NoOPError(
                    "No transaction found for cmte_id {} and report_id {}".format(
                        cmte_id, report_id
                    )
                )
            merged_list = []
            for dictA in schedA_list:
                entity_id = dictA.get("entity_id")
                data = {"entity_id": entity_id, "cmte_id": cmte_id}
                entity_list = get_entities(data)
                dictEntity = entity_list[0]
                merged_dict = {**dictA, **dictEntity}
                merged_list.append(merged_dict)
        return merged_list
    except Exception:
        raise


def get_list_child_schedA(report_id, cmte_id, transaction_id):
    """
    load all child sched_a items for this transaction
    """
    try:
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:

            # GET child rows from schedA table
            query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, 
            contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, 
            election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier, levin_account_id, itemized_ind
                            FROM public.sched_a WHERE report_id in ('{}') AND cmte_id = %s AND back_ref_transaction_id = %s AND 
                            delete_ind is distinct from 'Y'""".format(
                "', '".join(report_list)
            )

            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                [cmte_id, transaction_id],
            )

            for row in cursor.fetchall():
                # forms_obj.append(data_row)
                data_row = list(row)
                schedA_list = data_row[0]
            merged_list = []
            if not (schedA_list is None):
                for dictA in schedA_list:
                    entity_id = dictA.get("entity_id")
                    data = {"entity_id": entity_id, "cmte_id": cmte_id}
                    entity_list = get_entities(data)
                    dictEntity = entity_list[0]
                    merged_dict = {**dictA, **dictEntity}
                    merged_list.append(merged_dict)
        return merged_list
    except Exception:
        raise


def put_sql_schedA(
    cmte_id,
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
    levin_account_id,
    transaction_type_identifier,
):
    """
    update a schedule_a item
    """
    try:
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute(
                """UPDATE public.sched_a SET line_number = %s, transaction_type = %s, back_ref_transaction_id = %s, back_ref_sched_name = %s, 
              entity_id = %s, contribution_date = %s, contribution_amount = %s, purpose_description = %s, memo_code = %s, memo_text = %s, election_code = %s, 
              election_other_description = %s, donor_cmte_id = %s, donor_cmte_name = %s, levin_account_id = %s, transaction_type_identifier = %s, last_update_date = %s 
              WHERE transaction_id = %s AND report_id in ('{}') AND cmte_id = %s AND delete_ind is distinct from 'Y'""".format(
                    "', '".join(report_list)
                ),
                [
                    line_number,
                    transaction_type,
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
                    levin_account_id,
                    transaction_type_identifier,
                    datetime.datetime.now(),
                    transaction_id,
                    cmte_id,
                ],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "The Transaction ID: {} does not exist in schedA table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def delete_sql_schedA(transaction_id, report_id, cmte_id):
    """delete a sched_a item
    """
    try:
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from Sched_A table
            cursor.execute(
                """UPDATE public.sched_a SET delete_ind = 'Y', last_update_date = %s WHERE transaction_id = %s AND report_id in ('{}') 
              AND cmte_id = %s AND delete_ind is distinct from 'Y'""".format(
                    "', '".join(report_list)
                ),
                [datetime.datetime.now(), transaction_id, report_id, cmte_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "The Transaction ID: {} is either already deleted or does not exist in schedA table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def remove_sql_schedA(transaction_id, report_id, cmte_id):
    """delete a sched_a item
    """
    try:
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from Sched_A table
            cursor.execute(
                """DELETE FROM public.sched_a WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s""",
                [transaction_id, report_id, cmte_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "The Transaction ID: {} is either already deleted or does not exist in schedA table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


# def delete_parent_child_link_sql_schedA(transaction_id, report_id, cmte_id):
#     """delete parent child link in sched_a
#     """
#     try:
#         with connection.cursor() as cursor:
#             # UPDATE back_ref_transaction_id value to null in sched_a table
#             cursor.execute("""UPDATE public.sched_a SET back_ref_transaction_id = %s WHERE back_ref_transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""", [
#                            None, transaction_id, report_id, cmte_id])
#     except Exception:
#         raise


def find_form_type(report_id, cmte_id):
    """
    load form type based on report_id and cmte_id
    """
    try:
        # handling cases where report_id is reported as 0
        if report_id in ["0", "0", 0]:
            return "F3X"
        # end of error handling
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT form_type FROM public.reports WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
                [report_id, cmte_id],
            )
            form_types = cursor.fetchone()
        if cursor.rowcount == 0:
            raise Exception(
                "The Report ID: {} is either already deleted or does not exist in reports table".format(
                    report_id
                )
            )
        else:
            return form_types[0]
    except Exception as e:
        raise Exception("The form_type function is throwing an error:" + str(e))


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
            "The aggregate_start_date function is throwing an error: " + str(e)
        )


def func_aggregate_amount(
    contribution_date, transaction_type_identifier, entity_id, cmte_id
):
    """
    query aggregate amount based on start/end date, transaction_type, entity_id and cmte_id
    """
    try:
        with connection.cursor() as cursor:

            if transaction_type_identifier in PTY_AGGREGATE_TYPES_HQ:
                params = """ AND transaction_type_identifier IN ('{}')""".format(
                    "', '".join(PTY_AGGREGATE_TYPES_HQ)
                )
            elif transaction_type_identifier in PTY_AGGREGATE_TYPES_CO:
                params = """ AND transaction_type_identifier IN ('{}')""".format(
                    "', '".join(PTY_AGGREGATE_TYPES_CO)
                )
            elif transaction_type_identifier in PTY_AGGREGATE_TYPES_NPRE:
                params = """ AND transaction_type_identifier IN ('{}')""".format(
                    "', '".join(PTY_AGGREGATE_TYPES_NPRE)
                )
            elif transaction_type_identifier in PTY_AGGREGATE_TYPES_RE:
                params = """ AND transaction_type_identifier IN ('{}')""".format(
                    "', '".join(PTY_AGGREGATE_TYPES_RE)
                )
            elif transaction_type_identifier in PAC_AGGREGATE_TYPES_1:
                params = """ AND transaction_type_identifier IN ('{}')""".format(
                    "', '".join(PAC_AGGREGATE_TYPES_1)
                )
            else:
                params = """ AND transaction_type_identifier NOT IN ('{}')""".format(
                    "', '".join(
                        PAC_AGGREGATE_TYPES_1
                        + PTY_AGGREGATE_TYPES_HQ
                        + PTY_AGGREGATE_TYPES_CO
                        + PTY_AGGREGATE_TYPES_NPRE
                        + PTY_AGGREGATE_TYPES_RE
                    )
                )

            query_string = """SELECT aggregate_amt FROM sched_a  WHERE entity_id = %s {} AND cmte_id = %s 
    AND extract('year' FROM contribution_date) = extract('year' FROM %s::date)
    AND contribution_date <= %s::date
    AND ((back_ref_transaction_id IS NULL AND memo_code IS NULL) OR (back_ref_transaction_id IS NOT NULL))
    AND delete_ind is distinct FROM 'Y' 
    ORDER BY contribution_date DESC, create_date DESC;""".format(
                params
            )

            cursor.execute(
                query_string, [entity_id, cmte_id, contribution_date, contribution_date]
            )
            result = cursor.fetchone()
        if result is None:
            aggregate_amt = 0
        elif result[0] is None:
            aggregate_amt = 0
        else:
            aggregate_amt = result[0]
        return aggregate_amt
    except Exception as e:
        raise Exception("The aggregate_amount function is throwing an error: " + str(e))


def list_all_transactions_entity(
    aggregate_start_date, aggregate_end_date, entity_id, cmte_id
):
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
            cursor.execute(
                """
            SELECT t1.contribution_amount, 
                t1.transaction_id, 
                t1.report_id, 
                t1.line_number, 
                t1.contribution_date, 
                (SELECT t2.delete_ind FROM public.reports t2 WHERE t2.report_id = t1.report_id), 
                t1.memo_code, 
                t1.back_ref_transaction_id,
                t1.transaction_type_identifier
            FROM public.sched_a t1 
            WHERE entity_id = %s 
            AND cmte_id = %s 
            AND contribution_date >= %s 
            AND contribution_date <= %s 
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY contribution_date ASC, create_date ASC
            """,
                [entity_id, cmte_id, aggregate_start_date, aggregate_end_date],
            )
            transactions_list = cursor.fetchall()
        return transactions_list
    except Exception as e:
        raise Exception(
            "The list_all_transactions_entity function is throwing an error: " + str(e)
        )


def get_linenumber_itemization(
    transaction_type_identifier, aggregate_amount, itemization_value, line_number
):
    try:
        itemized_ind = None
        output_line_number = None
        if transaction_type_identifier in ITEMIZATION_TRANSACTION_TYPE_IDENTIFIER_LIST:
            if aggregate_amount <= itemization_value:
                output_line_number = "11AII"
            else:
                output_line_number = "11AI"
        else:
            output_line_number = line_number

        if (
            transaction_type_identifier
            in ITEMIZED_IND_UPDATE_TRANSACTION_TYPE_IDENTIFIER
        ):
            if aggregate_amount <= itemization_value:
                itemized_ind = "U"
        return output_line_number, itemized_ind
    except Exception as e:
        raise Exception(
            "The get_linenumber_itemization function is throwing an error: " + str(e)
        )


def put_sql_agg_amount_schedA(cmte_id, transaction_id, aggregate_amount):
    """
    update aggregate amount
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE public.sched_a SET aggregate_amt = %s WHERE transaction_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
                [aggregate_amount, transaction_id, cmte_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "put_sql_agg_amount_schedA function: The Transaction ID: {} does not exist in schedA table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def update_linenumber_aggamt_transactions_SA(
    contribution_date, transaction_type_identifier, entity_id, cmte_id, report_id
):
    """
    helper function for updating private contribution line number based on aggrgate amount
    the aggregate amount is a contribution_date-based on incremental update, the line number
    is updated accordingly:
    edit 1: check if the report corresponding to the transaction is deleted or not (delete_ind flag in reports table) 
            and only when it is NOT add contribution_amount to aggregate amount
    edit 2: updation of aggregate amount will roll to all transacctions irrespective of report id and report being filed
    edit 3: if back_ref_transaction_id is none, then check if memo_code is NOT 'X' and if it is not, add contribution_amount to aggregate amount; 
            if back_ref_transaction_id is NOT none, then add irrespective of memo_code, add contribution_amount to aggregate amount
    e.g.
    date, contribution_amount, aggregate_amount, line_number
    1/1/2018, 50, 50, 11AII
    2/1/2018, 60, 110, 11AII
    3/1/2018, 100, 210, 11AI (aggregate_amount > 200, update line number)

    """
    try:
        child_flag_SB = False
        child_flag_SA = False
        itemization_value = 200
        # itemized_transaction_list = []
        # unitemized_transaction_list = []
        form_type = find_form_type(report_id, cmte_id)
        if isinstance(contribution_date, str):
            contribution_date = date_format(contribution_date)
        aggregate_start_date, aggregate_end_date = find_aggregate_date(
            form_type, contribution_date
        )
        # checking for child tranaction identifer for updating auto generated SB transactions
        if (
            transaction_type_identifier
            in AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT
        ):
            child_flag_SB = True
            child_transaction_type_identifier = AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.get(
                transaction_type_identifier
            )
        # checking for child tranaction identifer for updating auto generated SA transactions
        if (
            transaction_type_identifier
            in AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT
        ):
            child_flag_SA = True
            child_transaction_type_identifier = AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT.get(
                transaction_type_identifier
            )
        # make sure transaction list comes back sorted by contribution_date ASC
        transactions_list = list_all_transactions_entity(
            aggregate_start_date, aggregate_end_date, entity_id, cmte_id
        )
        aggregate_amount = 0
        PAC_aggregate_amount = 0
        HQ_aggregate_amount = 0
        CO_aggregate_amount = 0
        NPRE_aggregate_amount = 0
        RE_aggregate_amount = 0
        REMAIN_aggregate_amount = 0
        committee_type = cmte_type(cmte_id)
        for transaction in transactions_list:
            # checking in reports table if the delete_ind flag is false for the corresponding report
            if transaction[5] != "Y":
                # checking if the back_ref_transaction_id is null or not.
                # If back_ref_transaction_id is none, checking if the transaction is a memo or not, using memo_code not equal to X.
                if transaction[7] != None or (
                    transaction[7] == None and transaction[6] != "X"
                ):
                    if (committee_type == "PAC") and transaction[
                        8
                    ] in PAC_AGGREGATE_TYPES_1:
                        PAC_aggregate_amount += transaction[0]
                        aggregate_amount = PAC_aggregate_amount
                    elif (committee_type == "PTY") and transaction[
                        8
                    ] in PTY_AGGREGATE_TYPES_HQ:
                        HQ_aggregate_amount += transaction[0]
                        aggregate_amount = HQ_aggregate_amount
                    elif (committee_type == "PTY") and transaction[
                        8
                    ] in PTY_AGGREGATE_TYPES_CO:
                        CO_aggregate_amount += transaction[0]
                        aggregate_amount = CO_aggregate_amount
                    elif (committee_type == "PTY") and transaction[
                        8
                    ] in PTY_AGGREGATE_TYPES_NPRE:
                        NPRE_aggregate_amount += transaction[0]
                        aggregate_amount = NPRE_aggregate_amount
                    elif (committee_type == "PTY") and transaction[
                        8
                    ] in PTY_AGGREGATE_TYPES_RE:
                        RE_aggregate_amount += transaction[0]
                        aggregate_amount = RE_aggregate_amount
                    else:
                        REMAIN_aggregate_amount += transaction[0]
                        aggregate_amount = REMAIN_aggregate_amount
                # Removed report_id constraint as we have to modify aggregate amount irrespective of report_id
                # if str(report_id) == str(transaction[2]):
                if contribution_date <= transaction[4]:
                    line_number, itemized_ind = get_linenumber_itemization(
                        transaction[8],
                        aggregate_amount,
                        itemization_value,
                        transaction[3],
                    )
                    put_sql_linenumber_schedA(
                        cmte_id,
                        line_number,
                        itemized_ind,
                        transaction[1],
                        entity_id,
                        aggregate_amount,
                    )

                # Updating aggregate amount to child auto generate sched A transactions
                if child_flag_SA:
                    child_SA_transaction_list = get_list_child_schedA(
                        report_id, cmte_id, transaction[1]
                    )
                    for child_SA_transaction in child_SA_transaction_list:
                        put_sql_agg_amount_schedA(
                            cmte_id,
                            child_SA_transaction.get("transaction_id"),
                            aggregate_amount,
                        )
                # Updating aggregate amount to child auto generate sched B transactions
                if child_flag_SB:
                    child_SB_transaction_list = get_list_child_transactionId_schedB(
                        cmte_id, transaction[1]
                    )
                    for child_SB_transaction in child_SB_transaction_list:
                        put_sql_agg_amount_schedB(
                            cmte_id, child_SB_transaction[0], aggregate_amount
                        )

    except Exception as e:
        raise Exception(
            "The update_linenumber_aggamt_transactions_SA function is throwing an error: "
            + str(e)
        )


def put_sql_linenumber_schedA(
    cmte_id, line_number, itemized_ind, transaction_id, entity_id, aggregate_amount
):
    """
    update line number
    """
    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute(
                """UPDATE public.sched_a SET line_number = %s, itemized_ind = %s, aggregate_amt = %s WHERE transaction_id = %s AND cmte_id = %s AND entity_id = %s AND delete_ind is distinct from 'Y'""",
                [
                    line_number,
                    itemized_ind,
                    aggregate_amount,
                    transaction_id,
                    cmte_id,
                    entity_id,
                ],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "put_sql_linenumber_schedA function: The Transaction ID: {} does not exist in schedA table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def none_to_empty(val):
    if val is None:
        return ""
    return str(val)


def get_in_kind_entity_name(entity_data):
    """
    return entity_name if available,
    else make up one with first_name, last_name, middle_name, prefix and suffix
    """
    logger.debug("get in kind entity name with {}".format(entity_data))
    if entity_data.get("entity_name"):
        return entity_data.get("entity_name")
    return ",".join(
        [
            none_to_empty(entity_data.get("first_name")),
            none_to_empty(entity_data.get("last_name")),
            none_to_empty(entity_data.get("middle_name")),
            none_to_empty(entity_data.get("prefix")),
            none_to_empty(entity_data.get("suffix")),
        ]
    )


"""
**************************************************** API FUNCTIONS - SCHED A TRANSACTION *************************************************************
"""


@new_report_date
def post_schedA(datum):
    """save sched_a item and the associated entities."""
    try:
        # save entities first
        if "entity_id" in datum:
            get_data = {
                "cmte_id": datum.get("cmte_id"),
                "entity_id": datum.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
            entity_flag = True
        else:
            entity_data = post_entities(datum)
            entity_flag = False

        # continue to save transaction
        entity_id = entity_data.get("entity_id")
        datum["entity_id"] = entity_id
        # for sched_l contributions, the transaction is starts with 'SLA'
        if datum.get("transaction_type_identifier") in SCHED_L_A_TRAN_TYPES:
            trans_char = "LA"
            datum["line_number"], datum[
                "transaction_type"
            ] = get_line_number_trans_type(datum.get("transaction_type_identifier"))
        else:
            trans_char = "SA"
        transaction_id = get_next_transaction_id(trans_char)
        datum["transaction_id"] = transaction_id
        # checking if donor cmte id exists then copying entity name to donor committee name as they both are the same
        if "donor_cmte_id" in datum and datum.get("donor_cmte_id") not in [
            "",
            " ",
            None,
            "none",
            "null",
            "None",
        ]:
            datum["donor_cmte_name"] = datum.get("entity_name")
        try:
            logger.debug("saving sched_a transaction with data:{}".format(datum))
            post_sql_schedA(
                datum.get("cmte_id"),
                datum.get("report_id"),
                datum.get("line_number"),
                datum.get("transaction_type"),
                transaction_id,
                datum.get("back_ref_transaction_id"),
                datum.get("back_ref_sched_name"),
                entity_id,
                datum.get("contribution_date"),
                check_decimal(datum.get("contribution_amount")),
                datum.get("purpose_description"),
                datum.get("memo_code"),
                datum.get("memo_text"),
                datum.get("election_code"),
                datum.get("election_other_description"),
                datum.get("donor_cmte_id"),
                datum.get("donor_cmte_name"),
                datum.get("transaction_type_identifier"),
                datum.get("levin_account_id"),
            )
            logger.debug("transaction saved...")
            try:
                if (
                    datum.get("transaction_type_identifier")
                    in AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT
                ):
                    logger.debug("auto generating sched_b child transaction:")
                    child_datum = AUTO_parent_SA_to_child_SB_dict(datum)
                    logger.debug("child data:{}".format(child_datum))

                    # in_kind_entity_name = get_in_kind_entity_name(entity_data)
                    # logger.debug('child in kind name:{}'.format(in_kind_entity_name))
                    child_datum["expenditure_purpose"] = "In-Kind " + datum.get(
                        "purpose_description", " "
                    )

                    if datum.get("transaction_type_identifier") in [
                        "IK_TRAN",
                        "IK_TRAN_FEA",
                    ]:
                        child_datum["beneficiary_cmte_id"] = None
                        child_datum["other_name"] = None
                    child_data = post_schedB(child_datum)
                elif (
                    datum.get("transaction_type_identifier")
                    in AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT
                ):
                    child_datum = copy.deepcopy(datum)
                    child_datum["back_ref_transaction_id"] = datum.get("transaction_id")
                    child_datum["purpose_description"] = "In-Kind " + datum.get(
                        "purpose_description", " "
                    )
                    child_datum[
                        "transaction_type_identifier"
                    ] = AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT.get(
                        datum.get("transaction_type_identifier")
                    )
                    child_datum["line_number"], child_datum[
                        "transaction_type"
                    ] = get_line_number_trans_type(
                        child_datum.get("transaction_type_identifier")
                    )
                    child_data = post_schedA(child_datum)
                elif (
                    datum.get("transaction_type_identifier")
                    in TWO_TRANSACTIONS_ONE_SCREEN_SA_SA_TRANSTYPE_DICT
                ):
                    check_mandatory_fields_SA(datum, MANDATORY_CHILD_FIELDS_SCHED_A)
                    child_datum = child_SA_to_parent_schedA_dict(datum)
                    child_data = post_schedA(child_datum)
                elif (
                    datum.get("transaction_type_identifier")
                    in TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT
                ):
                    if not "child_datum" in datum:
                        raise Exception("child data missing!!!")
                    child_datum = datum.get("child_datum")
                    # update some filds and ensure the parent-child relationaship
                    child_datum["cmte_id"] = datum.get("cmte_id")
                    child_datum["report_id"] = datum.get("report_id")
                    child_datum[
                        "transaction_type_identifier"
                    ] = TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT.get(
                        datum.get("transaction_type_identifier")
                    )
                    child_datum["line_number"], child_datum[
                        "transaction_type"
                    ] = get_line_number_trans_type(
                        child_datum.get("transaction_type_identifier")
                    )
                    child_datum["back_ref_transaction_id"] = transaction_id
                    child_data = post_schedB(child_datum)
                else:
                    pass
            except:
                remove_schedA(datum)
                raise
        except Exception as e:
            # if exceptions saving shced_a, remove entities or rollback entities too
            if entity_flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": datum.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The post_sql_schedA function is throwing an error: " + str(e)
            )

        # update line number based on aggregate amount info
        if transaction_id.startswith("SA"):
            update_linenumber_aggamt_transactions_SA(
                datum.get("contribution_date"),
                datum.get("transaction_type_identifier"),
                entity_id,
                datum.get("cmte_id"),
                datum.get("report_id"),
            )
        if datum.get("transaction_type_identifier") in SCHED_L_A_TRAN_TYPES:
            print("haha")
            update_aggregate_sl(datum)
            update_sl_summary(datum)
        return datum
    except:
        raise


def get_schedA(data):
    """load sched_a and the child sched_a and sched_b transactions."""
    try:
        tran_desc_dic = get_transaction_type_descriptions()
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedA(report_id, cmte_id, transaction_id)
            for obj in forms_obj:
                obj.update(API_CALL_SA)
                obj.update({"election_year": REQ_ELECTION_YR})

            childA_forms_obj = get_list_child_schedA(report_id, cmte_id, transaction_id)
            for obj in childA_forms_obj:
                obj.update(API_CALL_SA)
                tran_id = obj.get("transaction_type_identifier")
                obj.update(
                    {"transaction_type_description": tran_desc_dic.get(tran_id, "")}
                )
                obj.update({"election_year": REQ_ELECTION_YR})
                # obj.update(ELECTION_YR)

            childB_forms_obj = get_list_child_schedB(report_id, cmte_id, transaction_id)
            for obj in childB_forms_obj:
                tran_id = obj.get("transaction_type_identifier")
                obj.update(
                    {"transaction_type_description": tran_desc_dic.get(tran_id, "")}
                )
                obj.update(API_CALL_SB)
                obj.update({"election_year": REQ_ELECTION_YR})
                # obj.update(ELECTION_YR)

            child_forms_obj = childA_forms_obj + childB_forms_obj
            # for obj in childB_forms_obj:
            #     obj.update({'api_call':''})
            if len(child_forms_obj) > 0:
                forms_obj[0]["child"] = child_forms_obj
        else:
            forms_obj = get_list_schedA(report_id, cmte_id)
            for obj in forms_obj:
                obj.update(API_CALL_SA)
                obj.update({"election_year": REQ_ELECTION_YR})
                # obj.update(ELECTION_YR)

        return forms_obj
    except:
        raise


@new_report_date
def put_schedA(datum):
    """update sched_a item
    """
    try:
        check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        transaction_id = check_transaction_id(datum.get("transaction_id"))

        # TODO: need to discuss biz logic behind prev_transation_data???
        prev_transaction_data = get_schedA(datum)[0]
        entity_flag = False
        if "entity_id" in datum:
            entity_flag = True
            get_data = {
                "cmte_id": datum.get("cmte_id"),
                "entity_id": datum.get("entity_id"),
            }
            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
        else:
            entity_data = post_entities(datum)
        entity_id = entity_data.get("entity_id")
        datum["entity_id"] = entity_id
        # checking if donor cmte id exists then copying entity name to donor committee name as they both are the same
        if "donor_cmte_id" in datum and datum.get("donor_cmte_id") not in [
            "",
            " ",
            None,
            "none",
            "null",
            "None",
        ]:
            datum["donor_cmte_name"] = datum.get("entity_name")
        try:
            put_sql_schedA(
                datum.get("cmte_id"),
                datum.get("report_id"),
                datum.get("line_number"),
                datum.get("transaction_type"),
                transaction_id,
                datum.get("back_ref_transaction_id"),
                datum.get("back_ref_sched_name"),
                entity_id,
                datum.get("contribution_date"),
                datum.get("contribution_amount"),
                datum.get("purpose_description"),
                datum.get("memo_code"),
                datum.get("memo_text"),
                datum.get("election_code"),
                datum.get("election_other_description"),
                datum.get("donor_cmte_id"),
                datum.get("donor_cmte_name"),
                datum.get("levin_account_id"),
                datum.get("transaction_type_identifier"),
            )
            try:
                if (
                    datum.get("transaction_type_identifier")
                    in AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT
                ):
                    child_datum = AUTO_parent_SA_to_child_SB_dict(datum)
                    child_datum["expenditure_purpose"] = "In-Kind #" + transaction_id
                    if datum.get("transaction_type_identifier") in [
                        "IK_TRAN",
                        "IK_TRAN_FEA",
                    ]:
                        child_datum["beneficiary_cmte_id"] = None
                        child_datum["other_name"] = None
                    child_transaction_id = get_child_transaction_schedB(
                        datum.get("cmte_id"), datum.get("report_id"), transaction_id
                    )
                    if child_transaction_id is None:
                        child_data = post_schedB(child_datum)
                        # child_transaction_id = get_next_transaction_id("SB")
                        # post_sql_schedB(datum.get('cmte_id'), datum.get('report_id'), child_line_number, child_transaction_type, child_transaction_id, transaction_id, datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), '0.00', expenditure_purpose, None, None, None, datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), None, datum.get('donor_cmte_name'), None, None, None, None, None, None, child_transaction_type_identifier)
                    else:
                        child_datum["transaction_id"] = child_transaction_id
                        put_sql_schedB(
                            child_datum.get("cmte_id"),
                            child_datum.get("report_id"),
                            child_datum.get("line_number"),
                            child_datum.get("transaction_type"),
                            child_datum.get("transaction_id"),
                            child_datum.get("back_ref_transaction_id"),
                            child_datum.get("back_ref_sched_name"),
                            child_datum.get("entity_id"),
                            child_datum.get("expenditure_date"),
                            child_datum.get("expenditure_amount"),
                            child_datum.get("semi_annual_refund_bundled_amount"),
                            child_datum.get("expenditure_purpose"),
                            child_datum.get("category_code"),
                            child_datum.get("memo_code"),
                            child_datum.get("memo_text"),
                            child_datum.get("election_code"),
                            child_datum.get("election_other_description"),
                            child_datum.get("beneficiary_cmte_id"),
                            child_datum.get("beneficiary_cand_id"),
                            child_datum.get("other_name"),
                            child_datum.get("other_street_1"),
                            child_datum.get("other_street_2"),
                            child_datum.get("other_city"),
                            child_datum.get("other_state"),
                            child_datum.get("other_zip"),
                            child_datum.get("nc_soft_account"),
                            child_datum.get("transaction_type_identifier"),
                            child_datum.get("beneficiary_cand_office"),
                            child_datum.get("beneficiary_cand_state"),
                            child_datum.get("beneficiary_cand_district"),
                            child_datum.get("beneficiary_cmte_name"),
                            child_datum.get("beneficiary_cand_last_name"),
                            child_datum.get("beneficiary_cand_first_name"),
                            child_datum.get("beneficiary_cand_middle_name"),
                            child_datum.get("beneficiary_cand_prefix"),
                            child_datum.get("beneficiary_cand_suffix"),
                            child_datum.get("aggregate_amt"),
                            child_datum.get("beneficiary_cand_entity_id"),
                            child_datum.get("levin_account_id"),
                        )
                        # put_sql_schedB(datum.get('cmte_id'), datum.get('report_id'), child_line_number, child_transaction_type, child_transaction_id, transaction_id, datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), '0.00', expenditure_purpose, None, None, None, datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), None, datum.get('donor_cmte_name'), None, None, None, None, None, None, child_transaction_type_identifier)
                    child_SA_transaction_id = get_child_transaction_schedA(
                        datum.get("cmte_id"), datum.get("report_id"), transaction_id
                    )
                    if child_SA_transaction_id is not None:
                        delete_sql_schedA(
                            child_SA_transaction_id,
                            datum.get("report_id"),
                            datum.get("cmte_id"),
                        )
                elif (
                    datum.get("transaction_type_identifier")
                    in AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT
                ):
                    child_datum = copy.deepcopy(datum)
                    child_datum[
                        "transaction_type_identifier"
                    ] = AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT.get(
                        datum.get("transaction_type_identifier")
                    )
                    child_datum["line_number"], child_datum[
                        "transaction_type"
                    ] = get_line_number_trans_type(
                        child_datum.get("transaction_type_identifier")
                    )
                    child_datum["back_ref_transaction_id"] = transaction_id
                    child_datum["purpose_description"] = "In-Kind #" + transaction_id
                    child_transaction_id = get_child_transaction_schedA(
                        datum.get("cmte_id"), datum.get("report_id"), transaction_id
                    )
                    if child_transaction_id is None:
                        child_data = post_schedA(child_datum)
                        # child_transaction_id = get_next_transaction_id("SB")
                        # post_sql_schedB(datum.get('cmte_id'), datum.get('report_id'), child_line_number, child_transaction_type, child_transaction_id, transaction_id, datum.get('back_ref_sched_name'), entity_id, datum.get('contribution_date'), datum.get('contribution_amount'), '0.00', expenditure_purpose, None, None, None, datum.get('election_code'), datum.get('election_other_description'), datum.get('donor_cmte_id'), None, datum.get('donor_cmte_name'), None, None, None, None, None, None, child_transaction_type_identifier)
                    else:
                        child_datum["transaction_id"] = child_transaction_id
                        put_sql_schedA(
                            child_datum.get("cmte_id"),
                            child_datum.get("report_id"),
                            child_datum.get("line_number"),
                            child_datum.get("transaction_type"),
                            child_datum.get("transaction_id"),
                            child_datum.get("back_ref_transaction_id"),
                            child_datum.get("back_ref_sched_name"),
                            entity_id,
                            child_datum.get("contribution_date"),
                            child_datum.get("contribution_amount"),
                            child_datum.get("purpose_description"),
                            child_datum.get("memo_code"),
                            child_datum.get("memo_text"),
                            child_datum.get("election_code"),
                            child_datum.get("election_other_description"),
                            child_datum.get("donor_cmte_id"),
                            child_datum.get("donor_cmte_name"),
                            child_datum.get("levin_account_id"),
                            child_datum.get("transaction_type_identifier"),
                        )
                    child_SB_transaction_id = get_child_transaction_schedB(
                        datum.get("cmte_id"), datum.get("report_id"), transaction_id
                    )
                    if child_SB_transaction_id is not None:
                        delete_sql_schedB(
                            child_SB_transaction_id,
                            datum.get("report_id"),
                            datum.get("cmte_id"),
                        )
                elif (
                    datum.get("transaction_type_identifier")
                    in TWO_TRANSACTIONS_ONE_SCREEN_SA_SA_TRANSTYPE_DICT
                ):
                    child_datum = child_SA_to_parent_schedA_dict(datum)
                    check_mandatory_fields_SA(datum, MANDATORY_CHILD_FIELDS_SCHED_A)
                    child_transaction_id = get_child_transaction_schedA(
                        datum.get("cmte_id"), datum.get("report_id"), transaction_id
                    )
                    if child_transaction_id is None:
                        child_data = post_schedA(child_datum)
                    else:
                        child_datum["transaction_id"] = child_transaction_id
                        child_data = put_schedA(child_datum)
                    # TODO: not sure why we need to delete a sched_b item here?
                    child_SB_transaction_id = get_child_transaction_schedB(
                        datum.get("cmte_id"), datum.get("report_id"), transaction_id
                    )
                    if child_SB_transaction_id is not None:
                        delete_sql_schedB(
                            child_SB_transaction_id,
                            datum.get("report_id"),
                            datum.get("cmte_id"),
                        )
                elif (
                    datum.get("transaction_type_identifier")
                    in TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT
                ):
                    if not "child_datum" in datum:
                        raise Exception("child data missing!!!")
                    child_datum = datum.get("child_datum")
                    # update some filds and ensure the parent-child relationaship
                    child_datum["cmte_id"] = datum.get("cmte_id")
                    child_datum["report_id"] = datum.get("report_id")
                    child_datum[
                        "transaction_type_identifier"
                    ] = TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT.get(
                        datum.get("transaction_type_identifier")
                    )
                    child_datum["line_number"], child_datum[
                        "transaction_type"
                    ] = get_line_number_trans_type(
                        child_datum.get("transaction_type_identifier")
                    )
                    child_datum["back_ref_transaction_id"] = transaction_id
                    if not "transaction_id" in child_datum:
                        child_SB_transaction_id = get_child_transaction_schedB(
                            datum.get("cmte_id"), datum.get("report_id"), transaction_id
                        )
                        if not child_SB_transaction_id:
                            child_data = post_schedB(child_datum)
                        else:
                            child_datum["transaction_id"] = child_SB_transaction_id
                            child_data = put_schedB(child_datum)
                    else:
                        child_data = put_schedB(child_datum)
                elif (
                    datum.get("transaction_type_identifier")
                    in CHILD_SCHEDA_AUTO_UPDATE_PARENT_SCHEDA_DICT
                ):
                    child_datum = copy.deepcopy(datum)
                    child_datum["transaction_id"] = child_datum.get(
                        "back_ref_transaction_id"
                    )
                    transaction_data = get_schedA(child_datum)[0]
                    transaction_data["entity_id"] = entity_id
                    transaction_data["contribution_date"] = child_datum.get(
                        "contribution_date"
                    )
                    transaction_data["contribution_amount"] = child_datum.get(
                        "contribution_amount"
                    )
                    transaction_data["election_code"] = child_datum.get("election_code")
                    transaction_data["election_other_description"] = child_datum.get(
                        "election_other_description"
                    )
                    transaction_data["donor_cmte_id"] = child_datum.get("donor_cmte_id")
                    transaction_data["donor_cmte_name"] = child_datum.get(
                        "donor_cmte_name"
                    )
                    put_sql_schedA(
                        transaction_data.get("cmte_id"),
                        transaction_data.get("report_id"),
                        transaction_data.get("line_number"),
                        transaction_data.get("transaction_type"),
                        transaction_data.get("transaction_id"),
                        transaction_data.get("back_ref_transaction_id"),
                        transaction_data.get("back_ref_sched_name"),
                        entity_id,
                        transaction_data.get("contribution_date"),
                        transaction_data.get("contribution_amount"),
                        transaction_data.get("purpose_description"),
                        transaction_data.get("memo_code"),
                        transaction_data.get("memo_text"),
                        transaction_data.get("election_code"),
                        transaction_data.get("election_other_description"),
                        transaction_data.get("donor_cmte_id"),
                        transaction_data.get("donor_cmte_name"),
                        transaction_data.get("levin_account_id"),
                        transaction_data.get("transaction_type_identifier"),
                    )
            except:
                put_sql_schedA(
                    prev_transaction_data.get("cmte_id"),
                    prev_transaction_data.get("report_id"),
                    prev_transaction_data.get("line_number"),
                    prev_transaction_data.get("transaction_type"),
                    transaction_id,
                    prev_transaction_data.get("back_ref_transaction_id"),
                    prev_transaction_data.get("back_ref_sched_name"),
                    entity_id,
                    prev_transaction_data.get("contribution_date"),
                    prev_transaction_data.get("contribution_amount"),
                    prev_transaction_data.get("purpose_description"),
                    prev_transaction_data.get("memo_code"),
                    prev_transaction_data.get("memo_text"),
                    prev_transaction_data.get("election_code"),
                    prev_transaction_data.get("election_other_description"),
                    prev_transaction_data.get("donor_cmte_id"),
                    prev_transaction_data.get("donor_cmte_name"),
                    prev_transaction_data.get("levin_account_id"),
                    prev_transaction_data.get("transaction_type_identifier"),
                )
                raise
        except Exception as e:
            if entity_flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": datum.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The put_sql_schedA function is throwing an error: " + str(e)
            )

        # update line number based on aggregate amount info
        update_date = datetime.datetime.strptime(
            prev_transaction_data.get("contribution_date"), "%Y-%m-%d"
        ).date()
        if update_date > datum.get("contribution_date"):
            update_date = datum.get("contribution_date")

        if transaction_id.startswith("SA"):
            update_linenumber_aggamt_transactions_SA(
                update_date,
                datum.get("transaction_type_identifier"),
                entity_id,
                datum.get("cmte_id"),
                datum.get("report_id"),
            )
        if datum.get("transaction_type_identifier") in SCHED_L_A_TRAN_TYPES:
            update_aggregate_sl(datum)
            update_sl_summary(datum)
        return datum
    except:
        raise


def delete_schedA(data):
    """delete sched_a item and update all associcated items
    """
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        transaction_id = check_transaction_id(data.get("transaction_id"))
        datum = get_list_schedA(report_id, cmte_id, transaction_id)[0]
        delete_sql_schedA(transaction_id, report_id, cmte_id)
        update_linenumber_aggamt_transactions_SA(
            datetime.datetime.strptime(
                datum.get("contribution_date"), "%Y-%m-%d"
            ).date(),
            datum.get("transaction_type_identifier"),
            datum.get("entity_id"),
            datum.get("cmte_id"),
            datum.get("report_id"),
        )
    except:
        raise


def remove_schedA(data):
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        transaction_id = check_transaction_id(data.get("transaction_id"))
        remove_sql_schedA(transaction_id, report_id, cmte_id)
    except:
        raise


# TODO: refactor this function
# something like: if isinstance(data, collections.Iterable):


def check_type_list(data):
    try:
        if not type(data) is list:
            raise Exception(
                "The child transactions have to be sent in as an array or list. Input received: {}".format(
                    data
                )
            )
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
            "transaction_type_identifier": data.get("transaction_type_identifier"),
            "back_ref_sched_name": data.get("back_ref_sched_name"),
            "contribution_date": date_format(data.get("contribution_date")),
            "contribution_amount": check_decimal(data.get("contribution_amount")),
            "purpose_description": data.get("purpose_description"),
            "memo_code": data.get("memo_code"),
            "memo_text": data.get("memo_text"),
            "election_code": data.get("election_code"),
            "election_other_description": data.get("election_other_description"),
            "entity_type": data.get("entity_type"),
            "entity_name": data.get("entity_name"),
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "middle_name": data.get("middle_name"),
            "preffix": data.get("prefix"),
            "suffix": data.get("suffix"),
            "street_1": data.get("street_1"),
            "street_2": data.get("street_2"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip_code": data.get("zip_code"),
            "occupation": data.get("occupation"),
            "employer": data.get("employer"),
            "ref_cand_cmte_id": data.get("ref_cand_cmte_id"),
            "back_ref_transaction_id": data.get("back_ref_transaction_id"),
            "donor_cmte_id": data.get("donor_cmte_id"),
            "levin_account_id": data.get("levin_account_id"),
            "donor_cmte_name": data.get("donor_cmte_name"),
        }
        if "entity_id" in data and check_null_value(data.get("entity_id")):
            datum["entity_id"] = data.get("entity_id")
        datum["line_number"], datum["transaction_type"] = get_line_number_trans_type(
            data.get("transaction_type_identifier")
        )

        if (
            data.get("transaction_type_identifier")
            in TWO_TRANSACTIONS_ONE_SCREEN_SA_SA_TRANSTYPE_DICT.keys()
        ):

            child_datum = {
                "child_transaction_type_identifier": TWO_TRANSACTIONS_ONE_SCREEN_SA_SA_TRANSTYPE_DICT.get(
                    data.get("transaction_type_identifier")
                ),
                "child_back_ref_sched_name": data.get("child*back_ref_sched_name"),
                "child_contribution_date": data.get("child*contribution_date"),
                "child_contribution_amount": data.get("child*contribution_amount"),
                "child_purpose_description": data.get("child*purpose_description"),
                "child_memo_code": data.get("child*memo_code"),
                "child_memo_text": data.get("child*memo_text"),
                "child_election_code": data.get("election_code"),
                "child_election_other_description": data.get(
                    "election_other_description"
                ),
                "child_entity_type": data.get("child*entity_type"),
                "child_entity_name": data.get("child*entity_name"),
                "child_first_name": data.get("child*first_name"),
                "child_last_name": data.get("child*last_name"),
                "child_middle_name": data.get("child*middle_name"),
                "child_preffix": data.get("child*prefix"),
                "child_suffix": data.get("child*suffix"),
                "child_street_1": data.get("child*street_1"),
                "child_street_2": data.get("child*street_2"),
                "child_city": data.get("child*city"),
                "child_state": data.get("child*state"),
                "child_zip_code": data.get("child*zip_code"),
                "child_occupation": data.get("child*occupation"),
                "child_employer": data.get("child*employer"),
                "child_ref_cand_cmte_id": data.get("child*ref_cand_cmte_id"),
                "child_donor_cmte_id": data.get("child*donor_cmte_id"),
                "child_donor_cmte_name": data.get("child*donor_cmte_name"),
            }
            if "child*entity_id" in data and check_null_value(
                data.get("child*entity_id")
            ):
                child_datum["child_entity_id"] = data.get("child*entity_id")
            child_datum["child_line_number"], child_datum[
                "child_transaction_type"
            ] = get_line_number_trans_type(
                child_datum.get("child_transaction_type_identifier")
            )
            datum = {**datum, **child_datum}

        if (
            data.get("transaction_type_identifier")
            in TWO_TRANSACTIONS_ONE_SCREEN_SA_SB_TRANSTYPE_DICT
        ):
            child_datum = {
                k.split("*")[1]: v for k, v in data.items() if k.startswith("child")
            }
            datum["child_datum"] = child_datum

        return datum
    except:
        raise


def child_SA_to_parent_schedA_dict(data):
    try:
        datum = {
            "report_id": data.get("report_id"),
            "cmte_id": data.get("cmte_id"),
            "transaction_type_identifier": data.get(
                "child_transaction_type_identifier"
            ),
            "back_ref_sched_name": data.get("child_back_ref_sched_name"),
            "contribution_date": date_format(data.get("child_contribution_date")),
            "contribution_amount": check_decimal(data.get("child_contribution_amount")),
            "purpose_description": data.get("child_purpose_description"),
            "memo_code": data.get("child_memo_code"),
            "memo_text": data.get("child_memo_text"),
            "election_code": data.get("child_election_code"),
            "election_other_description": data.get("child_election_other_description"),
            "entity_type": data.get("child_entity_type"),
            "entity_name": data.get("child_entity_name"),
            "first_name": data.get("child_first_name"),
            "last_name": data.get("child_last_name"),
            "middle_name": data.get("child_middle_name"),
            "preffix": data.get("child_preffix"),
            "suffix": data.get("child_suffix"),
            "street_1": data.get("child_street_1"),
            "street_2": data.get("child_street_2"),
            "city": data.get("child_city"),
            "state": data.get("child_state"),
            "zip_code": data.get("child_zip_code"),
            "occupation": data.get("child_occupation"),
            "employer": data.get("child_employer"),
            "ref_cand_cmte_id": data.get("child_ref_cand_cmte_id"),
            "donor_cmte_id": data.get("child_donor_cmte_id"),
            "donor_cmte_name": data.get("child_donor_cmte_name"),
            "line_number": data.get("child_line_number"),
            "transaction_type": data.get("child_transaction_type"),
            "back_ref_transaction_id": data.get("transaction_id"),
        }
        if "child_entity_id" in data and check_null_value(data.get("child_entity_id")):
            datum["entity_id"] = data.get("child_entity_id")

        return datum
    except:
        raise


def AUTO_parent_SA_to_child_SB_dict(data):
    try:
        datum = {
            "report_id": data.get("report_id"),
            "cmte_id": data.get("cmte_id"),
            "transaction_type_identifier": AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.get(
                data.get("transaction_type_identifier")
            ),
            "back_ref_sched_name": data.get("back_ref_sched_name"),
            "expenditure_date": data.get("contribution_date"),
            "expenditure_amount": check_decimal(data.get("contribution_amount")),
            "semi_annual_refund_bundled_amount": check_decimal(
                data.get("semi_annual_refund_bundled_amount", "0.0")
            ),
            "category_code": None,
            "memo_code": data.get("memo_code"),
            "memo_text": data.get("memo_text"),
            "election_code": data.get("election_code"),
            "election_other_description": data.get("election_other_description"),
            "beneficiary_cmte_id": data.get("donor_cmte_id"),
            "beneficiary_cand_id": None,
            "other_name": data.get("donor_cmte_name"),
            "other_street_1": None,
            "other_street_2": None,
            "other_city": None,
            "other_state": None,
            "other_zip": None,
            "nc_soft_account": None,
            "entity_type": data.get("entity_type"),
            "entity_name": data.get("entity_name"),
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "middle_name": data.get("middle_name"),
            "preffix": data.get("preffix"),
            "suffix": data.get("suffix"),
            "street_1": data.get("street_1"),
            "street_2": data.get("street_2"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip_code": data.get("zip_code"),
            "occupation": data.get("occupation"),
            "employer": data.get("employer"),
            "ref_cand_cmte_id": data.get("ref_cand_cmte_id"),
            "back_ref_transaction_id": data.get("transaction_id"),
            "entity_id": data.get("entity_id"),
        }
        datum["line_number"], datum["transaction_type"] = get_line_number_trans_type(
            datum.get("transaction_type_identifier")
        )

        return datum
    except:
        raise


def get_child_transaction_schedB(cmte_id, report_id, back_ref_transaction_id):
    """
    load child sched_b transaction_id
    """
    try:
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:
            query_string = """SELECT transaction_id FROM public.sched_b WHERE report_id in ('{}') AND cmte_id = %s AND back_ref_transaction_id = %s AND 
            delete_ind is distinct from 'Y'""".format(
                "', '".join(report_list)
            )
            cursor.execute(query_string, [cmte_id, back_ref_transaction_id])
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
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:
            query_string = """SELECT transaction_id FROM public.sched_a WHERE report_id in ('{}') AND cmte_id = %s AND back_ref_transaction_id = %s AND 
            delete_ind is distinct from 'Y'""".format(
                "', '".join(report_list)
            )
            cursor.execute(query_string, [cmte_id, back_ref_transaction_id])
            if cursor.rowcount == 0:
                return None
            else:
                return cursor.fetchone()[0]
    except:
        raise

def reattribution_auto_generate_transactions(cmte_id, report_id, transaction_id, contribution_date, contribution_amount, back_ref_transaction_id):

    """ This function auto generates 2 copies of the transaction_id in the report_id. One will be an exact copy 
    of the transaction_id and other will have modifications to contribution date and amount. Kindly check FNE-1878
    ticket for the business rules that apply to reattribution"""
    try:
        query_string_1 = """INSERT INTO public.sched_a(
        cmte_id, report_id, line_number, transaction_type, 
        back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, 
        contribution_amount, purpose_description, memo_code, memo_text, 
        election_code, election_other_description, delete_ind, create_date, 
        last_update_date, donor_cmte_id, donor_cmte_name, 
        transaction_type_identifier, election_year, itemized_ind, levin_account_id)
            SELECT cmte_id, %s, line_number, transaction_type, 
               %s, null, entity_id, contribution_date, 
               contribution_amount, purpose_description, 'X', 
               concat('MEMO: Originally reported ',to_char(contribution_date, 'MM/DD/YYYY'),'. $', %s::text, ' reattributed below'), 
               election_code, election_other_description, delete_ind, create_date, 
               last_update_date, donor_cmte_id, donor_cmte_name, 
               transaction_type_identifier, election_year, itemized_ind, levin_account_id
          FROM public.sched_a WHERE transaction_id= %s and cmte_id= %s;"""

        query_string_2 = """INSERT INTO public.sched_a(
        cmte_id, report_id, line_number, transaction_type, 
        back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, 
        contribution_amount, purpose_description, memo_code, memo_text, 
        election_code, election_other_description, delete_ind, create_date, 
        last_update_date, donor_cmte_id, donor_cmte_name, 
        transaction_type_identifier, election_year, itemized_ind, levin_account_id)
            SELECT cmte_id, %s, line_number, transaction_type, 
               %s, null, entity_id, %s, 
               %s, purpose_description, 'X', 'MEMO: Reattribution Below', 
               election_code, election_other_description, delete_ind, create_date, 
               last_update_date, donor_cmte_id, donor_cmte_name, 
               transaction_type_identifier, election_year, itemized_ind, levin_account_id
          FROM public.sched_a WHERE transaction_id= %s and cmte_id= %s;"""

        with connection.cursor() as cursor:
            cursor.execute(query_string_1, [report_id, back_ref_transaction_id, contribution_amount, transaction_id, cmte_id])
            if cursor.rowcount == 0:
                raise Exception('The transaction ID: {} does not exist in sched_a for committee ID: {}'.format(transaction_id, cmte_id))
            cursor.execute(query_string_2, [report_id, back_ref_transaction_id, contribution_date, -1*Decimal(contribution_amount), transaction_id, cmte_id])
    except Exception as e:
        raise Exception('The reattribution_auto_generate_transactions function is throwing an error: ' + str(e))

def reattribution_auto_update_transactions(cmte_id, report_id, contribution_date, contribution_amount, back_ref_transaction_id):
    try:
        query_string = """UPDATE public.sched_a SET report_id = %s
        WHERE transaction_id = %s AND cmte_id = %s;"""

        query_string_s1 = """UPDATE public.sched_a SET report_id = %s, memo_text = %s
        WHERE back_ref_transaction_id = %s AND cmte_id = %s AND memo_text LIKE %s"""

        query_string_s2 = """UPDATE public.sched_a SET report_id = %s, contribution_date = %s, contribution_amount = %s
        WHERE back_ref_transaction_id = %s AND cmte_id = %s AND memo_text NOT LIKE %s"""

        with connection.cursor() as cursor:
            cursor.execute(query_string, [report_id, back_ref_transaction_id, cmte_id])
            if cursor.rowcount == 0:
                raise Exception('The transaction ID: {} does not exist in sched_a for committee ID: {}'.format(back_ref_transaction_id, cmte_id))
        with connection.cursor() as cursor:
            memo_text = 'MEMO: Originally reported ' + contribution_date.strftime("%m/%d/%Y") + '. $' + contribution_amount + ' reattributed below'
            cursor.execute(query_string_s1, [report_id, memo_text, back_ref_transaction_id, cmte_id, '%Originally%'])
            if cursor.rowcount == 0:
                raise Exception('The back ref transaction ID: {} does not exist in sched_a for committee ID: {}'.format(back_ref_transaction_id, cmte_id))
        with connection.cursor() as cursor:
            cursor.execute(query_string_s2, [report_id, contribution_date, -1*Decimal(contribution_amount), 
                back_ref_transaction_id, cmte_id, '%Originally%'])
    except Exception as e:
        raise Exception('The reattribution_auto_update_transactions function is throwing an error: ' + str(e))

"""
***************************************************** SCHED A - POST API CALL STARTS HERE **********************************************************
"""


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedA(request):
    """
    sched_a api supporting POST, GET, DELETE, PUT
    """

    # POST api: create new transactions and children transactions if any
    global REQ_ELECTION_YR
    if request.method == "POST":
        if "election_year" in request.data:
            REQ_ELECTION_YR = request.data.get("election_year")
        if "election_year" in request.query_params:
            REQ_ELECTION_YR = request.query_params.get("election_year")
        try:
            # checking if reattribution is triggered for a transaction
            reattribution_flag = False
            if "reattribution_id" in request.data and request.data[
                "reattribution_id"
            ] not in ["", "", None, "null"]:
                reattribution_flag = True
                if 'reattribution_report_id' not in request.data:
                    raise Exception('reattribution_report_id parameter is missing. Kindly provide this id to continue reattribution')
            validate_sa_data(request.data)
            cmte_id = request.user.username
            report_id = check_report_id(request.data.get("report_id"))
            # To check if the report id exists in reports table
            form_type = find_form_type(report_id, cmte_id)
            datum = schedA_sql_dict(request.data)
            datum["report_id"] = report_id
            datum["cmte_id"] = cmte_id
            # Adding memo_code and memo_text values for reattribution flags
            if reattribution_flag:
                datum['memo_code'] = 'X'
                datum['memo_text'] = 'MEMO: Reattribution'
                datum['report_id'] = check_report_id(request.data['reattribution_report_id'])
            # posting data into schedA
            data = post_schedA(datum)
            # Auto generation of reattribution transactions
            if reattribution_flag:
                reattribution_auto_generate_transactions(
                    cmte_id,
                    datum['report_id'],
                    request.data["reattribution_id"],
                    datum["contribution_date"],
                    datum["contribution_amount"],
                    data['transaction_id']
                )
            output = get_schedA(data)
            # for earmark child transaction: update parent transction  purpose_description
            if datum.get("transaction_type_identifier") in EARMARK_SA_CHILD_LIST:
                update_earmark_parent_purpose(datum)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                "The schedA API - POST is throwing an exception: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Get records from schedA table
    if request.method == "GET":
        if "election_year" in request.data:
            REQ_ELECTION_YR = request.data.get("election_year")
        if "election_year" in request.query_params:
            REQ_ELECTION_YR = request.query_params.get("election_year")

        try:
            data = {"cmte_id": request.user.username}
            if "report_id" in request.query_params and check_null_value(
                request.query_params.get("report_id")
            ):
                data["report_id"] = check_report_id(
                    request.query_params.get("report_id")
                )
            else:
                raise Exception("Missing Input: report_id is mandatory")
            # To check if the report id exists in reports table
            form_type = find_form_type(data.get("report_id"), data.get("cmte_id"))
            if "transaction_id" in request.query_params and check_null_value(
                request.query_params.get("transaction_id")
            ):
                data["transaction_id"] = check_transaction_id(
                    request.query_params.get("transaction_id")
                )
            datum = get_schedA(data)
            # # for obj in datum:
            #     obj.update({'api_call' : 'sa/schedA'})
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(
                forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False
            )
        except Exception as e:
            logger.debug(e)
            return Response(
                "The schedA API - GET is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    # PUT api call handled here
    if request.method == "PUT":
        if "election_year" in request.data:
            REQ_ELECTION_YR = request.data.get("election_year")
        if "election_year" in request.query_params:
            REQ_ELECTION_YR = request.query_params.get("election_year")
        try:
            # checking if reattribution is triggered for a transaction
            reattribution_flag = False
            if 'isReattribution' in request.data and request.data['isReattribution'] not in ['None', 'null', '', ""]:
                if request.data['isReattribution'] in ['True', 'true', 't', 'T', True]:
                    reattribution_flag = True
                    if 'reattribution_report_id' not in request.data:
                        raise Exception('reattribution_report_id parameter is missing. Kindly provide this id to continue reattribution')
                    else:
                        reattribution_report_id = check_report_id(request.data['reattribution_report_id'])
            validate_sa_data(request.data)
            datum = schedA_sql_dict(request.data)
            if "transaction_id" in request.data and check_null_value(
                request.data.get("transaction_id")
            ):
                datum["transaction_id"] = request.data.get("transaction_id")
            else:
                raise Exception("Missing Input: transaction_id is mandatory")
            # handling null,none value of report_id
            if not (check_null_value(request.data.get("report_id"))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get("report_id"))
            # end of handling
            datum["report_id"] = report_id
            datum["cmte_id"] = request.user.username
            # To check if the report id exists in reports table
            form_type = find_form_type(report_id, datum.get('cmte_id'))
            # updating data for reattribution fields
            if reattribution_flag:
                datum['memo_code'] = 'X'
                datum['memo_text'] = 'MEMO: Reattribution'
            data = put_schedA(datum)
            # Updating auto generated transactions for reattribution transactions
            if reattribution_flag:
                reattribution_auto_update_transactions(datum['cmte_id'], 
                    reattribution_report_id,
                    datum['contribution_date'], datum['contribution_amount'], datum['transaction_id'])
                data['report_id'] = reattribution_report_id
            output = get_schedA(data)

            # for earmark child transaction: update parent transction  purpose_description
            if datum.get("transaction_type_identifier") in EARMARK_SA_CHILD_LIST:
                update_earmark_parent_purpose(datum)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                "The schedA API - PUT is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    # delete api call handled here
    if request.method == "DELETE":
        if "election_year" in request.data:
            REQ_ELECTION_YR = request.data.get("election_year")
        if "election_year" in request.query_params:
            REQ_ELECTION_YR = request.query_params.get("election_year")

        try:
            data = {"cmte_id": request.user.username}
            if "report_id" in request.query_params and check_null_value(
                request.query_params.get("report_id")
            ):
                data["report_id"] = check_report_id(
                    request.query_params.get("report_id")
                )
            else:
                raise Exception("Missing Input: report_id is mandatory")
            # To check if the report id exists in reports table
            form_type = find_form_type(data.get("report_id"), data.get("cmte_id"))
            if "transaction_id" in request.query_params and check_null_value(
                request.query_params.get("transaction_id")
            ):
                data["transaction_id"] = check_transaction_id(
                    request.query_params.get("transaction_id")
                )
            else:
                raise Exception("Missing Input: transaction_id is mandatory")
            delete_schedA(data)
            return Response(
                "The Transaction ID: {} has been successfully deleted".format(
                    data.get("transaction_id")
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                "The schedA API - DELETE is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )


@api_view(["GET"])
def contribution_aggregate(request):
    """
    contribution_aggregate api with GET request
    """
    if request.method == "GET":
        try:
            check_mandatory_fields_SA(request.query_params, MANDATORY_FIELDS_AGGREGATE)
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
            transaction_type_identifier = request.query_params.get(
                "transaction_type_identifier"
            )
            contribution_date = date_format(
                request.query_params.get("contribution_date")
            )
            if "entity_id" in request.query_params and check_null_value(
                request.query_params.get("entity_id")
            ):
                entity_id = request.query_params.get("entity_id")
            else:
                entity_id = "0"
            if "contribution_amount" in request.query_params and check_null_value(
                request.query_params.get("contribution_amount")
            ):
                contribution_amount = check_decimal(
                    request.query_params.get("contribution_amount")
                )
            else:
                contribution_amount = "0"
            # form_type = find_form_type(report_id, cmte_id)
            # aggregate_start_date, aggregate_end_date = find_aggregate_date(form_type, aggregate_date)
            aggregate_amt = func_aggregate_amount(
                contribution_date, transaction_type_identifier, entity_id, cmte_id
            )
            total_amt = aggregate_amt + Decimal(contribution_amount)
            return JsonResponse(
                {"contribution_aggregate": total_amt}, status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                "The contribution_aggregate API is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )


def report_end_date(report_id, cmte_id):
    """
    query report end date
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT cvg_end_date FROM public.reports WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct FROM 'Y'""",
                [report_id, cmte_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "The Report ID: {} does not exist in reports table".format(
                        report_id
                    )
                )
            cvg_end_date = cursor.fetchone()[0]
        return cvg_end_date
    except Exception as e:
        raise Exception("The report_end_date function is throwing an error: " + str(e))


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


def update_parent_amounts_to_trash(
    transaction_amount, transaction_id, cmte_id, _delete
):
    """FUNCTION TO HANDLE SC SD PARENT AMOUNT UPDATES WHEN SA,SB,SE,SF,SH PAYMENTS ARE DELETED OR RESTORED"""
    try:
        dict_map = {
            "SC": ["loan_payment_to_date", "loan_balance"],
            "SD": ["payment_amount", "balance_at_close"],
        }
        table_map = {"SC": "sched_c", "SD": "sched_d"}
        """Mapping variable"""
        if transaction_id[:2] in dict_map:
            query_list = dict_map[transaction_id[:2]]
        else:
            raise Exception(
                "The update_parent_amounts_to_trash function works only for Sched_C and Sched_D transactions."
            )
        """Mapping signs"""
        if _delete == "Y":
            query_list.append("-")
            query_list.append("+")
        else:
            query_list.append("+")
            query_list.append("-")

        """Mapping value"""
        query_list.append(str(transaction_amount))
        print(query_list)

        query_string = """
            {0} = {0} {2} {4},
            {1} = {1} {3} {4},
        """.format(
            query_list[0], query_list[1], query_list[2], query_list[3], query_list[4]
        )

        _sql = """UPDATE public.{0}
                SET {1}
                last_update_date = %s
                WHERE transaction_id = %s
                AND cmte_id = %s
                """.format(
            table_map[transaction_id[:2]], query_string
        )
        with connection.cursor() as cursor:
            cursor.execute(_sql, [datetime.datetime.now(), transaction_id, cmte_id])
            print(cursor.query)
            if cursor.rowcount < 1:
                raise Exception(
                    "There is no transaction associcated with the transaction_id: "
                    + transaction_id
                )
    except Exception:
        raise


def get_child_transactions_to_trash(transaction_id, _delete):
    """ Get a list of all child transactions specifically for schedule C,D that should be deleted when a schedule C or D transaction is deleted"""
    try:
        if _delete == "Y":
            action = "trash"
            # Trashing only undeleted transactions
            param_string = """ AND delete_ind IS DISTINCT FROM 'Y' """
        else:
            action = "restore"
            # Restoring only auto generated transactions
            param_string = """ AND transaction_type_identifier IN ('LOAN_FROM_IND', 'LOAN_FROM_BANK', 'LOAN_OWN_TO_CMTE_OUT', 'SC1',
            'IK_OUT','IK_BC_OUT','PARTY_IK_OUT','PARTY_IK_BC_OUT','PAC_IK_OUT','PAC_IK_BC_OUT','IK_TRAN_OUT','IK_TRAN_FEA_OUT')"""

        _sql = """SELECT report_id, transaction_id, '{}' AS action
                FROM public.all_transactions_view
                WHERE back_ref_transaction_id = %s""".format(
            action
        )
        with connection.cursor() as cursor:
            _query = """SELECT json_agg(t) FROM ({}) as t""".format(_sql + param_string)
            cursor.execute(_query, [transaction_id])
            logger.debug(cursor.query)
            forms_obj = cursor.fetchone()

        if forms_obj and forms_obj[0]:
            return forms_obj[0]
        else:
            return []

    except Exception as e:
        raise Exception(
            "The get_child_transactions function is throwing an error:" + str(e)
        )


def trash_restore_sql_transaction(table_list, report_id, transaction_id, _delete="Y"):
    """trash or restore transactions which handles all transactions across all tables"""
    try:
        report_list = superceded_report_id_list(report_id)
        row_count = 0
        for table in table_list:
            with connection.cursor() as cursor:
                # UPDATE delete_ind flag to Y in DB
                _sql = """
                UPDATE public.{} 
                SET delete_ind = '{}', last_update_date = %s
                WHERE report_id in ('{}')
                        AND transaction_id = '{}'
                """.format(
                    table, _delete, "', '".join(report_list), transaction_id
                )
                cursor.execute(_sql, [datetime.datetime.now()])
                logger.debug(cursor.query)
                row_count += cursor.rowcount
        if not row_count:
            raise Exception(
                """The transaction ID: {1} is either already deleted
                 or does not exist in {0} table""".format(
                    ",".join(table_list), transaction_id
                )
            )
        else:
            return transaction_id
    except Exception:
        raise


def get_backref_id_trash(transaction_id, cmte_id):
    """ function to grab parent transaction id and amount so that we can update parent amounts in SC and SD"""
    try:
        _sql = """SELECT back_ref_transaction_id, transaction_amount
                    FROM public.all_transactions_view
                    WHERE transaction_id=%s AND cmte_id=%s AND
                    transaction_type_identifier NOT IN ('LOAN_FROM_IND', 'LOAN_FROM_BANK', 'LOAN_OWN_TO_CMTE_OUT');
                    """
        with connection.cursor() as cursor:
            cursor.execute(_sql, [transaction_id, cmte_id])
            if cursor.rowcount > 0:
                forms_obj = cursor.fetchone()
                return forms_obj[0], forms_obj[1]
            else:
                return None, None
    except Exception:
        raise


def delete_H1_carry_over(transaction_id, cmte_id):
    try:
        _sql = """SELECT atv.transaction_table, (SELECT cm.cmte_type_category FROM public.committee_master cm WHERE cm.cmte_id = %s) 
                FROM public.all_transactions_view atv 
                WHERE atv.transaction_id = %s and atv.cmte_id = %s 
               """
        with connection.cursor() as cursor:
            cursor.execute(_sql, [cmte_id, transaction_id, cmte_id])
            forms_obj = cursor.fetchone()
            if forms_obj[0] == "sched_h1":
                if forms_obj[1] == "PTY":
                    _sql1 = """UPDATE public.sched_h1 
                        SET delete_ind = 'Y' 
                        FROM public.sched_h1 ch1
                        WHERE sched_h1.election_year = ch1.election_year 
                        AND ch1.cmte_id = sched_h1.cmte_id
                        AND ch1.transaction_id = %s 
                        AND sched_h1.cmte_id = %s
                        AND sched_h1.delete_ind is distinct from 'Y';
                        """
                if forms_obj[1] == "PAC":
                    _sql1 = """UPDATE public.sched_h1 
                        SET delete_ind = 'Y' 
                        FROM public.sched_h1 ch1
                        WHERE sched_h1.election_year = ch1.election_year 
                        AND ch1.cmte_id = sched_h1.cmte_id
                        AND ch1.administrative = sched_h1.administrative
                        AND ch1.generic_voter_drive = sched_h1.generic_voter_drive
                        AND ch1.public_communications = sched_h1.public_communications
                        AND ch1.transaction_id = %s 
                        AND sched_h1.cmte_id = %s
                        AND sched_h1.delete_ind is distinct from 'Y';
                        """
                cursor.execute(_sql1, [transaction_id, cmte_id])
                print(cursor.query)

    except Exception:
        raise

def get_auto_generated_reattribution_transactions(action, transaction_id, transaction_type_identifier):
    try:
        _sql = """SELECT report_id, transaction_id, '{}' AS action
                FROM public.all_transactions_view
                WHERE back_ref_transaction_id = %s AND transaction_type_identifier = %s""".format(action)
        with connection.cursor() as cursor:
            _query = """SELECT json_agg(t) FROM ({}) as t""".format(_sql)
            cursor.execute(_query, [transaction_id, transaction_type_identifier])
            logger.debug(cursor.query)
            forms_obj = cursor.fetchone()
        if forms_obj and forms_obj[0]:
            return forms_obj[0]
        else:
            return []
    except Exception as e:
        raise Exception('The get_auto_generated_reattribution_transactions function is throwing an error: ' + str(e))
        
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
    deleted_transaction_ids = []
    _actions = request.data.get("actions", [])
    for _action in _actions:
        report_id = _action.get("report_id", "")
        transaction_id = _action.get("transaction_id", "")
        cmte_id = request.user.username

        action = _action.get("action", "")
        _delete = "Y" if action == "trash" else ""
        # get_schedA data, do sql transaction, update aggregation
        # try:
        table_list = SCHEDULE_TO_TABLE_DICT.get(transaction_id[:2])
        if table_list:
            if transaction_id[:2] in ("SA", "LA", "LB", "SB", "SE", "SF", "SH"):
                # Handling deletion/restoration of payments for schedule C and schedule D
                back_ref_transaction_id, transaction_amount = get_backref_id_trash(
                    transaction_id, cmte_id
                )
                if back_ref_transaction_id and back_ref_transaction_id[:2] in (
                    "SC",
                    "SD",
                ):
                    update_parent_amounts_to_trash(
                        transaction_amount, back_ref_transaction_id, cmte_id, _delete
                    )
                # load data and prepare for aggregation and take care parent-child relationship

                tran_data = {}
                if transaction_id[:2] == "SF":
                    tran_data = load_schedF(cmte_id, report_id, transaction_id)[0]
                if transaction_id[:2] == "SE":
                    tran_data = load_schedE(cmte_id, report_id, transaction_id)[0]

                # Deleting/Restoring the transaction
                deleted_transaction_ids.append(
                    trash_restore_sql_transaction(
                        table_list, report_id, transaction_id, _delete
                    )
                )

                # Handling aggregate update for sched_A transactions
                if transaction_id[:2] == "SA":
                    datum = get_list_schedA(report_id, cmte_id, transaction_id, True)[0]
                    update_linenumber_aggamt_transactions_SA(
                        datetime.datetime.strptime(
                            datum.get("contribution_date"), "%Y-%m-%d"
                        ).date(),
                        datum.get("transaction_type_identifier"),
                        datum.get("entity_id"),
                        datum.get("cmte_id"),
                        datum.get("report_id"),
                    )
                    # Deleting/Restoring auto generated transactions for Schedule A
                    if _delete == 'Y' or (_delete != 'Y' and datum.get('transaction_type_identifier') in ['IK_REC','IK_BC_REC','PARTY_IK_REC','PARTY_IK_BC_REC','PAC_IK_REC',
                        'PAC_IK_BC_REC','IK_TRAN','IK_TRAN_FEA']):
                        _actions.extend(get_child_transactions_to_trash(transaction_id, _delete))
                    # Handling Reattribution auto generated transactions
                    if _delete != 'Y' and datum['transaction_type_identifier'] in ['IND_REC_NON_CONT_ACC', 'IND_NP_CONVEN_ACC', 
                        'IND_NP_HQ_ACC', 'IND_NP_RECNT_ACC', 'IND_RECNT_REC', 'INDV_REC', 'JF_TRAN_PAC_MEMO', 
                        'JF_TRAN_IND_MEMO', 'JF_TRAN_PARTY_MEMO', 'JF_TRAN_TRIB_MEMO', 'JF_TRAN_NP_RECNT_IND_MEMO', 
                        'JF_TRAN_NP_RECNT_PAC_MEMO', 'JF_TRAN_NP_RECNT_TRIB_MEMO', 'JF_TRAN_NP_CONVEN_IND_MEMO', 
                        'JF_TRAN_NP_CONVEN_PAC_MEMO', 'JF_TRAN_NP_CONVEN_TRIB_MEMO''JF_TRAN_NP_HQ_IND_MEMO', 
                        'JF_TRAN_NP_HQ_PAC_MEMO', 'JF_TRAN_NP_HQ_TRIB_MEMO']:
                        _actions.extend(get_auto_generated_reattribution_transactions(action, transaction_id, datum['transaction_type_identifier']))
                
                if transaction_id[:2] == 'LA':
                    tran_data = get_list_schedA(report_id, cmte_id, transaction_id, True)[0]
                    logger.debug('update sl aggregate with LA data {}'.format(tran_data))
                    update_aggregate_sl(tran_data)
                    logger.debug("update sl summary with LA data {}".format(tran_data))
                    update_sl_summary(tran_data)

                if transaction_id[:2] == "LB":
                    tran_data = get_sched_b_transactions(
                        report_id, cmte_id, transaction_id=transaction_id
                    )[0]
                    logger.debug("update sl summary with LB data {}".format(tran_data))
                    update_sl_summary(tran_data)

                # Handling delete of sched_B, sched_E, sched_F child transactions
                if transaction_id[:2] in ["SB", "SE", "SF"] and _delete == "Y":
                    _actions.extend(
                        get_child_transactions_to_trash(transaction_id, _delete)
                    )

                if transaction_id[:2] == "SF":
                    update_aggregate_sf(
                        tran_data["cmte_id"],
                        tran_data["beneficiary_cand_id"],
                        datetime.datetime.strptime(
                            tran_data.get("expenditure_date"), "%Y-%m-%d"
                        )
                        .date()
                        .strftime("%m/%d/%Y"),
                    )

                if transaction_id[:2] == "SE":
                    update_aggregate_se(tran_data)

                # Handling delete of schedule H4/H6 transactions: delete child trans and update aggregate
                if transaction_id[:2] == "SH" and _delete == "Y":
                    tran_tbl = get_sched_h_transaction_table(transaction_id)
                    if tran_tbl == "sched_h4":
                        logger.debug(
                            "sched_h4 trash: check child transaction and update ytd amount:"
                        )
                        _actions.extend(
                            get_child_transactions_to_trash(transaction_id, _delete)
                        )
                        data = load_schedH4(cmte_id, report_id, transaction_id)[0]
                        logger.debug(
                            "update sched h4 aggregate amount after trashing {}".format(
                                data
                            )
                        )
                        update_activity_event_amount_ytd_h4(data)
                    if tran_tbl == "sched_h6":
                        logger.debug(
                            "sched_h6 trash: check child transaction and update ytd amount:"
                        )
                        _actions.extend(
                            get_child_transactions_to_trash(transaction_id, _delete)
                        )
                        data = load_schedH6(cmte_id, report_id, transaction_id)[0]
                        logger.debug(
                            "update sched h4 aggregate amount after trashing {}".format(
                                data
                            )
                        )
                        update_activity_event_amount_ytd_h6(data)
            elif transaction_id[:2] in ("SC", "SD"):
                # Handling auto deletion of payments and auto generated transactions for sched_C and sched_D
                if _delete == "Y" or (transaction_id[:2] == "SC" and _delete != "Y"):
                    _actions.extend(
                        get_child_transactions_to_trash(transaction_id, _delete)
                    )
                # Deleting/Restoring the transaction
                deleted_transaction_ids.append(
                    trash_restore_sql_transaction(
                        table_list, report_id, transaction_id, _delete
                    )
                )
            else:
                # Deleting/Restoring the transaction
                deleted_transaction_ids.append(
                    trash_restore_sql_transaction(
                        table_list, report_id, transaction_id, _delete
                    )
                )
        else:
            raise Exception(
                "The transaction id {} has not been assigned to SCHEDULE_TO_TABLE_DICT. Deleted transactions are: {}".format(
                    transaction_id, ",".join(deleted_transaction_ids)
                )
            )

        # update report last_update_date
        renew_report_update_date(report_id)

        # except Exception as e:
        #     return Response("The trash_restore_transactions API is throwing an error: " + str(e) + ". Deleted transactions are: {}".format(",".join(deleted_transaction_ids)),
        #         status=status.HTTP_400_BAD_REQUEST)
    return Response(
        {
            "result": "success",
            "deletedTransactions": "{}".format(",".join(deleted_transaction_ids)),
        },
        status=status.HTTP_200_OK,
    )


"""
******************************************************************************************************************************
END - TRASH RESTORE TRANSACTIONS API - SCHED_A APP (MOVED FROM CORE APP)
******************************************************************************************************************************
"""
"""
******************************************************************************************************************************
API TO GET LATEST OR MOST RECENT AMENDED REPORT ID AND ITS STATUS BASED ON TRANSACTION DATE INPUT
USED IN REATTRIBUTION REPORT ID GENERATION
******************************************************************************************************************************
"""


@api_view(["GET"])
def get_report_id_from_date(request):
    try:
        transaction_date = date_format(request.query_params.get("transaction_date"))
        cmte_id = request.user.username
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (SELECT report_id AS "reportId", CASE WHEN(status IS NULL 
                    OR status::text = 'Saved'::text) THEN 'Saved'
                    ELSE 'Filed' END AS status FROM public.reports WHERE cmte_id=%s AND %s>=cvg_start_date
                    AND %s<=cvg_end_date AND delete_ind IS DISTINCT FROM 'Y' ORDER BY amend_ind ASC, amend_number DESC
                    LIMIT 1) t""",
                [cmte_id, transaction_date, transaction_date],
            )
            result = cursor.fetchone()
        if result and result[0]:
            return Response(result[0][0], status=status.HTTP_200_OK)
        else:
            return Response(
                {"reportId": None, "status": None}, status=status.HTTP_200_OK
            )
    except Exception as e:
        return Response(
            "The get_report_id_from_date API is throwing the following error: " + str(e)
        )


"""
******************************************************************************************************************************
END - get_report_id_from_date API - SCHED_A APP (MOVED FROM CORE APP)
******************************************************************************************************************************
"""
