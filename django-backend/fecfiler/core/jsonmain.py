from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
import maya
from .models import Cmte_Report_Types_View, My_Forms_View  # , GenericDocument
from rest_framework.response import Response
from fecfiler.forms.models import CommitteeInfo
from fecfiler.forms.serializers import CommitteeInfoSerializer
import json
import datetime
import os
import requests
from django.views.decorators.csrf import csrf_exempt
import logging
from django.db import connection
from django.http import JsonResponse
from datetime import datetime, date
import boto3
from boto3.s3.transfer import S3Transfer
from botocore.exceptions import ClientError
import boto
from boto.s3.key import Key
from django.conf import settings
import re
import csv
from django.core.paginator import Paginator
from fecfiler.core.views import (get_list_entity, NoOPError, get_cvg_dates)

conn = boto.connect_s3()

# Dictionary mapping form type value to form type in forms_and_schedules table
FORMTYPE_FORM_DICT = {
        'F3X': 'form_3x'
}

# Dictionary mapping schedules to schedule codes in forms_and_schedules table
SCHED_SCHED_CODES_DICT = {
        'sched_a': 'SA',
        'sched_b': 'SB',
        'sched_c': 'SC',
        # 'sched_c1': 'SC1',
        # 'sched_c2': 'SC2',
        'sched_d': 'SD',
        'sched_e': 'SE',
        'sched_f': 'SF',
        'sched_h1': 'SH',
        'sched_h2': 'SH',
        'sched_h3': 'SH',
        'sched_h4': 'SH',
        'sched_h5': 'SH',
        'sched_h6': 'SH',
        'sched_l': 'SL',

}
# Dictionary that maps form type to the schedules that it should include
# FORMTYPE_SCHEDULES_DICT = {
#     'F3X': ['SA', 'SB']
# }

# Dictionary mapping schedules to DB table name
# SCHEDULES_DBTABLES_DICT = {
#     'SA': 'public.sched_a',
#     'SB': 'public.sched_b',
#     'SE': 'public.sched_e',
#     'SF': 'public.sched_f',
#     'SC': 'public.sched_c'
# }

# Dictionary that excludes line numbers from final json
EXCLUDED_LINE_NUMBERS_FROM_JSON_LIST = ['11AII']

# List of all sched D transction type identifiers. This has no back_ref_transaction_id column so modifying SQL based on this list
list_of_transaction_types_with_no_back_ref = ['DEBT_TO_VENDOR', 'LOANS_OWED_TO_CMTE', 'LOANS_OWED_BY_CMTE', 'ALLOC_H1', 'ALLOC_H2_RATIO', 'TRAN_FROM_NON_FED_ACC', 'TRAN_FROM_LEVIN_ACC', 'SCHED_L_SUM']

list_of_SL_SA_transaction_types = ['LEVIN_TRIB_REC', 'LEVIN_PARTN_REC', 'LEVIN_ORG_REC', 'LEVIN_INDV_REC', 'LEVIN_NON_FED_REC', 'LEVIN_OTH_REC', 'LEVIN_PAC_REC']

list_of_SL_SB_transaction_types = ['LEVIN_VOTER_ID', 'LEVIN_GOTV', 'LEVIN_GEN', 'LEVIN_OTH_DISB', 'LEVIN_VOTER_REG']


def get_header_details():
    return {
        "version": "8.3",
        "softwareName": "ABC Inc",
        "softwareVersion": "1.02 Beta",
        "additionalInfomation": "Any other useful information"
    }


def json_query(query, query_values_list, error_string, empty_list_flag):
    try:
        with connection.cursor() as cursor:
            sql_query = """SELECT json_agg(t) FROM ({}) t""".format(query)
            # print(sql_query)
            cursor.execute(sql_query, query_values_list)
            # print(cursor.query.decode("utf-8"))
            result = cursor.fetchone()[0]
            if result is None:
                # TO Handle zero transactions in sched_a or sched_b for a specific transaction_type_identifer using this condition
                if empty_list_flag:
                        return []
                else:
                    raise NoOPError('No results are found in ' + error_string +
                        ' Table. Input received:{}'.format(','.join(query_values_list)))
            else:
                # print(result)
                return result
    except:
        raise


def get_data_details(report_id, cmte_id):
    try:
        query_1 = """SELECT cmte_id AS "committeeId", COALESCE(cmte_name,'') AS "committeeName", COALESCE(street_1,'') AS "street1",
                                        COALESCE(street_2,'') AS "street2", COALESCE(city,'') AS "city", COALESCE(state, '') AS "state", COALESCE(zip_code, '') AS "zipCode",
                                        COALESCE(treasurer_last_name, '') AS "treasurerLastName", COALESCE(treasurer_first_name, '') AS "treasurerFirstName",
                                        COALESCE(treasurer_middle_name, '') AS "treasurerMiddleName", COALESCE(treasurer_prefix, '') AS "treasurerPrefix",
                                        COALESCE(treasurer_suffix, '') as "treasurerSuffix"
                                FROM public.committee_master Where cmte_id = %s"""
        values_1 = [cmte_id]
        string_1 = "Committee Master"

        query_2 = """SELECT COALESCE(cmte_addr_chg_flag,'') AS "changeOfAddress", COALESCE(state_of_election,'') AS "electionState",
                                        COALESCE(report_type,'') AS "reportCode", COALESCE(amend_ind,'') AS "amendmentIndicator", COALESCE(election_code,'') AS "electionCode",
                                        COALESCE(qual_cmte_flag,'') AS "qualifiedCommitteeIndicator", COALESCE(to_char(date_of_election,'MM/DD/YYYY'),'') AS "electionDate",
                                        COALESCE(to_char(date_signed,'MM/DD/YYYY'),'') AS "dateSigned"
                                FROM public.form_3x Where report_id = %s and cmte_id = %s AND delete_ind is distinct from 'Y'"""
        values_2 = [report_id, cmte_id]
        string_2 = "Form 3X"

        query_3 = """SELECT COALESCE(amend_number, 0) AS "amendmentNumber", COALESCE(to_char(cvg_start_date,'MM/DD/YYYY'),'') AS "coverageStartDate", COALESCE(to_char(cvg_end_date,'MM/DD/YYYY'),'') AS "coverageEndDate",
                                form_type AS "formType", report_id AS "reportId"
                                FROM public.reports WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'"""
        values_3 = [report_id, cmte_id]
        string_3 = "Reports"
        return {**json_query(query_1, values_1, string_1, False)[0], **json_query(query_2, values_2, string_2, False)[0], **json_query(query_3, values_3, string_3, False)[0]}

    except Exception:
        raise


def get_f3x_summary_details(report_id, cmte_id):
    try:
        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)
        cashOnHandYear = cvg_start_date.year

        colA_query = """SELECT COALESCE(coh_bop, 0.0) AS "6b_cashOnHandBeginning", COALESCE(ttl_receipts_sum_page_per, 0.0) AS "6c_totalReceipts",
                                       COALESCE(subttl_sum_page_per, 0.0) AS "6d_subtotal", COALESCE(ttl_disb_sum_page_per, 0.0) AS "7_totalDisbursements",
                                       COALESCE(coh_cop, 0.0) AS "8_cashOnHandAtClose", COALESCE(debts_owed_to_cmte, 0.0) AS "9_debtsTo",
                                       COALESCE(debts_owed_by_cmte, 0.0) AS "10_debtsBy", COALESCE(indv_item_contb_per, 0.0) AS "11ai_Itemized",
                                       COALESCE(indv_unitem_contb_per, 0.0) AS "11aii_Unitemized", COALESCE(ttl_indv_contb, 0.0) AS "11aiii_Total",
                                       COALESCE(pol_pty_cmte_contb_per_i, 0.0) AS "11b_politicalPartyCommittees", COALESCE(other_pol_cmte_contb_per_i, 0.0) AS "11c_otherPoliticalCommitteesPACs",
                                       COALESCE(ttl_contb_col_ttl_per, 0.0) AS "11d_totalContributions", COALESCE(tranf_from_affiliated_pty_per, 0.0) AS "12_transfersFromAffiliatedOtherPartyCommittees",
                                       COALESCE(all_loans_received_per, 0.0) AS "13_allLoansReceived", COALESCE(loan_repymts_received_per, 0.0) AS "14_loanRepaymentsReceived",
                                       COALESCE(offsets_to_op_exp_per_i, 0.0) AS "15_offsetsToOperatingExpendituresRefunds", COALESCE(fed_cand_contb_ref_per, 0.0) AS "16_refundsOfFederalContributions",
                                       COALESCE(other_fed_receipts_per, 0.0) AS "17_otherFederalReceiptsDividends", COALESCE(tranf_from_nonfed_acct_per, 0.0) AS "18a_transfersFromNonFederalAccount_h3",
                                       COALESCE(tranf_from_nonfed_levin_per, 0.0) AS "18b_transfersFromNonFederalLevin_h5", COALESCE(ttl_nonfed_tranf_per, 0.0) AS "18c_totalNonFederalTransfers",
                                       COALESCE(ttl_receipts_per, 0.0) AS "19_totalReceipts", COALESCE(ttl_fed_receipts_per, 0.0) AS "20_totalFederalReceipts",
                                       COALESCE(shared_fed_op_exp_per, 0.0) AS "21ai_federalShare", COALESCE(shared_nonfed_op_exp_per, 0.0) AS "21aii_nonFederalShare",
                                       COALESCE(other_fed_op_exp_per, 0.0) AS "21b_otherFederalOperatingExpenditures", COALESCE(ttl_op_exp_per, 0.0) AS "21c_totalOperatingExpenditures",
                                       COALESCE(tranf_to_affliliated_cmte_per, 0.0) AS "22_transfersToAffiliatedOtherPartyCommittees", COALESCE(fed_cand_cmte_contb_per, 0.0) AS "23_contributionsToFederalCandidatesCommittees",
                                       COALESCE(indt_exp_per, 0.0) AS "24_independentExpenditures", COALESCE(coord_exp_by_pty_cmte_per, 0.0) AS "25_coordinatedExpenditureMadeByPartyCommittees",
                                       COALESCE(loan_repymts_made_per, 0.0) AS "26_loanRepayments", COALESCE(loans_made_per, 0.0) AS "27_loansMade",
                                       COALESCE(indv_contb_ref_per, 0.0) AS "28a_individualsPersons", COALESCE(pol_pty_cmte_contb_per_ii, 0.0) AS "28b_politicalPartyCommittees",
                                       COALESCE(other_pol_cmte_contb_per_ii, 0.0) AS "28c_otherPoliticalCommittees", COALESCE(ttl_contb_ref_per_i, 0.0) AS "28d_totalContributionsRefunds",
                                       COALESCE(other_disb_per, 0.0) AS "29_otherDisbursements", COALESCE(shared_fed_actvy_fed_shr_per, 0.0) AS "30ai_sharedFederalActivity_h6_fedShare",
                                       COALESCE(shared_fed_actvy_nonfed_per, 0.0) AS "30aii_sharedFederalActivity_h6_nonFed", COALESCE(non_alloc_fed_elect_actvy_per, 0.0) AS "30b_nonAllocable_100_federalElectionActivity",
                                       COALESCE(ttl_fed_elect_actvy_per, 0.0) AS "30c_totalFederalElectionActivity", COALESCE(ttl_disb_per, 0.0) AS "31_totalDisbursements",
                                       COALESCE(ttl_fed_disb_per, 0.0) AS "32_totalFederalDisbursements", COALESCE(ttl_contb_per, 0.0) AS "33_totalContributions",
                                       COALESCE(ttl_contb_ref_per_ii, 0.0) AS "34_totalContributionRefunds", COALESCE(net_contb_per, 0.0) AS "35_netContributions",
                                       COALESCE(ttl_fed_op_exp_per, 0.0) AS "36_totalFederalOperatingExpenditures", COALESCE(offsets_to_op_exp_per_ii, 0.0) AS "37_offsetsToOperatingExpenditures",
                                       COALESCE(net_op_exp_per, 0.0) AS "38_netOperatingExpenditures"
                                FROM public.form_3x Where report_id = %s and cmte_id = %s AND delete_ind is distinct from 'Y'"""

        colB_query = """SELECT COALESCE(coh_begin_calendar_yr, 0.0) AS "6a_cashOnHandJan_1",
                                   COALESCE(ttl_receipts_sum_page_ytd, 0.0) AS "6c_totalReceipts",
                                       COALESCE(subttl_sum_ytd, 0.0) AS "6d_subtotal", COALESCE(ttl_disb_sum_page_ytd, 0.0) AS "7_totalDisbursements",
                                       COALESCE(coh_coy, 0.0) AS "8_cashOnHandAtClose", COALESCE(indv_item_contb_ytd, 0.0) AS "11ai_Itemized",
                                       COALESCE(indv_unitem_contb_ytd, 0.0) AS "11aii_Unitemized", COALESCE(ttl_indv_contb_ytd, 0.0) AS "11aiii_Total",
                                       COALESCE(pol_pty_cmte_contb_ytd_i, 0.0) AS "11b_politicalPartyCommittees", COALESCE(other_pol_cmte_contb_ytd_i, 0.0) AS "11c_otherPoliticalCommitteesPACs",
                                       COALESCE(ttl_contb_col_ttl_ytd, 0.0) AS "11d_totalContributions", COALESCE(tranf_from_affiliated_pty_ytd, 0.0) AS "12_transfersFromAffiliatedOtherPartyCommittees",
                                       COALESCE(all_loans_received_ytd, 0.0) AS "13_allLoansReceived", COALESCE(loan_repymts_received_ytd, 0.0) AS "14_loanRepaymentsReceived",
                                       COALESCE(offsets_to_op_exp_ytd_i, 0.0) AS "15_offsetsToOperatingExpendituresRefunds", COALESCE(fed_cand_cmte_contb_ytd, 0.0) AS "16_refundsOfFederalContributions",
                                       COALESCE(other_fed_receipts_ytd, 0.0) AS "17_otherFederalReceiptsDividends", COALESCE(tranf_from_nonfed_acct_ytd, 0.0) AS "18a_transfersFromNonFederalAccount_h3",
                                       COALESCE(tranf_from_nonfed_levin_ytd, 0.0) AS "18b_transfersFromNonFederalLevin_h5", COALESCE(ttl_nonfed_tranf_ytd, 0.0) AS "18c_totalNonFederalTransfers",
                                       COALESCE(ttl_receipts_ytd, 0.0) AS "19_totalReceipts", COALESCE(ttl_fed_receipts_ytd, 0.0) AS "20_totalFederalReceipts",
                                       COALESCE(shared_fed_op_exp_ytd, 0.0) AS "21ai_federalShare", COALESCE(shared_nonfed_op_exp_ytd, 0.0) AS "21aii_nonFederalShare",
                                       COALESCE(other_fed_op_exp_ytd, 0.0) AS "21b_otherFederalOperatingExpenditures", COALESCE(ttl_op_exp_ytd, 0.0) AS "21c_totalOperatingExpenditures",
                                       COALESCE(tranf_to_affilitated_cmte_ytd, 0.0) AS "22_transfersToAffiliatedOtherPartyCommittees", COALESCE(fed_cand_cmte_contb_ref_ytd, 0.0) AS "23_contributionsToFederalCandidatesCommittees",
                                       COALESCE(indt_exp_ytd, 0.0) AS "24_independentExpenditures", COALESCE(coord_exp_by_pty_cmte_ytd, 0.0) AS "25_coordinatedExpenditureMadeByPartyCommittees",
                                       COALESCE(loan_repymts_made_ytd, 0.0) AS "26_loanRepayments", COALESCE(loans_made_ytd, 0.0) AS "27_loansMade",
                                       COALESCE(indv_contb_ref_ytd, 0.0) AS "28a_individualsPersons", COALESCE(pol_pty_cmte_contb_ytd_ii, 0.0) AS "28b_politicalPartyCommittees",
                                       COALESCE(other_pol_cmte_contb_ytd_ii, 0.0) AS "28c_otherPoliticalCommittees", COALESCE(ttl_contb_ref_ytd_i, 0.0) AS "28d_totalContributionsRefunds",
                                       COALESCE(other_disb_ytd, 0.0) AS "29_otherDisbursements", COALESCE(shared_fed_actvy_fed_shr_ytd, 0.0) AS "30ai_sharedFederalActivity_h6_fedShare",
                                       COALESCE(shared_fed_actvy_nonfed_ytd, 0.0) AS "30aii_sharedFederalActivity_h6_nonFed", COALESCE(non_alloc_fed_elect_actvy_ytd, 0.0) AS "30b_nonAllocable_100_federalElectionActivity",
                                       COALESCE(ttl_fed_elect_actvy_ytd, 0.0) AS "30c_totalFederalElectionActivity", COALESCE(ttl_disb_ytd, 0.0) AS "31_totalDisbursements",
                                       COALESCE(ttl_fed_disb_ytd, 0.0) AS "32_totalFederalDisbursements", COALESCE(ttl_contb_ytd, 0.0) AS "33_totalContributions",
                                       COALESCE(ttl_contb_ref_ytd_ii, 0.0) AS "34_totalContributionRefunds", COALESCE(net_contb_ytd, 0.0) AS "35_netContributions",
                                       COALESCE(ttl_fed_op_exp_ytd, 0.0) AS "36_totalFederalOperatingExpenditures", COALESCE(offsets_to_op_exp_ytd_ii, 0.0) AS "37_offsetsToOperatingExpenditures",
                                       COALESCE(net_op_exp_ytd, 0.0) AS "38_netOperatingExpenditures"
                                        FROM public.form_3x Where report_id = %s and cmte_id = %s AND delete_ind is distinct from 'Y'"""

        values = [report_id, cmte_id]

        return {
            "cashOnHandYear": cashOnHandYear,
            "colA": json_query(colA_query, values, "Form3X", False)[0],
            "colB": json_query(colB_query, values, "Form3X", False)[0]
        }
    except NoOPError:
        raise NoOPError(
            'The Committee ID: {} does not exist in Committee Master Table'.format(cmte_id))
    except Exception:
        raise


def get_transactions(identifier, report_id, cmte_id, back_ref_transaction_id, transaction_id_list):
    try:
        query_1 = """SELECT query_string FROM public.tran_query_string WHERE tran_type_identifier = %s"""
        query_values_list_1 = [identifier]
        # print('identifier: '+ identifier)
        output = json_query(query_1, query_values_list_1,
                            "tran_query_string", False)[0]
        query = output.get('query_string')
        if transaction_id_list:
                query = query + " AND transaction_id in ('{}')".format(
                        "', '".join(transaction_id_list))
        # Addressing no back_ref_transaction_id column in sched_D
        if identifier in list_of_transaction_types_with_no_back_ref:
            query_values_list = [report_id, cmte_id]
        else:
            query_values_list = [report_id, cmte_id,
                back_ref_transaction_id, back_ref_transaction_id]
        error_string = identifier + ". Get all transactions"
        return json_query(query, query_values_list, error_string, True)
    except Exception:
        raise

def get_back_ref_transaction_ids(DB_table, identifier, report_id, cmte_id, transaction_id_list):
    try:
        output = []
        query = """SELECT DISTINCT(back_ref_transaction_id) FROM {} 
            WHERE transaction_type_identifier = %s AND report_id = %s AND cmte_id = %s
            AND transaction_id in ('{}') AND delete_ind is distinct from 'Y'""".format(DB_table, "', '".join(transaction_id_list))
        query_values_list = [identifier, report_id, cmte_id]
        results = json_query(query, query_values_list, DB_table, True)
        for result in results:
            output.append(result['back_ref_transaction_id'])
        return output
    except Exception:
        raise


def get_transaction_type_identifier(DB_table, report_id, cmte_id, transaction_id_list):
        try:
                if transaction_id_list:
                    # Addressing no back_ref_transaction_id column in sched_D
                    # if DB_table in ["public.sched_d", "public.sched_c", "public.sched_h1", "public.sched_h2", "public.sched_h3", "public.sched_h5", "public.sched_l"]:
                    query = """SELECT DISTINCT(transaction_type_identifier) FROM {} WHERE report_id = %s AND cmte_id = %s AND transaction_id in ('{}') AND delete_ind is distinct from 'Y'""".format(
                        DB_table, "', '".join(transaction_id_list))
                    # else:
                    #     query = """SELECT DISTINCT(transaction_type_identifier) FROM {} WHERE report_id = %s AND cmte_id = %s AND transaction_id in ('{}') AND back_ref_transaction_id is NULL AND delete_ind is distinct from 'Y'""".format(
                    #         DB_table, "', '".join(transaction_id_list))
                else:
                    # Addressing no back_ref_transaction_id column in sched_D
                    if DB_table in ["public.sched_d", "public.sched_c", "public.sched_h1", "public.sched_h2", "public.sched_h3", "public.sched_h5", "public.sched_l"]:
                        query = """SELECT DISTINCT(transaction_type_identifier) FROM {} WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""".format(DB_table)
                    else:
                        query = """SELECT DISTINCT(transaction_type_identifier) FROM {} WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id is NULL AND delete_ind is distinct from 'Y'""".format(DB_table)
                query_values_list = [report_id, cmte_id]
                result = json_query(query, query_values_list, DB_table, True)
                # print(result)
                return result
        except Exception as e:
                raise Exception(
                    'The get_transaction_type_identifier function is raising the following error: ' + str(e))


def get_schedules_for_form_type(form_type):
        try:
                query = """SELECT DISTINCT(sched_type) FROM public.forms_and_schedules WHERE form_type = %s AND json_builder_flag IS TRUE"""
                query_values_list = [form_type]
                error_string = "forms_and_schedules"
                result = json_query(query, query_values_list, error_string, False)
                # print(result)
                return result
        except Exception as e:
                raise Exception(
                    'The get_schedules_for_form_type function is raising the following error: ' + str(e))


def get_child_identifer(identifier, form_type):
        try:
              query = """SELECT c.tran_identifier FROM ref_transaction_types p LEFT JOIN ref_transaction_types c ON c.parent_tran_id=p.ref_tran_id WHERE p.tran_identifier = %s AND p.form_type = %s ORDER BY p.line_num,p.ref_tran_id"""
              query_values_list = [identifier, form_type]
              error_string = "ref_transaction_types"
              result = json_query(query, query_values_list, error_string, True)
              # print(result)
              return result
        except Exception as e:
                raise Exception(
                    'The get_child_identifer function is raising the following error:' + str(e))

def get_all_child_transaction_identifers(form_type):
        try:
              output = []
              query = """SELECT p.tran_identifier FROM ref_transaction_types p WHERE p.parent_tran_id IS NOT NULL AND p.form_type = %s ORDER BY p.line_num,p.ref_tran_id"""
              query_values_list = [form_type]
              error_string = "ref_transaction_types"
              results = json_query(query, query_values_list, error_string, True)
              for result in results:
                  output.append(result['tran_identifier'])
              return output
        except Exception as e:
                raise Exception(
                    'The get_all_child_transaction_identifers function is raising the following error:' + str(e))

@api_view(["POST"])
def create_json_builders(request):
    try:
        # import ipdb;ipdb.set_trace()
        # print("request",request)
        MANDATORY_INPUTS = ['report_id', 'call_from'] 
        error_string = ""
        output = {}
        transaction_flag = False

        transaction_id_list = []

        committeeId = request.data.get('committeeId')
        password = request.data.get('password')
        formType = request.data.get('formType')
        newAmendIndicator =  request.data.get('newAmendIndicator')
        report_id =  request.data.get('report_id')
        reportSequence =  request.data.get('reportSequence')
        emailAddress1 =  request.data.get('emailAddress1')
        reportType =  request.data.get('reportType')
        coverageStartDate =  request.data.get('coverageStartDate')
        coverageEndDate =  request.data.get('coverageEndDate')
        originalFECId =  request.data.get('originalFECId')
        backDoorCode =  request.data.get('backDoorCode')
        emailAddress2 =  request.data.get('emailAddress2')
        wait =  request.data.get('wait')

        # Handling Mandatory Inputs required
        
        for field in MANDATORY_INPUTS:
            if field not in request.data or request.data.get(field) in [None, 'null', '', ""]:
                error_string += ','.join(field)
        if error_string != "":
            raise Exception(
                'The following inputs are mandatory for this API: ' + error_string)
        # Assiging data passed through request
        #report_id = request.data.get('report_id')
        call_from = request.data.get('call_from')
        cmte_id = request.user.username
        # Checking for transaction ids in the request
        if 'transaction_id' in request.data and request.data.get('transaction_id'):
            transaction_flag = True
            transaction_id_string = request.data.get(
                'transaction_id').replace(" ", "")
            transaction_id_list = transaction_id_string.split(',')
        # Populating output json with header and data values
        output['header'] = get_header_details()
        output['data'] = get_data_details(report_id, cmte_id)
        # Figuring out the form type
        form_type = output.get('data').get('formType')
        full_form_type = FORMTYPE_FORM_DICT.get(form_type)
        # Figuring out what schedules are to be checked for the form type
        schedule_name_list = get_schedules_for_form_type(full_form_type)
        # List of all the child transactions that need back_ref_transaction_id
        ALL_CHILD_TRANSACTION_TYPES_LIST = get_all_child_transaction_identifers(form_type) 

        # *******************************TEMPORARY MODIFICATION FTO CHECK ONLY SCHED A AND SCHED B TABLES************************************
        schedule_name_list = [
            {'sched_type': 'sched_a'}, {'sched_type': 'sched_b'}, {'sched_type': 'sched_c'}, {'sched_type': 'sched_d'}, {'sched_type': 'sched_e'}, 
            {'sched_type': 'sched_f'}, {'sched_type': 'sched_h4'}, {'sched_type': 'sched_h6'}, {'sched_type': 'sched_c1'}, 
            {'sched_type': 'sched_c2'}, {'sched_type': 'sched_h1'}, {'sched_type': 'sched_h2'}, {'sched_type': 'sched_h3'}, {'sched_type': 'sched_h5'},
            {'sched_type': 'sched_l'}]
        # Adding Summary data to output based on form type
        if form_type == 'F3X' and (not transaction_flag):
            # Iterating through schedules list and populating data into output
            output['data']['summary'] = get_f3x_summary_details(
                report_id, cmte_id)
        if schedule_name_list:
            output['data']['schedules'] = {}
            for schedule_name in schedule_name_list:
                schedule = SCHED_SCHED_CODES_DICT.get(
                    schedule_name.get('sched_type'))
                if schedule:
                    if schedule not in output['data']['schedules']:
                        output['data']['schedules'][schedule] = []
                    DB_table = "public." + schedule_name.get('sched_type')
                    list_identifier = get_transaction_type_identifier(
                        DB_table, report_id, cmte_id, transaction_id_list)
                    print('****')
                    print(list_identifier)
                    for identifier in list_identifier:
                        identifier = identifier.get('transaction_type_identifier')
                        # print(identifier)
                        # Handling transaction id list: Having no child transactions printed if transaction id list is specified
                        # *******************************************
                        # if transaction_id_list:
                        #     child_identifier_list = []
                        # else:
                        child_identifier_list = get_child_identifer(
                                identifier, form_type)
                                # ********************************************
                        # SQL QUERY to get all transactions of the specific identifier
                        if identifier not in ALL_CHILD_TRANSACTION_TYPES_LIST:
                            print('*****')
                            print('parent')
                            parent_transactions = get_transactions(
                                identifier, report_id, cmte_id, None, transaction_id_list)
                            print(parent_transactions)
                        else:
                            # print('here')
                            # Handling transaction id list: getting data for child transactions mentioned in transaction list
                            if transaction_id_list:
                                parent_transactions = []
                                back_ref_tran_id_list = get_back_ref_transaction_ids(
                                    DB_table, identifier, report_id, cmte_id, transaction_id_list)
                                for back_ref_tran_id in back_ref_tran_id_list:
                                    parent_transactions.extend(get_transactions(
                                        identifier, report_id, cmte_id, back_ref_tran_id, transaction_id_list))
                        for transaction in parent_transactions:
                            # print(transaction)
                            if child_identifier_list:
                                for child_identifier in child_identifier_list:
                                    child_identifier = child_identifier.get(
                                        'tran_identifier')
                                    if child_identifier:
                                        child_transactions = get_transactions(
                                            child_identifier, report_id, cmte_id, transaction.get('transactionId'), [])
                                        # print(child_transactions)
                                        if child_transactions:
                                            if 'child' in transaction:
                                                transaction['child'].extend(
                                                    child_transactions)
                                            else:
                                                transaction['child'] = child_transactions
                            if transaction.get('lineNumber') not in EXCLUDED_LINE_NUMBERS_FROM_JSON_LIST:
                                if transaction.get('transactionTypeIdentifier') in list_of_SL_SA_transaction_types:
                                    if 'SL-A' not in output['data']['schedules']:
                                        output['data']['schedules']['SL-A'] = []
                                    output['data']['schedules']['SL-A'].append(transaction)
                                elif transaction.get('transactionTypeIdentifier') in list_of_SL_SB_transaction_types:
                                    if 'SL-B' not in output['data']['schedules']:
                                        output['data']['schedules']['SL-B'] = []
                                    output['data']['schedules']['SL-B'].append(transaction)
                                else:
                                    output['data']['schedules'][schedule].append(transaction)
        up_datetime = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        tmp_filename = cmte_id + '_' + str(report_id)+'_'+str(up_datetime)+'.json'
        tmp_path = '/tmp/'+tmp_filename
        json.dump(output, open(tmp_path, 'w'), indent=4)

        # Transfering the local json file to S3 bucket
        client = boto3.client('s3')
        transfer = S3Transfer(client)
        transfer.upload_file(tmp_path, 'dev-efile-repo', tmp_filename)

        if call_from == "PrintPreviewPDF":
            data_obj = {'form_type': form_type}
            file_obj = {'json_file': ('data.json', open(
                tmp_path, 'rb'), 'application/json')}

            print("data_obj = ", data_obj)
            print("file_obj = ", file_obj)
            resp = requests.post(settings.NXG_FEC_PRINT_API_URL +
                                 settings.NXG_FEC_PRINT_API_VERSION, data=data_obj, files=file_obj)

        elif call_from == "Submit":
            # data_obj = request
            data_obj = {'committeeId': committeeId,
                        'password': password,
                        'formType': formType,
                        'newAmendIndicator': newAmendIndicator,
                        'report_id': report_id,
                        'reportSequence': reportSequence,
                        'emailAddress1': emailAddress1,
                        'reportType': reportType,
                        'coverageStartDate': coverageStartDate,
                        'coverageEndDate': coverageEndDate,
                        'originalFECId': originalFECId,
                        'backDoorCode': backDoorCode,
                        'emailAddress2': emailAddress2,
                        'wait': wait
                        }
            file_obj = {'fecDataFile': ('data.json', open(
                tmp_path, 'rb'), 'application/json')}
            print("data_obj = ", data_obj)
            print("file_obj = ", file_obj)

            add_log(report_id,
                cmte_id, 
                4,
                " create_json_builders calling data Validatior with data_obj", 
                json.dumps(data_obj), 
                '',
                '', 
                '' 
                ) 

            resp = requests.post("http://" + settings.DATA_RECEIVE_API_URL +
                                 "/v1/upload_filing", data=data_obj, files=file_obj)

        if not resp.ok:
            return Response(resp.json(), status=status.HTTP_400_BAD_REQUEST)
        else:
            dictprint = resp.json()
            return JsonResponse(dictprint, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response("The create_json_builders is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

'''
message_type,
 1-FATAL, 2-ERROR, 3-WARN, 4-INFO, 5-DEBUG, 6-TRACE
'''
def add_log(reportid, 
            cmte_id, 
            message_type, 
            message_text, 
            response_json, 
            error_code, 
            error_json, 
            app_error,
            host_name=os.uname()[1],
            process_name="create_json_builders"):

     with connection.cursor() as cursor:
        cursor.execute("""INSERT INTO public.upload_logs(
                                        report_id, 
                                        cmte_id, 
                                        process_name, 
                                        message_type, 
                                        message_text, 
                                        response_json, 
                                        error_code, 
                                        error_json, 
                                        app_error, 
                                        host_name)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                        [reportid, cmte_id, process_name, message_type, message_text, response_json, error_code, error_json, app_error, host_name])

