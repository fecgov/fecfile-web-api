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

from fecfiler.sched_L.views import update_sl_summary

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
    save_cand_entity,
    superceded_report_id_list,
)
from fecfiler.core.transaction_util import (
    get_line_number_trans_type,
    get_sched_b_transactions,
    transaction_exists,
    update_earmark_parent_purpose,
    update_sched_d_parent,
    update_sched_c_parent,
    get_transaction_type_descriptions,
    cmte_type,
)
from fecfiler.core.report_helper import new_report_date

from fecfiler.core.aggregation_helper import (find_form_type, find_aggregate_date,
    update_linenumber_aggamt_transactions_SA)

logger = logging.getLogger(__name__)


# semi_annual_refund_bundled_amount remmoed from ths list but is still needed
# you need to pass in a valid decimal value: this is valid until db change happens
list_mandatory_fields_schedB = [
    "report_id",
    "expenditure_date",
    "expenditure_amount",
    "transaction_type_identifier",
    "entity_type",
]

# a list of transactions with negative transaction_amount
NEGATIVE_TRANSACTIONS = [
    "OPEXP_VOID",
    "CONT_TO_OTH_CMTE_VOID",
    "OTH_DISB_NC_ACC_PMT_TO_PROL_VOID",
    "FEA_100PCT_PAY_VOID",
    "REF_CONT_IND_VOID",
    "REF_CONT_PARTY_VOID",
    "REF_CONT_PAC_VOID",
    "REF_CONT_NON_FED_VOID",
]

# for child transactions, we'll validate parent_id exists in the db
# TODO: later on chagne it to load this list from DB
CHILD_PARENT_SB_SB_TRANSACTIONS = {
    "OTH_DISB_CC_PAY_MEMO": ("OTH_DISB_CC_PAY", "sched_b"),
    "OTH_DISB_STAF_REIM_MEMO": ("OTH_DISB_STAF_REIM", "sched_b"),
    "OTH_DISB_PMT_TO_PROL_MEMO": ("OTH_DISB_PMT_TO_PROL", "sched_b"),
    "OTH_DISB_NC_ACC_CC_PAY_MEMO": ("OTH_DISB_NC_ACC_CC_PAY", "sched_b"),
    "OTH_DISB_NC_ACC_STAF_REIM_MEMO": ("OTH_DISB_NC_ACC_STAF_REIM", "sched_b"),
    "OTH_DISB_NC_ACC_PMT_TO_PROL_MEMO": ("OTH_DISB_NC_ACC_PMT_TO_PROL", "sched_b"),
    "FEA_PAY_TO_PROL_MEMO": ("FEA_PAY_TO_PROL", "sched_b"),
    "FEA_CC_PAY_MEMO": ("FEA_CC_PAY", "sched_b"),
    "FEA_STAF_REIM_MEMO": ("FEA_STAF_REIM", "sched_b"),
    "CONT_REDESIG_MEMO": ("CONT_REDESIG", "sched_b"),
}

CHILD_SCHEDB_AUTO_UPDATE_PARENT_SCHEDA_DICT = {
    "IK_OUT": "IK_REC",
    "IK_BC_OUT": "IK_BC_REC",
    "PARTY_IK_OUT": "PARTY_IK_REC",
    "PARTY_IK_BC_OUT": "PARTY_IK_BC_REC",
    "PAC_IK_OUT": "PAC_IK_REC",
    "PAC_IK_BC_OUT": "PAC_IK_BC_REC",
    "IK_TRAN_OUT": "IK_TRAN",
    "IK_TRAN_FEA_OUT": "IK_TRAN_FEA",
}
EARMARK_SB_CHILD_LIST = [
    "CON_EAR_DEP_MEMO",
    "CON_EAR_UNDEP_MEMO",
    "PAC_CON_EAR_DEP_MEMO",
    "PAC_CON_EAR_UNDEP_MEMO",
]

# a list of treansaction types for sched_l(levin funds report) disbursments
SCHED_L_B_TRAN_TYPES = [
    "LEVIN_VOTER_ID",
    "LEVIN_GOTV",
    "LEVIN_GEN",
    "LEVIN_OTH_DISB",
    "LEVIN_VOTER_REG",
]

SCHED_D_CHILD_LIST = ["OTH_DISB_DEBT", "OPEXP_DEBT"]
SCHED_C_CHILD_LIST = ["LOAN_REPAY_MADE"]

# adding election_year field needed by front end
REQT_ELECTION_YR = ""

ITEMIZED_SB_UPDATE_TRANSACTION_TYPE_IDENTIFIER = [
    "OPEXP",
    "OPEXP_CC_PAY",
    "OPEXP_STAF_REIM",
    "OPEXP_PMT_TO_PROL",
    "OPEXP_VOID",
    "OPEXP_HQ_ACC_OP_EXP_NP",
    "OPEXP_CONV_ACC_OP_EXP_NP",
    "OPEXP_DEBT",
    "OTH_DISB",
    "OTH_DISB_CC_PAY",
    "OTH_DISB_STAF_REIM",
    "OTH_DISB_PMT_TO_PROL",
    "OTH_DISB_RECNT",
    "OTH_DISB_NP_RECNT_ACC",
    "OTH_DISB_NC_ACC",
    "OTH_DISB_NC_ACC_CC_PAY",
    "OTH_DISB_NC_ACC_STAF_REIM",
    "OTH_DISB_NC_ACC_PMT_TO_PROL",
    "OTH_DISB_VOID",
    "REF_CONT_IND",
    "REF_CONT_IND_VOID",
    "FEA_100PCT_PAY",
    "FEA_CC_PAY",
    "FEA_STAF_REIM",
    "FEA_PAY_TO_PROL",
    "FEA_VOID",
    "FEA_100PCT_DEBT_PAY",
]


def date_format_agg(cvg_date):
    try:
        if cvg_date == None or cvg_date in ["none", "null", " ", ""]:
            return None
        cvg_dt = datetime.datetime.strptime(cvg_date, "%Y-%m-%d").date()
        return cvg_dt
    except:
        raise


# To avoid circular reference adding sched_a function
def put_sql_schedA_from_schedB(
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
                election_other_description = %s, donor_cmte_id = %s, donor_cmte_name = %s, transaction_type_identifier = %s, last_update_date = %s 
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
                    transaction_type_identifier,
                    datetime.datetime.now(),
                    transaction_id,
                    report_id,
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



def get_next_transaction_id(trans_char):
    """
    query the db for next transarion id
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT public.get_next_transaction_id(%s)""", [trans_char]
            )
            transaction_ids = cursor.fetchone()
            transaction_id = transaction_ids[0]
        return transaction_id
    except Exception:
        raise


def check_transaction_id(transaction_id):
    """
    make sure transaction_id start with 'SB'
    """
    try:
        transaction_type_list = ["SB", "LB"]
        transaction_type = transaction_id[0:2]
        if not (transaction_type in transaction_type_list):
            raise Exception(
                "The Transaction ID: {} is not in the specified format. Transaction IDs start with SB characters".format(
                    transaction_id
                )
            )
        return transaction_id
    except Exception:
        raise


def check_type_list(data):
    """
    make sure child transaction data is in a list
    """
    try:
        if not type(data) is list:
            raise Exception(
                """
                The child transactions have to be sent in as an array or list. 
                Input received: {}""".format(
                    data
                )

            )
        else:
            return data
    except:
        raise


def check_decimal(value):
    """
    check value is decimal data
    """
    try:
        check_value = Decimal(value)
        return value
    except Exception as e:
        raise Exception(
            """
            Invalid Input: Expecting a decimal value like 18.11, 24.07. 
            Input received: {}""".format(
                value
            )

        )


def check_mandatory_fields_SB(data, list_mandatory_fields):
    """
    verify madatory fields with SB transaction
    """
    try:
        error = []
        for field in list_mandatory_fields:
            if not (field in data and check_null_value(data.get(field))):
                error.append(field)
        if len(error) > 0:
            string = ""
            for x in error:
                string = string + x + ", "
            string = string[0:-2]
            raise Exception(
                """The following mandatory fields are required in order to 
                save data to schedB table: {}""".format(
                    string
                )
            )
    except:
        raise


def post_sql_schedB(
    cmte_id,
    report_id,
    line_number,
    transaction_type,
    transaction_id,
    back_ref_transaction_id,
    back_ref_sched_name,
    entity_id,
    expenditure_date,
    expenditure_amount,
    semi_annual_refund_bundled_amount,
    expenditure_purpose,
    category_code,
    memo_code,
    memo_text,
    election_code,
    election_other_description,
    beneficiary_cmte_id,
    beneficiary_cand_id,
    other_name,
    other_street_1,
    other_street_2,
    other_city,
    other_state,
    other_zip,
    nc_soft_account,
    transaction_type_identifier,
    beneficiary_cand_office,
    beneficiary_cand_state,
    beneficiary_cand_district,
    beneficiary_cmte_name,
    beneficiary_cand_last_name,
    beneficiary_cand_first_name,
    beneficiary_cand_middle_name,
    beneficiary_cand_prefix,
    beneficiary_cand_suffix,
    aggregate_amt,
    beneficiary_cand_entity_id,
    levin_account_id,
    aggregation_ind = None,
):
    """
    db transaction for post a db transaction
    """
    try:
        with connection.cursor() as cursor:
            # Insert data into schedB table
            cursor.execute(
                """INSERT INTO public.sched_b (
                    cmte_id, 
                    report_id, 
                    line_number, 
                    transaction_type, 
                    transaction_id, 
                    back_ref_transaction_id, 
                    back_ref_sched_name, 
                    entity_id, 
                    expenditure_date, 
                    expenditure_amount, 
                    semi_annual_refund_bundled_amount, 
                    expenditure_purpose, 
                    category_code, 
                    memo_code, 
                    memo_text, 
                    election_code, 
                    election_other_description, 
                    beneficiary_cmte_id, 
                    beneficiary_cand_id, 
                    other_name, 
                    other_street_1, 
                    other_street_2, 
                    other_city, 
                    other_state, 
                    other_zip, 
                    nc_soft_account, 
                    transaction_type_identifier,                     
                    beneficiary_cand_office,
                    beneficiary_cand_state,
                    beneficiary_cand_district,
                    beneficiary_cmte_name,
                    beneficiary_cand_last_name,
                    beneficiary_cand_first_name,
                    beneficiary_cand_middle_name,
                    beneficiary_cand_prefix,
                    beneficiary_cand_suffix,
                    aggregate_amt,
                    beneficiary_cand_entity_id,
                    levin_account_id,
                    aggregation_ind,
                    last_update_date,
                    create_date
                )
                VALUES ("""
                + ",".join(["%s"] * 42)
                + ")",

                [
                    cmte_id,
                    report_id,
                    line_number,
                    transaction_type,
                    transaction_id,
                    back_ref_transaction_id,
                    back_ref_sched_name,
                    entity_id,
                    expenditure_date,
                    expenditure_amount,
                    semi_annual_refund_bundled_amount,
                    expenditure_purpose,
                    category_code,
                    memo_code,
                    memo_text,
                    election_code,
                    election_other_description,
                    beneficiary_cmte_id,
                    beneficiary_cand_id,
                    other_name,
                    other_street_1,
                    other_street_2,
                    other_city,
                    other_state,
                    other_zip,
                    nc_soft_account,
                    transaction_type_identifier,
                    beneficiary_cand_office,
                    beneficiary_cand_state,
                    beneficiary_cand_district,
                    beneficiary_cmte_name,
                    beneficiary_cand_last_name,
                    beneficiary_cand_first_name,
                    beneficiary_cand_middle_name,
                    beneficiary_cand_prefix,
                    beneficiary_cand_suffix,
                    aggregate_amt,
                    beneficiary_cand_entity_id,
                    levin_account_id,
                    aggregation_ind,
                    datetime.datetime.now(),
                    datetime.datetime.now(),
                ],
            )
    except Exception:
        raise


def get_list_all_schedB(report_id, cmte_id):
    """
    get a list of all transactions with the same cmte_id and report_id
    """
    return get_sched_b_transactions(report_id, cmte_id)


def get_list_schedB(
    report_id, cmte_id, transaction_id, include_deleted_trans_flag=False
):
    """
    get sched_b item for this transaction_id
    """
    return get_sched_b_transactions(
        report_id,
        cmte_id,
        include_deleted_trans_flag=include_deleted_trans_flag,
        transaction_id=transaction_id,
    )


def get_list_child_schedB(report_id, cmte_id, transaction_id):
    """
    get all children sched_b items:
    back_ref_transaction_id == transaction_id
    """
    return get_sched_b_transactions(
        report_id, cmte_id, back_ref_transaction_id=transaction_id
    )

def put_sql_schedB(
    cmte_id,
    report_id,
    line_number,
    transaction_type,
    transaction_id,
    back_ref_transaction_id,
    back_ref_sched_name,
    entity_id,
    expenditure_date,
    expenditure_amount,
    semi_annual_refund_bundled_amount,
    expenditure_purpose,
    category_code,
    memo_code,
    memo_text,
    election_code,
    election_other_description,
    beneficiary_cmte_id,
    beneficiary_cand_id,
    other_name,
    other_street_1,
    other_street_2,
    other_city,
    other_state,
    other_zip,
    nc_soft_account,
    transaction_type_identifier,
    beneficiary_cand_office,
    beneficiary_cand_state,
    beneficiary_cand_district,
    beneficiary_cmte_name,
    beneficiary_cand_last_name,
    beneficiary_cand_first_name,
    beneficiary_cand_middle_name,
    beneficiary_cand_prefix,
    beneficiary_cand_suffix,
    aggregate_amt,
    beneficiary_cand_entity_id,
    levin_account_id,
    aggregation_ind = None,
):
    """
    db transaction for saving current sched_b item
    """
    try:
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE public.sched_b SET 
                            line_number = %s, 
                            transaction_type = %s, 
                            back_ref_transaction_id = %s, 
                            back_ref_sched_name = %s, 
                            entity_id = %s, 
                            expenditure_date = %s, 
                            expenditure_amount = %s, 
                            semi_annual_refund_bundled_amount = %s, 
                            expenditure_purpose = %s, 
                            category_code = %s, 
                            memo_code = %s, 
                            memo_text = %s, 
                            election_code = %s, 
                            election_other_description = %s, 
                            beneficiary_cmte_id = %s, 
                            beneficiary_cand_id = %s, 
                            other_name = %s, 
                            other_street_1 = %s, 
                            other_street_2 = %s, 
                            other_city = %s, 
                            other_state = %s, 
                            other_zip = %s, 
                            nc_soft_account = %s, 
                            transaction_type_identifier = %s, 
                            beneficiary_cand_office = %s,
                            beneficiary_cand_state = %s,
                            beneficiary_cand_district = %s,
                            beneficiary_cmte_name = %s,
                            beneficiary_cand_last_name = %s,
                            beneficiary_cand_first_name = %s,
                            beneficiary_cand_middle_name = %s,
                            beneficiary_cand_prefix = %s,
                            beneficiary_cand_suffix = %s,
                            aggregate_amt = %s,
                            beneficiary_cand_entity_id = %s,
                            levin_account_id = %s,
                            aggregation_ind = %s,
                            last_update_date = %s
                    WHERE transaction_id = %s 
                    AND report_id in ('{}') 
                    AND cmte_id = %s 
                    AND delete_ind is distinct from 'Y'
                """.format(
                    "', '".join(report_list)
                ),
                [
                    line_number,
                    transaction_type,
                    back_ref_transaction_id,
                    back_ref_sched_name,
                    entity_id,
                    expenditure_date,
                    expenditure_amount,
                    semi_annual_refund_bundled_amount,
                    expenditure_purpose,
                    category_code,
                    memo_code,
                    memo_text,
                    election_code,
                    election_other_description,
                    beneficiary_cmte_id,
                    beneficiary_cand_id,
                    other_name,
                    other_street_1,
                    other_street_2,
                    other_city,
                    other_state,
                    other_zip,
                    nc_soft_account,
                    transaction_type_identifier,
                    beneficiary_cand_office,
                    beneficiary_cand_state,
                    beneficiary_cand_district,
                    beneficiary_cmte_name,
                    beneficiary_cand_last_name,
                    beneficiary_cand_first_name,
                    beneficiary_cand_middle_name,
                    beneficiary_cand_prefix,
                    beneficiary_cand_suffix,
                    aggregate_amt,
                    beneficiary_cand_entity_id,
                    levin_account_id,
                    aggregation_ind,
                    datetime.datetime.now(),
                    transaction_id,
                    cmte_id,
                ],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "The Transaction ID: {} does not exist in schedB table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def delete_sql_schedB(transaction_id, report_id, cmte_id):
    """
    db transaction for deleting current item
    """
    try:
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:

            # UPDATE delete_ind flag on a single row from Sched_B table
            cursor.execute(
                """

                UPDATE public.sched_b 
                SET delete_ind = 'Y',
                last_update_date = %s 
                WHERE transaction_id = %s 
                AND report_id in ('{}')
                AND cmte_id = %s 
                AND delete_ind is distinct from 'Y'
                """.format(
                    "', '".join(report_list)
                ),
                [datetime.datetime.now(), transaction_id, cmte_id],
            )

            if cursor.rowcount == 0:
                raise Exception(
                    "The Transaction ID: {} is either already deleted or does not exist in schedB table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


# def delete_parent_child_link_sql_schedB(transaction_id, report_id, cmte_id):
#     """
#     db transaction for deleting all child transactions
#     """
#     try:
#         with connection.cursor() as cursor:

#             # UPDATE back_ref_transaction_id value to null in sched_b table
#             value = None
#             cursor.execute(
#                 """UPDATE public.sched_b SET back_ref_transaction_id = %s WHERE back_ref_transaction_id = %s AND report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""",
#                 [value, transaction_id, report_id, cmte_id],
#             )
#     except Exception:
#         raise


# not sure this function will ever be used - will implement this later
def post_cand_entity(data):
    """
    create a new entity
    """
    return save_cand_entity(data, new=True)


def put_cand_entity(data):
    """
    save/update an existing candiate entity
    """
    return save_cand_entity(data)


@new_report_date
def post_schedB(datum):
    """
    create and save current sched_b item
    """
    try:
        cmte_id = datum.get("cmte_id")
        entity_flag = False
        check_mandatory_fields_SB(datum, list_mandatory_fields_schedB)
        logger.debug("...mandatory check done.")
        if "entity_id" in datum:
            entity_flag = True
            get_data = {
                "cmte_id": datum.get("cmte_id"),
                "entity_id": datum.get("entity_id"),
            }
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
        else:
            entity_data = post_entities(datum)
        logger.debug("...entity saved")
        logger.debug("***datum:{}".format(datum))
        if datum.get("beneficiary_cand_entity_id"):
            logger.debug("saving cand data...")
            # get_data = {
            #     "cmte_id": datum.get("cmte_id"),
            #     "entity_id": datum.get("entity_id"),
            # }
            # prev_entity_list = get_entities(get_data)
            cand_data = put_cand_entity(datum)
            datum["beneficiary_cand_entity_id"] = cand_data.get("entity_id")
            logger.debug(
                "cand data saved with entity_id:{}".format(cand_data.get("entity_id"))
            )
        # else:
        #     cand_data = post_cand_entity(datum)
        entity_id = entity_data.get("entity_id")
        datum["entity_id"] = entity_id
        # datum["beneficiary_cand_entity_id"] = cand_data.get("entity_id")
        if datum.get("transaction_type_identifier") in SCHED_L_B_TRAN_TYPES:
            trans_char = "LB"  # for sched_l transactions
            datum["line_number"], datum[
                "transaction_type"
            ] = get_line_number_trans_type(datum.get("transaction_type_identifier"))
        else:
            trans_char = "SB"
        transaction_id = get_next_transaction_id(trans_char)
        datum["transaction_id"] = transaction_id

        # checking if beneficiary cmte id exists then copying entity name to beneficiary committee name as they both are the same
        if "beneficiary_cmte_id" in datum and datum.get("beneficiary_cmte_id") not in [
            "",
            " ",
            None,
            "none",
            "null",
            "None",
        ]:
            datum["beneficiary_cmte_name"] = datum.get("entity_name")

        if "election_code" in datum and datum.get("election_code") not in [
            "",
            " ",
            None,
            "none",
            "null",
            "None",
        ]:
            datum["election_code"] = datum.get("election_code") + str(
                datum.get("election_year", "")
            )
        try:
            post_sql_schedB(
                datum.get("cmte_id"),
                datum.get("report_id"),
                datum.get("line_number"),
                datum.get("transaction_type"),
                transaction_id,
                datum.get("back_ref_transaction_id"),
                datum.get("back_ref_sched_name"),
                entity_id,
                datum.get("expenditure_date"),
                datum.get("expenditure_amount"),
                datum.get("semi_annual_refund_bundled_amount"),
                datum.get("expenditure_purpose"),
                datum.get("category_code"),
                datum.get("memo_code"),
                datum.get("memo_text"),
                datum.get("election_code"),
                datum.get("election_other_description"),
                datum.get("beneficiary_cmte_id"),
                datum.get("beneficiary_cand_id"),
                datum.get("other_name"),
                datum.get("other_street_1"),
                datum.get("other_street_2"),
                datum.get("other_city"),
                datum.get("other_state"),
                datum.get("other_zip"),
                datum.get("nc_soft_account"),
                datum.get("transaction_type_identifier"),
                datum.get("beneficiary_cand_office"),
                datum.get("beneficiary_cand_state"),
                datum.get("beneficiary_cand_district"),
                datum.get("beneficiary_cmte_name"),
                datum.get("beneficiary_cand_last_name"),
                datum.get("beneficiary_cand_first_name"),
                datum.get("beneficiary_cand_middle_name"),
                datum.get("beneficiary_cand_prefix"),
                datum.get("beneficiary_cand_suffix"),
                datum.get("aggregate_amt"),
                datum.get("beneficiary_cand_entity_id"),
                datum.get("levin_account_id"),
                datum.get("aggregation_ind"),
            )
            logger.debug("payment transaction saved.")
            if datum.get("transaction_type_identifier") in SCHED_D_CHILD_LIST:
                update_sched_d_parent(
                    datum.get("cmte_id"),
                    datum.get("back_ref_transaction_id"),
                    datum.get("expenditure_amount"),
                )
            if datum.get("transaction_type_identifier") in SCHED_C_CHILD_LIST:
                update_sched_c_parent(
                    datum.get("cmte_id"),
                    datum.get("back_ref_transaction_id"),
                    datum.get("expenditure_amount"),
                )
            # Auto generation of redesignation transactions
            if "redesignation_id" in datum:
                redesignation_auto_generate_transactions(
                    datum["cmte_id"],
                    datum["report_id"],
                    datum["redesignation_id"],
                    datum["expenditure_date"],
                    datum["expenditure_amount"],
                    transaction_id,
                )

            # do aggregation: regular sb transactions
            if not transaction_id.startswith("LB"):
                update_schedB_aggamt_transactions(
                    datum.get("expenditure_date"),
                    datum.get("transaction_type_identifier"),
                    entity_id,
                    datum.get("cmte_id"),
                    datum.get("report_id"),
                )
            else:  # do aggregation: levin account transactions
                update_sl_summary(datum)

            # update line number based on aggregate amount info
            if datum['transaction_type_identifier'] in ['OPEXP_HQ_ACC_REG_REF','OPEXP_HQ_ACC_IND_REF',
                'OPEXP_HQ_ACC_TRIB_REF','OPEXP_CONV_ACC_REG_REF','OPEXP_CONV_ACC_TRIB_REF',
                'OPEXP_CONV_ACC_IND_REF','OTH_DISB_NP_RECNT_REG_REF','OTH_DISB_NP_RECNT_TRIB_REF',
                'OTH_DISB_NP_RECNT_IND_REF']:
                update_linenumber_aggamt_transactions_SA(
                    datum.get("expenditure_date"),
                    datum.get("transaction_type_identifier"),
                    entity_id,
                    datum.get("cmte_id"),
                    datum.get("report_id"),
                )
        except Exception as e:
            if entity_flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": datum.get(cmte_id), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The post_sql_schedB function is throwing an error: " + str(e)
            )
        # logger.debug("sched_b transaction saved successfully.")
        # if datum.get("transaction_type_identifier") in SCHED_L_B_TRAN_TYPES:
        #     (datum)update_sl_summary
        return datum
    except Exception as e:
        raise Exception("post_schedB function is throwing error: " + str(e))


def get_schedB(data):
    """
    db transaction for loading a sched_b item
    """
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        tran_desc_dic = get_transaction_type_descriptions()
        flag = False
        if "transaction_id" in data:
            try:
                transaction_id = data.get("transaction_id")
                check_transaction_id(transaction_id)
                flag = True
            except Exception:
                flag = False

        if flag:
            forms_obj = get_list_schedB(report_id, cmte_id, transaction_id)
            # adding hard-coded api call info to get object details
            for obj in forms_obj:
                obj.update({"api_call": "/sb/schedB"})
                if obj.get("election_code"):
                    obj.update({"election_year": obj.get("election_code")[1:]})
                    obj["election_code"] = obj.get("election_code")[0]
                # obj.update({"election_year": REQT_ELECTION_YR})
            child_forms_obj = get_list_child_schedB(report_id, cmte_id, transaction_id)
            for obj in child_forms_obj:
                obj.update({"api_call": "/sb/schedB"})
                if obj.get("election_code"):
                    obj.update({"election_year": obj.get("election_code")[1:]})
                    obj["election_code"] = obj.get("election_code")[0]
                # obj.update({"election_year": REQT_ELECTION_YR})
                tran_id = obj.get("transaction_type_identifier")
                obj.update(
                    {"transaction_type_description": tran_desc_dic.get(tran_id, "")}
                )
            if len(child_forms_obj) > 0:
                forms_obj[0]["child"] = child_forms_obj
        else:
            forms_obj = get_list_all_schedB(report_id, cmte_id)
            for obj in forms_obj:
                obj.update({"api_call": "/sb/schedB"})
                if obj.get("election_code"):
                    obj.update({"election_year": obj.get("election_code")[1:]})
                    obj["election_code"] = obj.get("election_code")[0]
                # obj.update({"election_year": REQT_ELECTION_YR})
        return forms_obj

    except:
        raise

# TODO: need to add beneficiary fields


# TODO: need to add beneficiary fields


def get_existing_expenditure(cmte_id, transaction_id):
    """
    fetch existing close balance in the db for current transaction
    """
    _sql = """
    select expenditure_amount
    from public.sched_b
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


@new_report_date
def put_schedB(datum):
    """
    save and update a sched_b item
    """
    try:
        check_mandatory_fields_SB(datum, list_mandatory_fields_schedB)
        transaction_id = datum.get("transaction_id")
        check_transaction_id(transaction_id)
        flag = False
        if "entity_id" in datum:
            flag = True
            get_data = {
                "cmte_id": datum.get("cmte_id"),
                "entity_id": datum.get("entity_id"),
            }
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
        else:
            entity_data = post_entities(datum)
        if datum.get("beneficiary_cand_entity_id"):
            # get_data = {
            #     "cmte_id": datum.get("cmte_id"),
            #     "entity_id": datum.get("entity_id"),
            # }
            # prev_entity_list = get_entities(get_data)
            cand_data = put_cand_entity(datum)
            datum["beneficiary_cand_entity_id"] = cand_data.get("entity_id")
        # else:
        #     cand_data = post_cand_entity(datum)
        entity_id = entity_data.get("entity_id")
        datum["entity_id"] = entity_id
        # datum["beneficiary_cand_entity_id"] = cand_data.get("entity_id")
        # entity_id = entity_data.get("entity_id")
        # datum["entity_id"] = entity_id

        # checking if beneficiary cmte id exists then copying entity name to beneficiary committee name as they both are the same
        if "beneficiary_cmte_id" in datum and datum.get("beneficiary_cmte_id") not in [
            "",
            " ",
            None,
            "none",
            "null",
            "None",
        ]:
            datum["beneficiary_cmte_name"] = datum.get("entity_name")

        if "election_code" in datum and datum.get("election_code") not in [
            "",
            " ",
            None,
            "none",
            "null",
            "None",
        ]:
            datum["election_code"] = datum.get("election_code") + str(
                datum.get("election_year", "")
            )
        try:
            if datum.get("transaction_type_identifier") in (
                SCHED_D_CHILD_LIST + SCHED_C_CHILD_LIST
            ):
                existing_exp = get_existing_expenditure(
                    datum.get("cmte_id"), datum.get("transaction_id")
                )
            put_sql_schedB(
                datum.get("cmte_id"),
                datum.get("report_id"),
                datum.get("line_number"),
                datum.get("transaction_type"),
                transaction_id,
                datum.get("back_ref_transaction_id"),
                datum.get("back_ref_sched_name"),
                entity_id,
                datum.get("expenditure_date"),
                datum.get("expenditure_amount"),
                datum.get("semi_annual_refund_bundled_amount"),
                datum.get("expenditure_purpose"),
                datum.get("category_code"),
                datum.get("memo_code"),
                datum.get("memo_text"),
                datum.get("election_code"),
                datum.get("election_other_description"),
                datum.get("beneficiary_cmte_id"),
                datum.get("beneficiary_cand_id"),
                datum.get("other_name"),
                datum.get("other_street_1"),
                datum.get("other_street_2"),
                datum.get("other_city"),
                datum.get("other_state"),
                datum.get("other_zip"),
                datum.get("nc_soft_account"),
                datum.get("transaction_type_identifier"),
                datum.get("beneficiary_cand_office"),
                datum.get("beneficiary_cand_state"),
                datum.get("beneficiary_cand_district"),
                datum.get("beneficiary_cmte_name"),
                datum.get("beneficiary_cand_last_name"),
                datum.get("beneficiary_cand_first_name"),
                datum.get("beneficiary_cand_middle_name"),
                datum.get("beneficiary_cand_prefix"),
                datum.get("beneficiary_cand_suffix"),
                datum.get("aggregate_amt"),
                datum.get("beneficiary_cand_entity_id"),
                datum.get("levin_account_id"),
                datum.get("aggregation_ind"),
            )
            logger.debug("sched_b data saved.")

            # need to update parent sched_d data if sched_d payment made
            if datum.get("transaction_type_identifier") in SCHED_D_CHILD_LIST:
                logger.debug("existing exp:{}".format(existing_exp))
                if float(existing_exp) != float(datum.get("expenditure_amount")):
                    update_sched_d_parent(
                        datum.get("cmte_id"),
                        datum.get("back_ref_transaction_id"),
                        datum.get("expenditure_amount"),
                        existing_exp,
                    )

            if datum.get("transaction_type_identifier") in SCHED_C_CHILD_LIST:
                logger.debug("existing exp:{}".format(existing_exp))
                if float(existing_exp) != float(datum.get("expenditure_amount")):
                    update_sched_c_parent(
                        datum.get("cmte_id"),
                        datum.get("back_ref_transaction_id"),
                        datum.get("expenditure_amount"),
                        existing_exp,
                    )

            if (
                datum.get("transaction_type_identifier")
                in CHILD_SCHEDB_AUTO_UPDATE_PARENT_SCHEDA_DICT.keys()
            ):
                transaction_data = get_list_schedA_from_schedB(
                    datum.get("report_id"),
                    datum.get("cmte_id"),
                    datum.get("back_ref_transaction_id"),
                )[0]
                transaction_data["entity_id"] = entity_id
                transaction_data["contribution_date"] = datum.get("expenditure_date")
                transaction_data["contribution_amount"] = datum.get(
                    "expenditure_amount"
                )
                transaction_data["election_code"] = datum.get("election_code")
                transaction_data["election_other_description"] = datum.get(
                    "election_other_description"
                )
                transaction_data["donor_cmte_id"] = datum.get("beneficiary_cmte_id")
                transaction_data["donor_cmte_name"] = datum.get("beneficiary_cmte_name")
                put_sql_schedA_from_schedB(
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
                    transaction_data.get("transaction_type_identifier"),
                )
            update_schedB_aggamt_transactions(
                datum.get("expenditure_date"),
                datum.get("transaction_type_identifier"),
                entity_id,
                datum.get("cmte_id"),
                datum.get("report_id"),
            )
            if datum['transaction_type_identifier'] in ['OPEXP_HQ_ACC_REG_REF','OPEXP_HQ_ACC_IND_REF',
                'OPEXP_HQ_ACC_TRIB_REF','OPEXP_CONV_ACC_REG_REF','OPEXP_CONV_ACC_TRIB_REF',
                'OPEXP_CONV_ACC_IND_REF','OTH_DISB_NP_RECNT_REG_REF','OTH_DISB_NP_RECNT_TRIB_REF',
                'OTH_DISB_NP_RECNT_IND_REF']:
                update_linenumber_aggamt_transactions_SA(
                    datum.get("expenditure_date"),
                    datum.get("transaction_type_identifier"),
                    entity_id,
                    datum.get("cmte_id"),
                    datum.get("report_id"),
                )
        except Exception as e:
            if flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": datum.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The put_sql_schedB function is throwing an error: " + str(e)
            )
        if datum.get("transaction_type_identifier") in SCHED_L_B_TRAN_TYPES:
            update_sl_summary(datum)
        return datum
    except:
        raise


def delete_schedB(data):
    """
    delete current sched_b item
    """
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        transaction_id = data.get("transaction_id")
        check_transaction_id(transaction_id)
        datum = get_list_schedB(report_id, cmte_id, transaction_id)[0]
        delete_sql_schedB(transaction_id, report_id, cmte_id)
        update_schedB_aggamt_transactions(
            datum.get("expenditure_date"),
            datum.get("transaction_type_identifier"),
            datum.get("entity_id"),
            datum.get("cmte_id"),
            datum.get("report_id"),
        )
        if datum['transaction_type_identifier'] in ['OPEXP_HQ_ACC_REG_REF','OPEXP_HQ_ACC_IND_REF',
            'OPEXP_HQ_ACC_TRIB_REF','OPEXP_CONV_ACC_REG_REF','OPEXP_CONV_ACC_TRIB_REF',
            'OPEXP_CONV_ACC_IND_REF','OTH_DISB_NP_RECNT_REG_REF','OTH_DISB_NP_RECNT_TRIB_REF',
            'OTH_DISB_NP_RECNT_IND_REF']:
            update_linenumber_aggamt_transactions_SA(
                    datum.get("expenditure_date"),
                    datum.get("transaction_type_identifier"),
                    entity_id,
                    datum.get("cmte_id"),
                    datum.get("report_id"),
                )
        # delete_parent_child_link_sql_schedB(transaction_id, report_id, cmte_id)
    except:
        raise


def validate_negative_transaction(data):
    """
    validate transaction amount if negative transaction encounterred.
    """
    if data.get("transaction_type_identifier") in NEGATIVE_TRANSACTIONS:
        if not float(data.get("expenditure_amount")) < 0:
            raise Exception("current transaction amount need to be negative!")


def parent_transaction_exists(tran_id, sched_tp):
    """
    check if parent transaction exists
    """
    return transaction_exists(tran_id, sched_tp)


def validate_parent_transaction_exist(data):
    """
    validate parent transaction exsit if saving a child transaction
    """
    if data.get("transaction_type_identifier") in CHILD_PARENT_SB_SB_TRANSACTIONS:
        if not data.get("back_ref_transaction_id"):
            raise Exception("Error: parent transaction id missing.")
        elif not parent_transaction_exists(
            data.get("back_ref_transaction_id"),
            CHILD_PARENT_SB_SB_TRANSACTIONS.get(
                data.get("transaction_type_identifier")
            )[1],
        ):
            raise Exception("Error: parent transaction not found.")
        else:
            pass



def schedB_sql_dict(data):
    """
    build a formulated data dictionary based on loaded 
    json and validate some field data
    """
    try:
        logger.debug('filtering data with schedB_sql_dict...')
        validate_negative_transaction(data)
        validate_parent_transaction_exist(data)
        # print(data)
        datum = {
            "line_number": data.get("line_number"),
            "transaction_type": data.get("transaction_type"),
            "transaction_type_identifier": data.get("transaction_type_identifier"),
            "back_ref_sched_name": data.get("back_ref_sched_name"),
            "expenditure_date": date_format(data.get("expenditure_date")),
            "expenditure_amount": check_decimal(data.get("expenditure_amount", None)),
            # "semi_annual_refund_bundled_amount": check_decimal(
            #     data.get("semi_annual_refund_bundled_amount", 0)
            # ),
            "expenditure_purpose": data.get("expenditure_purpose"),
            "category_code": data.get("category_code"),
            "memo_code": data.get("memo_code"),
            "memo_text": data.get("memo_text"),
            "election_code": data.get("election_code"),
            "election_year": data.get("election_year"),
            "election_other_description": data.get("election_other_description"),
            "beneficiary_cmte_id": data.get("beneficiary_cmte_id"),
            "beneficiary_cand_id": data.get("beneficiary_cand_id"),
            "other_name": data.get("other_name"),
            "other_street_1": data.get("other_street_1"),
            "other_street_2": data.get("other_street_2"),
            "other_city": data.get("other_city"),
            "other_state": data.get("other_state"),
            "other_zip": data.get("other_zip"),
            "nc_soft_account": data.get("nc_soft_account"),
            "beneficiary_cand_entity_id": data.get("beneficiary_cand_entity_id"),
            "beneficiary_cand_office": data.get("beneficiary_cand_office"),
            "beneficiary_cand_state": data.get("beneficiary_cand_state"),
            "beneficiary_cand_district": data.get("beneficiary_cand_district"),
            "beneficiary_cmte_name": data.get("beneficiary_cmte_name"),
            "beneficiary_cand_last_name": data.get("beneficiary_cand_last_name"),
            "beneficiary_cand_first_name": data.get("beneficiary_cand_first_name"),
            "beneficiary_cand_middle_name": data.get("beneficiary_cand_middle_name"),
            "beneficiary_cand_prefix": data.get("beneficiary_cand_prefix"),
            "beneficiary_cand_suffix": data.get("beneficiary_cand_suffix"),
            # "aggregate_amt": check_decimal(data.get("aggregate_amt", None)),
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
            # cand_entity_data
            "cand_office": data.get("cand_office"),
            "cand_office_state": data.get("cand_office_state"),
            "cand_office_district": data.get("cand_office_district"),
            # "beneficiary_cmte_name": data.get("beneficiary_cmte_name"),
            "cand_last_name": data.get("cand_last_name"),
            "cand_first_name": data.get("cand_first_name"),
            "cand_middle_name": data.get("cand_middle_name"),
            "cand_prefix": data.get("cand_prefix"),
            "cand_suffix": data.get("cand_suffix"),
            "cand_street_1": data.get("cand_street_1"),
            "cand_street_2": data.get("cand_street_2"),
            "cand_city": data.get("cand_city"),
            "cand_state": data.get("cand_state"),
            "cand_zip_code": data.get("cand_zip_code"),
            # levin transaction
            "levin_account_id": data.get("levin_account_id"),
            "aggregation_ind": data.get("aggregation_ind"),
        }
        # print('>>>>')
        if "aggregate_amt" in data and check_decimal(data.get("aggregate_amt")):
            datum["aggregate_amt"] = data.get("aggregate_amt")

        if "semi_annual_refund_bundled_amount" in data and check_decimal(
            data.get("semi_annual_refund_bundled_amount")
        ):
            datum["semi_annual_refund_bundled_amount"] = data.get(
                "semi_annual_refund_bundled_amount"
            )

        if "entity_id" in data and check_null_value(data.get("entity_id")):
            datum["entity_id"] = data.get("entity_id")
        datum["line_number"], datum["transaction_type"] = get_line_number_trans_type(
            data.get("transaction_type_identifier")
        )
        logger.debug('schedB_sql_dict done with {}'.format(datum))
        return datum
    except:
        raise


def redesignation_auto_generate_transactions(
    cmte_id,
    report_id,
    org_transaction_id,
    contribution_date,
    contribution_amount,
    redesignated_id,
):

    """ This function auto generates 2 copies of the transaction_id in the report_id. One will be an exact copy 
    of the transaction_id and other will have modifications to contribution date and amount. Kindly check FNE-1878
    ticket for the business rules that apply to reattribution"""
    try:
        query_string_original = """UPDATE public.sched_b SET redesignation_id=%s, redesignation_ind='O' WHERE transaction_id=%s AND cmte_id=%s"""
        query_string_redesignation = """UPDATE public.sched_b SET redesignation_id=%s, redesignation_ind='R' WHERE transaction_id=%s AND cmte_id=%s"""
        query_string_auto_1 = """INSERT INTO public.sched_b(
            cmte_id, report_id, line_number, transaction_type, 
            back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, 
            expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, 
            category_code, memo_code, memo_text, election_code, election_other_description, 
            beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, 
            other_street_2, other_city, other_state, other_zip, nc_soft_account, 
            delete_ind, beneficiary_cand_office, 
            beneficiary_cand_state, beneficiary_cand_district, aggregate_amt, 
            transaction_type_identifier, beneficiary_cmte_name, beneficiary_cand_last_name, 
            beneficiary_cand_first_name, beneficiary_cand_middle_name, beneficiary_cand_prefix, 
            beneficiary_cand_suffix, election_year, beneficiary_cand_entity_id, 
            itemized_ind, levin_account_id, redesignation_ind,redesignation_id)
            SELECT cmte_id, %s, line_number, transaction_type, 
               null, null, entity_id, expenditure_date, 
               expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose,
               category_code, 'X', 
               concat('MEMO: See ', (SELECT rrt.rpt_type_desc FROM public.ref_rpt_types rrt WHERE rrt.rpt_type = 
               (SELECT r.report_type FROM public.reports r WHERE r.report_id = %s)), ' report. Redesignation below'), 
               election_code, election_other_description, 
               beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, 
               other_street_2, other_city, other_state, other_zip, nc_soft_account,
               delete_ind, beneficiary_cand_office, 
               beneficiary_cand_state, beneficiary_cand_district, aggregate_amt, 
               transaction_type_identifier, beneficiary_cmte_name, beneficiary_cand_last_name, 
               beneficiary_cand_first_name, beneficiary_cand_middle_name, beneficiary_cand_prefix, 
               beneficiary_cand_suffix, election_year, beneficiary_cand_entity_id, 
               itemized_ind, levin_account_id, 'A', %s
            FROM public.sched_b WHERE transaction_id= %s and cmte_id= %s;"""

        query_string_auto_2 = """INSERT INTO public.sched_b(
            cmte_id, report_id, line_number, transaction_type, 
            back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, 
            expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, 
            category_code, memo_code, memo_text, election_code, election_other_description, 
            beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, 
            other_street_2, other_city, other_state, other_zip, nc_soft_account, 
            delete_ind, beneficiary_cand_office, 
            beneficiary_cand_state, beneficiary_cand_district, aggregate_amt, 
            transaction_type_identifier, beneficiary_cmte_name, beneficiary_cand_last_name, 
            beneficiary_cand_first_name, beneficiary_cand_middle_name, beneficiary_cand_prefix, 
            beneficiary_cand_suffix, election_year, beneficiary_cand_entity_id, 
            itemized_ind, levin_account_id, redesignation_ind,redesignation_id)
            SELECT cmte_id, %s, line_number, transaction_type, 
               null, null, entity_id, %s, 
               %s, semi_annual_refund_bundled_amount, expenditure_purpose,
               category_code, 'X', 'MEMO: Redesignated Below', election_code, election_other_description, 
               beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, 
               other_street_2, other_city, other_state, other_zip, nc_soft_account, 
               delete_ind, beneficiary_cand_office, 
               beneficiary_cand_state, beneficiary_cand_district, aggregate_amt, 
               transaction_type_identifier, beneficiary_cmte_name, beneficiary_cand_last_name, 
               beneficiary_cand_first_name, beneficiary_cand_middle_name, beneficiary_cand_prefix, 
               beneficiary_cand_suffix, election_year, beneficiary_cand_entity_id, 
               itemized_ind, levin_account_id, 'A', %s
          FROM public.sched_b WHERE transaction_id= %s and cmte_id= %s;"""

        query_string_aggregate = """SELECT expenditure_date, transaction_type_identifier,
        entity_id, cmte_id, report_id FROM public.sched_b WHERE redesignation_id=%s and 
        redesignation_ind='A' AND expenditure_amount >= 0 AND cmte_id=%s"""

        with connection.cursor() as cursor:
            cursor.execute(
                query_string_auto_1,
                [report_id, report_id, redesignated_id, org_transaction_id, cmte_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "The transaction ID: {} does not exist in sched_b for committee ID: {}".format(
                        org_transaction_id, cmte_id
                    )
                )
            cursor.execute(
                query_string_auto_2,
                [
                    report_id,
                    contribution_date,
                    -1 * Decimal(contribution_amount),
                    redesignated_id,
                    org_transaction_id,
                    cmte_id,
                ],
            )
            cursor.execute(
                query_string_original, [redesignated_id, org_transaction_id, cmte_id]
            )
            cursor.execute(
                query_string_redesignation,
                [org_transaction_id, redesignated_id, cmte_id],
            )
            cursor.execute(query_string_aggregate, [redesignated_id, cmte_id])
            # print(cursor.query)
            aggregate_data = cursor.fetchone()
            # print(aggregate_data)
            if aggregate_data:
                update_schedB_aggamt_transactions(
                    aggregate_data[0],
                    aggregate_data[1],
                    aggregate_data[2],
                    aggregate_data[3],
                    aggregate_data[4],
                )
            if aggregate_data[0].strftime("%Y") != contribution_date.strftime("%Y"):
                update_schedB_aggamt_transactions(
                    contribution_date,
                    aggregate_data[1],
                    aggregate_data[2],
                    aggregate_data[3],
                    aggregate_data[4],
                )
    except Exception as e:
        raise Exception(
            "The redesignation_auto_generate_transactions function is throwing an error: "
            + str(e)
        )


def redesignation_auto_update_transactions(
    cmte_id, report_id, expenditure_date, expenditure_amount, redesignated_id
):
    try:
        query_string = """UPDATE public.sched_b SET report_id = %s
        WHERE transaction_id = %s AND cmte_id = %s AND delete_ind IS DISTINCT FROM 'Y'"""

        query_string_s1 = """UPDATE public.sched_b SET report_id = %s
        WHERE redesignation_id = %s AND cmte_id = %s AND expenditure_amount > 0 AND redesignation_ind='A'"""

        query_string_s2 = """UPDATE public.sched_b SET report_id = %s, expenditure_date = %s, expenditure_amount = %s
        WHERE redesignation_id = %s AND cmte_id = %s AND expenditure_amount < 0 AND redesignation_ind='A'"""

        query_string_aggregate = """SELECT expenditure_date, transaction_type_identifier,
        entity_id, cmte_id, report_id FROM public.sched_b WHERE redesignation_id=%s and 
        redesignation_ind='A' AND expenditure_amount >= 0 AND cmte_id=%s"""

        with connection.cursor() as cursor:
            cursor.execute(query_string, [report_id, redesignated_id, cmte_id])
            if cursor.rowcount == 0:
                raise Exception(
                    "The transaction ID: {} does not exist in sched_b for committee ID: {}".format(
                        redesignated_id, cmte_id
                    )
                )
        with connection.cursor() as cursor:
            cursor.execute(query_string_s1, [report_id, redesignated_id, cmte_id])
            if cursor.rowcount == 0:
                raise Exception(
                    "The Redesignated ID: {} does not exist in sched_b for committee ID: {}".format(
                        redesignated_id, cmte_id
                    )
                )
        with connection.cursor() as cursor:
            cursor.execute(
                query_string_s2,
                [
                    report_id,
                    expenditure_date,
                    -1 * Decimal(expenditure_amount),
                    redesignated_id,
                    cmte_id,
                ],
            )
            cursor.execute(query_string_aggregate, [redesignated_id, cmte_id])
            # print(cursor.query)
            aggregate_data = cursor.fetchone()
            # print(aggregate_data)
            if aggregate_data:
                update_schedB_aggamt_transactions(
                    aggregate_data[0],
                    aggregate_data[1],
                    aggregate_data[2],
                    aggregate_data[3],
                    aggregate_data[4],
                )
            if aggregate_data[0].strftime("%Y") != expenditure_date.strftime("%Y"):
                update_schedB_aggamt_transactions(
                    expenditure_date,
                    aggregate_data[1],
                    aggregate_data[2],
                    aggregate_data[3],
                    aggregate_data[4],
                )
    except Exception as e:
        raise Exception(
            "The redesignation_auto_update_transactions function is throwing an error: "
            + str(e)
        )


def list_all_sb_transactions_entity(
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
            SELECT t1.expenditure_amount, 
                t1.transaction_id, 
                t1.report_id, 
                t1.line_number, 
                t1.expenditure_date, 
                (SELECT t2.delete_ind FROM public.reports t2 WHERE t2.report_id = t1.report_id), 
                t1.memo_code, 
                t1.back_ref_transaction_id,
                t1.transaction_type_identifier,
                t1.redesignation_ind, 
                t1.aggregation_ind
            FROM public.sched_b t1 
            WHERE entity_id = %s 
            AND cmte_id = %s 
            AND expenditure_date >= %s 
            AND expenditure_date <= %s 
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY expenditure_date ASC, create_date ASC
            """,
                [entity_id, cmte_id, aggregate_start_date, aggregate_end_date],
            )
            # print(cursor.query)
            transactions_list = cursor.fetchall()
        return transactions_list
    except Exception as e:
        raise Exception(
            "The list_all_sb_transactions_entity function is throwing an error: "
            + str(e)
        )


def get_sb_linenumber_itemization(
    transaction_type_identifier, aggregate_amount, itemization_value, line_number
):
    try:
        itemized_ind = None
        output_line_number = line_number

        if (
            transaction_type_identifier
            in ITEMIZED_SB_UPDATE_TRANSACTION_TYPE_IDENTIFIER
            and aggregate_amount <= itemization_value
        ):
            itemized_ind = "U"
        else:
            itemized_ind = "I"
        return output_line_number, itemized_ind
    except Exception as e:
        raise Exception(
            "The get_linenumber_itemization function is throwing an error: " + str(e)
        )


def put_sql_linenumber_schedB(
    cmte_id, line_number, itemized_ind, transaction_id, entity_id, aggregate_amount
):
    """
    update line number
    """
    try:
        with connection.cursor() as cursor:
            # Insert data into schedB table
            cursor.execute(
                """UPDATE public.sched_b SET line_number = %s, itemized_ind = %s, aggregate_amt = %s WHERE transaction_id = %s AND cmte_id = %s AND entity_id = %s AND delete_ind is distinct from 'Y'""",
                [
                    line_number,
                    itemized_ind,
                    aggregate_amount,
                    transaction_id,
                    cmte_id,
                    entity_id,
                ],
            )
            # print(cursor.query)
            if cursor.rowcount == 0:
                raise Exception(
                    "put_sql_linenumber_schedB function: The Transaction ID: {} does not exist in schedB table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def update_schedB_aggamt_transactions(
    expenditure_date, transaction_type_identifier, entity_id, cmte_id, report_id
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
        itemization_value = 200
        # itemized_transaction_list = []
        # unitemized_transaction_list = []
        form_type = find_form_type(report_id, cmte_id)
        if isinstance(expenditure_date, str):
            expenditure_date = date_format_agg(expenditure_date)
        aggregate_start_date, aggregate_end_date = find_aggregate_date(
            form_type, expenditure_date
        )
        # make sure transaction list comes back sorted by contribution_date ASC
        transactions_list = list_all_sb_transactions_entity(
            aggregate_start_date, aggregate_end_date, entity_id, cmte_id
        )
        aggregate_amount = 0
        committee_type = cmte_type(cmte_id)
        for transaction in transactions_list:
            # checking in reports table if the delete_ind flag is false for the corresponding report
            if transaction[5] != "Y":
                # checking if the back_ref_transaction_id is null or not.
                # If back_ref_transaction_id is none, checking if the transaction is a memo or not, using memo_code not equal to X.
                # according to new spec, all transations need to be aggregated
                # if transaction[7] != None or (
                #     transaction[7] == None and
                #     (transaction[6] != "X")
                # ):
                if transaction[10] != "N":
                    aggregate_amount += transaction[0]
                if expenditure_date <= transaction[4]:
                    line_number, itemized_ind = get_sb_linenumber_itemization(
                        transaction[8],
                        aggregate_amount,
                        itemization_value,
                        transaction[3],
                    )
                    put_sql_linenumber_schedB(
                        cmte_id,
                        line_number,
                        itemized_ind,
                        transaction[1],
                        entity_id,
                        aggregate_amount,
                    )

    except Exception as e:
        raise Exception(
            "The update_schedB_aggamt_transactions function is throwing an error: "
            + str(e)
        )


def update_sb_aggregation_status(transaction_id, status):
    """
    helpder function to update sa aggregation_ind
    """
    _sql = """
    update public.sched_b
    set aggregation_ind = %s
    where transaction_id = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, [status, transaction_id])
            if cursor.rowcount == 0:
                raise Exception(
                    "The Transaction ID: {} does not exist in sb table".format(
                        transaction_id
                    )
                )
    except:
        raise


@api_view(["PUT"])
def force_aggregate_sb(request):
    """
    api to force a transaction to be aggregated:
    1. set aggregate_ind = 'Y'
    2. re-do entity-based aggregation on sb
    """
    # if request.method == "GET":
    try:
        cmte_id = request.user.username
        report_id = request.data.get("report_id")
        transaction_id = request.data.get("transaction_id")
        if not transaction_id:
            raise Exception("transaction id is required for this api call.")
        update_sb_aggregation_status(transaction_id, "Y")
        sb_data = get_list_schedB(report_id, cmte_id, transaction_id)[0]
        update_schedB_aggamt_transactions(
            sb_data.get("expenditure_date"),
            sb_data.get("transaction_type_identifier"),
            sb_data.get("entity_id"),
            cmte_id,
            report_id,
        )
        return JsonResponse(
                {"status": "success"}, status=status.HTTP_200_OK
            )
        # update_linenumber_aggamt_transactions_SA(
        #     sb_data.get("contribution_date"),
        #     sb_data.get("transaction_type_identifier"),
        #     sb_data.get("entity_id"),
        #     cmte_id,
        #     report_id,
        # )
    except Exception as e:
        return Response(
            "The force_aggregate_sb API is throwing an error: " + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )

def force_itemize_unitemize(request, itemize=None):
    """
    helper function to itemize/un-itemize a transaction
    """
    try:
        cmte_id = request.user.username
        report_id = request.data.get("report_id")
        transaction_id = request.data.get("transaction_id")
        if not transaction_id:
            raise Exception("transaction id is required for this api call.")
        sb_data = get_list_schedB(report_id, cmte_id, transaction_id)[0]
        update_sb_itmization_status(sb_data, status=itemize)
        return JsonResponse(
                {"status": "success"}, status=status.HTTP_200_OK
            )
    except Exception as e:
        return Response(
            "The force_itemize_sb API is throwing an error: " + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )

def update_sb_itmization_status(data, status = None):
    """
    helpder function
    """
    transaction_type_identifier = data.get('transaction_type_identifier')
    transaction_id = data.get('transaction_id')
    report_id = data.get('report_id')
    if transaction_type_identifier in ITEMIZED_SB_UPDATE_TRANSACTION_TYPE_IDENTIFIER:
        
        # line_number = '11AI' if status == 'Y' else '11AII'
        
        _sql = """
        update public.sched_b
        set itemized_ind = %s
        where transaction_id = %s and report_id = %s
        """
        parameters = [status, transaction_id, report_id]
    else:
        raise Exception('current transaction cannot be force-unitemized.')
        # _sql = """
        # update public.sched_a
        # set itemized_ind = %s
        # where transaction_id = %s and report_id = %s
        # """
        # parameters = [status, transaction_id, report_id]
    with connection.cursor() as cursor:
        cursor.execute(_sql, parameters)
        if cursor.rowcount == 0:
            raise Exception('update itemization status failed for {}'.format(transaction_id))



@api_view(["PUT"])
def force_unitemize_sb(request):
    """
    api to force a sched_b transaction to be itemized:
    1. set itemized_ind = 'Y'
    """
    return force_itemize_unitemize(request, itemize='N')
    

@api_view(["PUT"])
def force_itemize_sb(request):
    """
    api to force a sched_b transaction to be itemized:
    1. set itemized_ind = 'Y'
    """
    return force_itemize_unitemize(request, itemize='Y')
    # # if request.method == "GET":
    # try:
    #     cmte_id = request.user.username
    #     report_id = request.data.get("report_id")
    #     transaction_id = request.data.get("transaction_id")
    #     if not transaction_id:
    #         raise Exception("transaction id is required for this api call.")
    #     sb_data = get_list_schedB(report_id, cmte_id, transaction_id)[0]
    #     update_sa_itmization_status(sb_data, status = 'Y')
    #     return JsonResponse(
    #             {"status": "success"}, status=status.HTTP_200_OK
    #         )
    # except Exception as e:
    #     return Response(
    #         "The force_itemize_sb API is throwing an error: " + str(e),
    #         status=status.HTTP_400_BAD_REQUEST,
    #     )


@api_view(["PUT"])
def force_unaggregate_sb(request):
    """
    api to force a transaction to be un-aggregated:
    1. set aggregate_ind = 'N'
    2. re-do entity-based aggregation on sb
    """
    # if request.method == "GET":
    try:
        cmte_id = request.user.username
        report_id = request.data.get("report_id")
        transaction_id = request.data.get("transaction_id")
        if not transaction_id:
            raise Exception("transaction id is required for this api call.")
        update_sb_aggregation_status(transaction_id, "N")
        sb_data = get_list_schedB(report_id, cmte_id, transaction_id)[0]
        update_schedB_aggamt_transactions(
            sb_data.get("expenditure_date"),
            sb_data.get("transaction_type_identifier"),
            sb_data.get("entity_id"),
            cmte_id,
            report_id,
        )
        return JsonResponse(
                {"status": "success"}, status=status.HTTP_200_OK
            )
        # update_linenumber_aggamt_transactions_SA(
        #     sb_data.get("contribution_date"),
        #     sb_data.get("transaction_type_identifier"),
        #     sb_data.get("entity_id"),
        #     cmte_id,
        #     report_id,
        # )
    except Exception as e:
        return Response(
            "The force_aggregate_sb API is throwing an error: " + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedB(request):
    """
    CRUD api for sched_b
    """
    global REQT_ELECTION_YR
    if request.method == "POST":
        if "election_year" in request.data:
            REQT_ELECTION_YR = request.data.get("election_year")
        if "election_year" in request.query_params:
            REQT_ELECTION_YR = request.query_params.get("election_year")
        try:
            # checking if redesignation is triggered for a transaction
            logger.debug("sched_b POST call with request data:{}".format(request.data))
            redesignation_flag = False
            if "redesignation_id" in request.data and request.data[
                "redesignation_id"
            ] not in ["", "", None, "null"]:
                redesignation_flag = True
                if "redesignation_report_id" not in request.data:
                    raise Exception(
                        "redesignation_report_id parameter is missing. Kindly provide this id to continue redesignation"
                    )
            cmte_id = request.user.username
            if not ("report_id" in request.data):
                raise Exception("Missing Input: Report_id is mandatory")
            if not ("transaction_type_identifier" in request.data):
                raise Exception("Missing Input: transaction_type_identifier")
            # handling null,none value of report_id
            # TODO: can report_id be 0? what does it mean?
            if not (check_null_value(request.data.get("report_id"))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get("report_id"))
            # end of handling
            datum = schedB_sql_dict(request.data)
            datum["report_id"] = report_id
            datum["cmte_id"] = cmte_id
            # Adding memo_code and memo_text values for redesignation flags
            if redesignation_flag:
                datum["memo_code"] = "X"
                datum["memo_text"] = "MEMO: Redesignated"
                datum["report_id"] = check_report_id(
                    request.data["redesignation_report_id"]
                )
                datum["redesignation_id"] = request.data["redesignation_id"]
            if "entity_id" in request.data and check_null_value(
                request.data.get("entity_id")
            ):
                datum["entity_id"] = request.data.get("entity_id")
            if "transaction_id" in request.data and check_null_value(
                request.data.get("transaction_id")
            ):
                datum["transaction_id"] = check_transaction_id(
                    request.data.get("transaction_id")
                )
                data = put_schedB(datum)
            else:
                logger.debug('calling post_schedB with data:{}'.format(datum))
                data = post_schedB(datum)

            # Associating child transactions to parent and storing them to DB
            if "child" in request.data:
                children = check_type_list(request.data.get("child"))
                if len(children) > 0:
                    child_output = []
                    for child in children:
                        child_datum = schedB_sql_dict(child)
                        child_datum["back_ref_transaction_id"] = data.get(
                            "transaction_id"
                        )
                        child_datum["report_id"] = report_id
                        child_datum["cmte_id"] = cmte_id
                        if "entity_id" in child and check_null_value(
                            child.get("entity_id")
                        ):
                            child_datum["entity_id"] = child.get("entity_id")
                        if "transaction_id" in child and check_null_value(
                            child.get("transaction_id")
                        ):
                            child_datum["transaction_id"] = check_transaction_id(
                                child.get("transaction_id")
                            )
                            child_data = put_schedB(child_datum)
                        else:
                            child_data = post_schedB(child_datum)
            output = get_schedB(data)
            # for earmark child transaction: update parent transction  purpose_description
            if datum.get("transaction_type_identifier") in EARMARK_SB_CHILD_LIST:
                update_earmark_parent_purpose(datum)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                "The schedB API - POST is throwing an exception: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Get records from schedB table
    if request.method == "GET":
        if "election_year" in request.data:
            REQT_ELECTION_YR = request.data.get("election_year")
        if "election_year" in request.query_params:
            REQT_ELECTION_YR = request.query_params.get("election_year")

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
            if "transaction_id" in request.query_params and check_null_value(
                request.query_params.get("transaction_id")
            ):
                data["transaction_id"] = check_transaction_id(
                    request.query_params.get("transaction_id")
                )
            datum = get_schedB(data)
            # for obj in datum:
            #     obj.update({"api_call": "sb/schedB"})
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
                "The schedB API - GET is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Modify a single record from schedB table
    if request.method == "PUT":
        if "election_year" in request.data:
            REQT_ELECTION_YR = request.data.get("election_year")
        if "election_year" in request.query_params:
            REQT_ELECTION_YR = request.query_params.get("election_year")

        try:
            # checking if redesignation is triggered for a transaction
            redesignation_flag = False
            if "isRedesignation" in request.data and request.data[
                "isRedesignation"
            ] not in ["None", "null", "", ""]:
                if request.data["isRedesignation"] in ["True", "true", "t", "T", True]:
                    redesignation_flag = True
                    if "redesignation_report_id" not in request.data:
                        raise Exception(
                            "redesignation_report_id parameter is missing. Kindly provide this id to continue reattribution"
                        )
                    else:
                        redesignation_report_id = check_report_id(
                            request.data["redesignation_report_id"]
                        )
            datum = schedB_sql_dict(request.data)

            if "transaction_id" in request.data and check_null_value(
                request.data.get("transaction_id")
            ):
                datum["transaction_id"] = check_transaction_id(
                    request.data.get("transaction_id")
                )
            else:
                raise Exception("Missing Input: transaction_id is mandatory")

            if not ("report_id" in request.data):
                raise Exception("Missing Input: Report_id is mandatory")
            # handling null,none value of report_id
            if not (check_null_value(request.data.get("report_id"))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get("report_id"))
            # end of handling
            datum["report_id"] = report_id
            datum["back_ref_transaction_id"] = request.data.get(
                "back_ref_transaction_id"
            )
            datum["cmte_id"] = request.user.username

            if "entity_id" in request.data and check_null_value(
                request.data.get("entity_id")
            ):
                datum["entity_id"] = request.data.get("entity_id")
            # updating data for redesignation fields
            if redesignation_flag:
                datum["memo_code"] = "X"
                datum["memo_text"] = "MEMO: Redesignated"
            data = put_schedB(datum)
            # Updating auto generated transactions for redesignated transactions
            if redesignation_flag:
                redesignation_auto_update_transactions(
                    datum["cmte_id"],
                    redesignation_report_id,
                    datum["expenditure_date"],
                    datum["expenditure_amount"],
                    datum["transaction_id"],
                )
                data["report_id"] = redesignation_report_id
            output = get_schedB(data)
            # for earmark child transaction: update parent transction  purpose_description
            if datum.get("transaction_type_identifier") in EARMARK_SB_CHILD_LIST:
                update_earmark_parent_purpose(datum)
            # UPDATE auto generated redesignation transactions
            if output[0].get("redesignation_ind") == "O":
                update_auto_generated_redesignated_transactions(output[0])
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.debug(e)
            return Response(
                "The schedB API - PUT is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Delete a single record from schedB table
    if request.method == "DELETE":

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
            if "transaction_id" in request.query_params and check_null_value(
                request.query_params.get("transaction_id")
            ):
                data["transaction_id"] = check_transaction_id(
                    request.query_params.get("transaction_id")
                )
            else:
                raise Exception("Missing Input: transaction_id is mandatory")
            delete_schedB(data)
            return Response(
                "The Transaction ID: {} has been successfully deleted".format(
                    data.get("transaction_id")
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.debug(e)
            return Response(
                "The schedB API - DELETE is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )


def update_auto_generated_redesignated_transactions(data):
    try:
        with connection.cursor() as cursor:
            auto_sql_1 = """UPDATE public.sched_b SET line_number = %s, transaction_type = %s, 
            entity_id = %s, expenditure_date = %s, expenditure_amount = %s, semi_annual_refund_bundled_amount = %s, 
            expenditure_purpose = %s, category_code = %s, election_code = %s, election_other_description = %s, 
            beneficiary_cmte_id = %s, other_name = %s, other_street_1 = %s, other_street_2 = %s, other_city = %s, 
            other_state = %s, other_zip = %s, nc_soft_account = %s, beneficiary_cmte_name = %s, 
            beneficiary_cand_entity_id = %s, levin_account_id = %s
            WHERE redesignation_ind = 'A' AND redesignation_id = %s 
            AND delete_ind IS DISTINCT FROM 'Y' AND cmte_id = %s AND expenditure_amount > 0"""
            cursor.execute(
                auto_sql_1,
                [
                    data["line_number"],
                    data["transaction_type"],
                    data["entity_id"],
                    data["expenditure_date"],
                    data["expenditure_amount"],
                    data["semi_annual_refund_bundled_amount"],
                    data["expenditure_purpose"],
                    data["category_code"],
                    data["election_code"],
                    data["election_other_description"],
                    data["beneficiary_cmte_id"],
                    data["other_name"],
                    data["other_street_1"],
                    data["other_street_2"],
                    data["other_city"],
                    data["other_state"],
                    data["other_zip"],
                    data["nc_soft_account"],
                    data["beneficiary_cmte_name"],
                    data["beneficiary_cand_entity_id"],
                    data["levin_account_id"],
                    data["redesignation_id"],
                    data["cmte_id"],
                ],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "There are no auto generated transactions for this redesignation_id:{} and cmte_id:{}".format(
                        data["redesignation_id"], data["cmte_id"]
                    )
                )

        with connection.cursor() as cursor:
            auto_sql_2 = """UPDATE public.sched_b SET line_number = %s, transaction_type = %s, 
            entity_id = %s, semi_annual_refund_bundled_amount = %s, 
            expenditure_purpose = %s, category_code = %s, election_code = %s, election_other_description = %s, 
            beneficiary_cmte_id = %s, other_name = %s, other_street_1 = %s, other_street_2 = %s, other_city = %s, 
            other_state = %s, other_zip = %s, nc_soft_account = %s, beneficiary_cmte_name = %s, 
            beneficiary_cand_entity_id = %s, levin_account_id = %s
            WHERE redesignation_ind = 'A' AND redesignation_id = %s 
            AND delete_ind IS DISTINCT FROM 'Y' AND cmte_id = %s AND expenditure_amount < 0"""
            cursor.execute(
                auto_sql_2,
                [
                    data["line_number"],
                    data["transaction_type"],
                    data["entity_id"],
                    data["semi_annual_refund_bundled_amount"],
                    data["expenditure_purpose"],
                    data["category_code"],
                    data["election_code"],
                    data["election_other_description"],
                    data["beneficiary_cmte_id"],
                    data["other_name"],
                    data["other_street_1"],
                    data["other_street_2"],
                    data["other_city"],
                    data["other_state"],
                    data["other_zip"],
                    data["nc_soft_account"],
                    data["beneficiary_cmte_name"],
                    data["beneficiary_cand_entity_id"],
                    data["levin_account_id"],
                    data["redesignation_id"],
                    data["cmte_id"],
                ],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "There are no auto generated transactions for this redesignation_id:{} and cmte_id:{}".format(
                        data["redesignation_id"], data["cmte_id"]
                    )
                )

    except Exception as e:
        raise Exception(
            "The update_auto_generated_redesignated_transactions function is throwing an error: "
            + str(e)
        )


def get_list_schedA_from_schedB(
    report_id, cmte_id, transaction_id=None, include_deleted_trans_flag=False
):

    try:
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:
            # GET single row from schedA table
            if transaction_id:
                if not include_deleted_trans_flag:
                    query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, 
                    entity_id, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, 
                    election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                    FROM public.sched_a 
                    WHERE report_id in ('{}') AND cmte_id = %s AND transaction_id = %s AND delete_ind is distinct from 'Y'""".format(
                        "', '".join(report_list)
                    )
                else:
                    query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, 
                    entity_id, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, 
                    election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                    FROM public.sched_a 
                    WHERE report_id in ('{}') AND cmte_id = %s AND transaction_id = %s""".format(
                        "', '".join(report_list)
                    )

                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [report_id, cmte_id, transaction_id],
                )
            else:
                if not include_deleted_trans_flag:
                    query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, 
                    back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, 
                    memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                    FROM public.sched_a 
                    WHERE report_id in ('{}') AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC""".format(
                        "', '".join(report_list)
                    )
                else:
                    query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, 
                    back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, 
                    memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                    FROM public.sched_a 
                    WHERE report_id in ('{}') AND cmte_id = %s ORDER BY transaction_id DESC""".format(
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
