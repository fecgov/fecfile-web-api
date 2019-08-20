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
        # 'sched_c': 'SC',
        # 'sched_c1': 'SC1',
        # 'sched_c2': 'SC2',
        # 'sched_d': 'SD',
        # 'sched_e': 'SE',
        # 'sched_f': 'SF',
        # 'sched_h1': 'SH1',
        # 'sched_h2': 'SH2',
        # 'sched_h3': 'SH3',
        # 'sched_h4': 'SH4',
        # 'sched_h5': 'SH5',
        # 'sched_h6': 'SH6',
        # 'sched_l': 'SL',

}
# Dictionary that maps form type to the schedules that it should include
FORMTYPE_SCHEDULES_DICT = {
    'F3X': ['SA', 'SB']
}

# Dictionary mapping schedules to DB table name
SCHEDULES_DBTABLES_DICT = {
    'SA': 'public.sched_a',
    'SB': 'public.sched_b'
}

# Dictionary that excludes line numbers from final json
EXCLUDED_LINE_NUMBERS_FROM_JSON_LIST = ['11AII']


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
            cursor.execute(sql_query, query_values_list)
            # print(cursor.query.decode("utf-8"))
            result = cursor.fetchone()[0]
            if result is None:
                # TO Handle zero transactions in sched_a or sched_b for a specific transaction_type_identifer using this condition
                if empty_list_flag:
                        return []
                else:
                                raise NoOPError('No results are found in' + error_string +
                                                'Table. Input received:{}'.format(','.join(query_values_list)))
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
    # except Exception:
    #     raise


def get_transactions(identifier, report_id, cmte_id, back_ref_transaction_id, transaction_id_list):
    try:
        query_1 = """SELECT query_string FROM public.tran_query_string WHERE tran_type_identifier = %s"""
        query_values_list_1 = [identifier]
        output = json_query(query_1, query_values_list_1,
                            "tran_query_string", False)[0]
        query = output.get('query_string')
        if transaction_id_list:
                query = query + \
                    " AND transaction_id in ('{}')".format(
                        "', '".join(transaction_id_list))
        query_values_list = [report_id, cmte_id,
            back_ref_transaction_id, back_ref_transaction_id]
        error_string = "SCHED_A. Get all transactions"
        return json_query(query, query_values_list, error_string, True)
    except Exception:
        raise


def get_transaction_type_identifier(DB_table, report_id, cmte_id, transaction_id_list):
        try:
                if transaction_id_list:
                        query = """SELECT DISTINCT(transaction_type_identifier) FROM {} WHERE report_id = %s AND cmte_id = %s AND transaction_id in ('{}') AND back_ref_transaction_id is NULL AND delete_ind is distinct from 'Y'""".format(
                            DB_table, "', '".join(transaction_id_list))
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


@api_view(["POST"])
def create_json_builders(request):
    try:
        MANDATORY_INPUTS = ['report_id', 'call_from']
        error_string = ""
        output = {}
        transaction_flag = False

        transaction_id_list = []
        # Handling Mandatory Inputs required
        for field in MANDATORY_INPUTS:
            if field not in request.data or request.data.get(field) in [None, 'null', '', ""]:
                error_string += ','.join(field)
        if error_string != "":
            raise Exception(
                'The following inputs are mandatory for this API: ' + error_string)
        # Assiging data passed through request
        report_id = request.data.get('report_id')
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

        # *******************************TEMPORARY MODIFICATION FTO CHECK ONLY SCHED A AND SCHED B TABLES************************************
        schedule_name_list = [
            {'sched_type': 'sched_a'}, {'sched_type': 'sched_b'}]
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
                output['data']['schedules'][schedule] = []
                DB_table = "public." + schedule_name.get('sched_type')
                list_identifier = get_transaction_type_identifier(
                    DB_table, report_id, cmte_id, transaction_id_list)
                for identifier in list_identifier:
                        identifier = identifier.get('transaction_type_identifier')
                        child_identifier_list = get_child_identifer(
                            identifier, form_type)
                        # SQL QUERY to get all transactions of the specific identifier
                        if identifier:
                            parent_transactions = get_transactions(
                                identifier, report_id, cmte_id, None, transaction_id_list)
                            for transaction in parent_transactions:
                                if child_identifier_list:
                                    for child_identifier in child_identifier_list:
                                        child_identifier = child_identifier.get(
                                            'tran_identifier')
                                        if child_identifier:
                                                child_transactions = get_transactions(
                                                    child_identifier, report_id, cmte_id, transaction.get('transactionId'), transaction_id_list)
                                                # print(child_transactions)
                                                if child_transactions:
                                                    if 'child' in transaction:
                                                        transaction['child'].extend(
                                                            child_transactions)
                                                    else:
                                                        transaction['child'] = child_transactions
                                if transaction.get('lineNumber') not in EXCLUDED_LINE_NUMBERS_FROM_JSON_LIST:
                                        output['data']['schedules'][schedule].append(
                                            transaction)
        up_datetime = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        tmp_filename = cmte_id + '_' + \
            str(report_id)+'_'+str(up_datetime)+'.json'
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
            data_obj = {'committeeId': request.data.get('committeeId'),
                        'password': request.data.get('password'),
                        'formType': request.data.get('formType'),
                        'newAmendIndicator': request.data.get('newAmendIndicator'),
                        'report_id': request.data.get('report_id'),
                        'reportSequence': request.data.get('reportSequence'),
                        'emailAddress1': request.data.get('emailAddress1'),
                        'reportType': request.data.get('reportType'),
                        'coverageStartDate': request.data.get('coverageStartDate'),
                        'coverageEndDate': request.data.get('coverageEndDate'),
                        'originalFECId': request.data.get('originalFECId'),
                        'backDoorCode': request.data.get('backDoorCode'),
                        'emailAddress2': request.data.get('emailAddress2'),
                        'wait': request.data.get('wait')
                        }
            file_obj = {'fecDataFile': ('data.json', open(
                tmp_path, 'rb'), 'application/json')}
            print("data_obj = ", data_obj)
            print("file_obj = ", file_obj)

            resp = requests.post("http://" + settings.DATA_RECEIVE_API_URL +
                                 "/v1/upload_filing", data=data_obj, files=file_obj)

        if not resp.ok:
            return Response(resp.json(), status=status.HTTP_400_BAD_REQUEST)
        else:
            dictprint = resp.json()
            return JsonResponse(dictprint, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response("The create_json_builders is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def sample_sql_generate(request):
        try:
                List_SA_similar_INDV_REC = ["INDV_REC", "PARTN_MEMO", "IK_REC", "REATT_FROM", "REATT_MEMO", "RET_REC", "EAR_REC",
                            "CON_EAR_UNDEP", "CON_EAR_DEP", "IND_RECNT_REC", "IND_NP_RECNT_ACC", "IND_NP_HQ_ACC", "IND_NP_CONVEN_ACC",
                            "IND_REC_NON_CONT_ACC", "JF_TRAN_IND_MEMO", "JF_TRAN_NP_RECNT_IND_MEMO", "JF_TRAN_NP_CONVEN_IND_MEMO",
                            "JF_TRAN_NP_HQ_IND_MEMO", "EAR_REC_RECNT_ACC", "EAR_REC_CONVEN_ACC", "EAR_REC_HQ_ACC"]
                INDV_REC_STRING = ""
                for tran in List_SA_similar_INDV_REC:

                        query = """SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.contribution_date,''MM/DD/YYYY'') AS "contributionDate", t1.contribution_amount AS "contributionAmount", COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                        COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.last_name, '''') AS "contributorLastName", COALESCE(t2.first_name, '''') AS "contributorFirstName",
                        COALESCE(t2.middle_name, '''') AS "contributorMiddleName", COALESCE(t2.preffix, '''') AS "contributorPrefix", COALESCE(t2.suffix, '''') AS "contributorSuffix",
                        COALESCE(t2.street_1, '''') AS "contributorStreet1", COALESCE(t2.street_2, '''') AS "contributorStreet2", COALESCE(t2.city, '''') AS "contributorCity",
                        COALESCE(t2.state, '''') AS "contributorState", COALESCE(t2.zip_code, '''') AS "contributorZipCode", COALESCE(t2.employer, '''') AS "contributorEmployer",
                        COALESCE(t2.occupation, '''') AS "contributorOccupation"
                        FROM public.sched_a t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                        INDV_REC_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SA')
#                       INDV_REC_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/indv_rec_sql.sql", 'w')
                file.write(INDV_REC_STRING)
                file.close()

                list_SA_similar_PAR_CON = ["PARTN_REC", "TRIB_REC", "TRIB_NP_RECNT_ACC", "TRIB_NP_HQ_ACC", "TRIB_NP_CONVEN_ACC",
                            "BUS_LAB_NON_CONT_ACC", "JF_TRAN_TRIB_MEMO", "JF_TRAN_NP_RECNT_TRIB_MEMO", "JF_TRAN_NP_CONVEN_TRIB_MEMO",
                            "JF_TRAN_NP_HQ_TRIB_MEMO"]
                PAR_CON_STRING = ""
                for tran in list_SA_similar_PAR_CON:

                        query = """
                        SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.contribution_date,''MM/DD/YYYY'') AS "contributionDate", t1.contribution_amount AS "contributionAmount", COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                        COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "contributorOrgName",
                        COALESCE(t2.street_1, '''') AS "contributorStreet1", COALESCE(t2.street_2, '''') AS "contributorStreet2", COALESCE(t2.city, '''') AS "contributorCity",
                        COALESCE(t2.state, '''') AS "contributorState", COALESCE(t2.zip_code, '''') AS "contributorZipCode"
                        FROM public.sched_a t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        PAR_CON_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SA')
#                       PAR_CON_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/par_con_sql.sql", 'w')
                file.write(PAR_CON_STRING)
                file.close()

                list_SA_similar_COND_EARM_PAC = ["EAR_MEMO", "PAC_CON_EAR_UNDEP", "PAC_CON_EAR_DEP", "PAC_EAR_REC", "PAC_EAR_MEMO", "PARTY_IK_REC", "PAC_IK_REC", "PARTY_REC",
                                "PAC_REC", "PAC_NON_FED_REC", "PAC_NON_FED_RET", "PAC_RET", "PARTY_RET", "TRAN", "PARTY_RECNT_REC", "PAC_RECNT_REC",
                                "TRIB_RECNT_REC", "PARTY_NP_RECNT_ACC", "PAC_NP_RECNT_ACC",
                                "PARTY_NP_HQ_ACC", "PAC_NP_HQ_ACC", "PARTY_NP_CONVEN_ACC", "PAC_NP_CONVEN_ACC", "OTH_CMTE_NON_CONT_ACC", "IK_TRAN", "IK_TRAN_FEA",
                                "JF_TRAN", "JF_TRAN_PARTY_MEMO", "JF_TRAN_PAC_MEMO",
                                "JF_TRAN_NP_RECNT_ACC", "JF_TRAN_NP_RECNT_PAC_MEMO", "JF_TRAN_NP_CONVEN_ACC", "JF_TRAN_NP_CONVEN_PAC_MEMO", "JF_TRAN_NP_HQ_ACC",
                                "JF_TRAN_NP_HQ_PAC_MEMO", "EAR_REC_RECNT_ACC_MEMO", "EAR_REC_CONVEN_ACC_MEMO", "EAR_REC_HQ_ACC_MEMO"]
                COND_EARM_PAC_STRING = ""
                for tran in list_SA_similar_COND_EARM_PAC:

                        query = """
                        SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.contribution_date,''MM/DD/YYYY'') AS "contributionDate", t1.contribution_amount AS "contributionAmount", COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                        COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", COALESCE(t1.donor_cmte_id, '''') AS "donorCommitteeId", COALESCE(t1.donor_cmte_name, '''') AS "donorCommitteeName",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "contributorOrgName",
                        COALESCE(t2.street_1, '''') AS "contributorStreet1", COALESCE(t2.street_2, '''') AS "contributorStreet2", COALESCE(t2.city, '''') AS "contributorCity",
                        COALESCE(t2.state, '''') AS "contributorState", COALESCE(t2.zip_code, '''') AS "contributorZipCode"
                        FROM public.sched_a t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        COND_EARM_PAC_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SA')
#                       COND_EARM_PAC_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/con_earm_sql.sql", 'w')
                file.write(COND_EARM_PAC_STRING)
                file.close()

                list_SA_similar_OFFSET = ["OFFSET_TO_OPEX"]
                list_SA_similar_REF_FED_CAN = ["REF_TO_FED_CAN"]
                list_SA_similar_OTH_REC = ["OTH_REC"]
                list_SA_similar_REF_NFED_CAN = ["REF_TO_OTH_CMTE"]

                SA_OTHER_STRING = ""
                for tran in list_SA_similar_OFFSET:

                        query = """
                        SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.contribution_date,''MM/DD/YYYY'') AS "contributionDate", t1.contribution_amount AS "contributionAmount", COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                        COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "contributorOrgName", COALESCE(t2.last_name, '''') AS "contributorLastName", COALESCE(t2.first_name, '''') AS "contributorFirstName",
                        COALESCE(t2.middle_name, '''') AS "contributorMiddleName", COALESCE(t2.preffix, '''') AS "contributorPrefix", COALESCE(t2.suffix, '''') AS "contributorSuffix",
                        COALESCE(t2.street_1, '''') AS "contributorStreet1", COALESCE(t2.street_2, '''') AS "contributorStreet2", COALESCE(t2.city, '''') AS "contributorCity",
                        COALESCE(t2.state, '''') AS "contributorState", COALESCE(t2.zip_code, '''') AS "contributorZipCode"
                        FROM public.sched_a t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        SA_OTHER_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SA')
#                       SA_OTHER_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SA_similar_OTH_REC:

                        query = """
                        SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.contribution_date,''MM/DD/YYYY'') AS "contributionDate", t1.contribution_amount AS "contributionAmount", COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                        COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "contributorOrgName", COALESCE(t2.last_name, '''') AS "contributorLastName", COALESCE(t2.first_name, '''') AS "contributorFirstName",
                        COALESCE(t2.middle_name, '''') AS "contributorMiddleName", COALESCE(t2.preffix, '''') AS "contributorPrefix", COALESCE(t2.suffix, '''') AS "contributorSuffix",
                        COALESCE(t2.street_1, '''') AS "contributorStreet1", COALESCE(t2.street_2, '''') AS "contributorStreet2", COALESCE(t2.city, '''') AS "contributorCity",
                        COALESCE(t2.state, '''') AS "contributorState", COALESCE(t2.zip_code, '''') AS "contributorZipCode", COALESCE(t2.employer, '''') AS "contributorEmployer",
                        COALESCE(t2.occupation, '''') AS "contributorOccupation"
                        FROM public.sched_a t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        SA_OTHER_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SA')
#                       SA_OTHER_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SA_similar_REF_NFED_CAN:

                        query = """
                        SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.contribution_date,''MM/DD/YYYY'') AS "contributionDate", t1.contribution_amount AS "contributionAmount", COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                        COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", COALESCE(t1.election_code, '''') AS "electionCode",
                        COALESCE(t1.election_other_description, '''') AS "electionOtherDescription",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "contributorOrgName",
                        COALESCE(t2.street_1, '''') AS "contributorStreet1", COALESCE(t2.street_2, '''') AS "contributorStreet2", COALESCE(t2.city, '''') AS "contributorCity",
                        COALESCE(t2.state, '''') AS "contributorState", COALESCE(t2.zip_code, '''') AS "contributorZipCode"
                        FROM public.sched_a t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        SA_OTHER_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SA')
#                       SA_OTHER_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SA_similar_REF_FED_CAN:

                        query = """
                        SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.contribution_date,''MM/DD/YYYY'') AS "contributionDate", t1.contribution_amount AS "contributionAmount", COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                        COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription",  COALESCE(t1.donor_cmte_id, '''') AS "donorCommitteeId", COALESCE(t1.donor_cmte_name, '''') AS "donorCommitteeName",
                        COALESCE(t1.election_code, '''') AS "electionCode", COALESCE(t1.election_other_description, '''') AS "electionOtherDescription",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "contributorOrgName",
                        COALESCE(t2.street_1, '''') AS "contributorStreet1", COALESCE(t2.street_2, '''') AS "contributorStreet2", COALESCE(t2.city, '''') AS "contributorCity",
                        COALESCE(t2.state, '''') AS "contributorState", COALESCE(t2.zip_code, '''') AS "contributorZipCode"
                        FROM public.sched_a t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        SA_OTHER_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SA')
#                       SA_OTHER_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/sa_oth_sql.sql", 'w')
                file.write(SA_OTHER_STRING)
                file.close()

                list_SB_similar_IK_OUT = ["IK_OUT"]
                list_SB_similar_IK_TF_OUT = ["IK_TRAN_OUT", "IK_TRAN_FEA_OUT"]
                list_SB_similar_EAR_OUT = ["CON_EAR_UNDEP_MEMO", "CON_EAR_DEP_MEMO",
                    "PAC_CON_EAR_UNDEP_MEMO", "PAC_CON_EAR_DEP_OUT"]
                list_SB_similar_IK_OUT_PTY = ["PARTY_IK_OUT", "PAC_IK_OUT"]

                SB_SA_CHILD_STRING = ""
                for tran in list_SB_similar_IK_OUT:

                        query = """
                        SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", t1.expenditure_amount AS "expenditureAmount",
                        COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription", COALESCE(t1.category_code, '''') AS "categoryCode",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.last_name, '''') AS "payeeLastName", COALESCE(t2.first_name, '''') AS "payeeFirstName",
                        COALESCE(t2.middle_name, '''') AS "payeeMiddleName", COALESCE(t2.preffix, '''') AS "payeePrefix", COALESCE(t2.suffix, '''') AS "payeeSuffix",
                        COALESCE(t2.street_1, '''') AS "payeeStreet1", COALESCE(t2.street_2, '''') AS "payeeStreet2", COALESCE(t2.city, '''') AS "payeeCity",
                        COALESCE(t2.state, '''') AS "payeeState", COALESCE(t2.zip_code, '''') AS "payeeZipCode"
                        FROM public.sched_b t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                        SB_SA_CHILD_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SB')
#                       SB_SA_CHILD_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SB', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SB_similar_IK_TF_OUT:

                        query = """
                        SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", t1.expenditure_amount AS "expenditureAmount",
                        COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription", COALESCE(t1.category_code, '''') AS "categoryCode",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "payeeOrgName",
                        COALESCE(t2.street_1, '''') AS "payeeStreet1", COALESCE(t2.street_2, '''') AS "payeeStreet2", COALESCE(t2.city, '''') AS "payeeCity",
                        COALESCE(t2.state, '''') AS "payeeState", COALESCE(t2.zip_code, '''') AS "payeeZipCode"
                        FROM public.sched_b t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        SB_SA_CHILD_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SB')
#                       SB_SA_CHILD_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SB', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SB_similar_EAR_OUT:

                        query = """
                        SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", t1.expenditure_amount AS "expenditureAmount",
                        COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription", COALESCE(t1.category_code, '''') AS "categoryCode",
                        COALESCE(t1.election_code, '''') AS "electionCode", COALESCE(t1.election_other_description, '''') AS "electionOtherDescription",
                        COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                        COALESCE(t1.beneficiary_cand_id, '''') AS "beneficiaryCandidateId",
                        COALESCE(t3.cand_last_name, '''') AS "beneficiaryCandidateLastName",
                        COALESCE(t3.cand_first_name, '''') AS "beneficiaryCandidateFirstName",
                        COALESCE(t3.cand_middle_name, '''') AS "beneficiaryCandidateMiddleName",
                        COALESCE(t3.cand_prefix, '''') AS "beneficiaryCandidatePrefix",
                        COALESCE(t3.cand_suffix, '''') AS "beneficiaryCandidateSuffix",
                        COALESCE(t3.cand_office, '''') AS "beneficiaryCandidateOffice",
                        COALESCE(t3.cand_office_state, '''') AS "beneficiaryCandidateState",
                        COALESCE(t3.cand_office_district, '''') AS "beneficiaryCandidateDistrict",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "payeeOrgName",
                        COALESCE(t2.street_1, '''') AS "payeeStreet1", COALESCE(t2.street_2, '''') AS "payeeStreet2", COALESCE(t2.city, '''') AS "payeeCity",
                        COALESCE(t2.state, '''') AS "payeeState", COALESCE(t2.zip_code, '''') AS "payeeZipCode"
                        FROM public.sched_b t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        LEFT JOIN public.candidate_master t3 ON t3.cand_id = t3.beneficiary_cand_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        SB_SA_CHILD_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SB')
#                       SB_SA_CHILD_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SB', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SB_similar_IK_OUT_PTY:

                        query = """
                        SELECT t1.line_number AS "lineNumber", t1.transaction_type AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", t1.expenditure_amount AS "expenditureAmount", COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                        COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription", COALESCE(t1.category_code, '''') AS "categoryCode",
                        COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "payeeOrgName",
                        COALESCE(t2.street_1, '''') AS "payeeStreet1", COALESCE(t2.street_2, '''') AS "payeeStreet2", COALESCE(t2.city, '''') AS "payeeCity",
                        COALESCE(t2.state, '''') AS "payeeState", COALESCE(t2.zip_code, '''') AS "payeeZipCode"
                        FROM public.sched_b t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        SB_SA_CHILD_STRING += """
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        AND form_type = '{2}' AND sched_type = '{3}';\n
                        """.format(query, tran, 'F3X', 'SB')
#                       SB_SA_CHILD_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
# VALUES ('F3X', 'SB', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/sb_sa_child_sql.sql", 'w')
                file.write(SB_SA_CHILD_STRING)
                file.close()

                file = open("/tmp/SA_sql.sql", 'w')
                file.write(INDV_REC_STRING)
                file.write(SB_SA_CHILD_STRING)
                file.write(PAR_CON_STRING)
                file.write(COND_EARM_PAC_STRING)
                file.write(SA_OTHER_STRING)
                file.write(SB_SA_CHILD_STRING)
                file.close()

                List_SB_similar_OPEX_REC = ['OPEXP','OPEXP_CC_PAY_MEMO', 'OPEXP_STAF_REIM', 'OPEXP_STAF_REIM_MEMO'] 

                OPEX_REC_STRING = ""
                for tran in List_SB_similar_OPEX_REC:
                        query = """SELECT t1.line_number AS "lineNumber", 
                        t1.transaction_type AS "transactionTypeCode",
                        t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                        COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        COALESCE(t2.entity_type, '''') AS "entityType", 
                        COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                        COALESCE(t2.last_name, '''') AS "payeeLastName", 
                        COALESCE(t2.first_name, '''') AS "payeeFirstName",
                        COALESCE(t2.middle_name, '''') AS "payeeMiddleName", 
                        COALESCE(t2.preffix, '''') AS "payeePrefix", 
                        COALESCE(t2.suffix, '''') AS "payeeSuffix",
                        COALESCE(t2.street_1, '''') AS "payeeStreet1", 
                        COALESCE(t2.street_2, '''') AS "payeeStreet2", 
                        COALESCE(t2.city, '''') AS "payeeCity",
                        COALESCE(t2.state, '''') AS "payeeState", 
                        COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                        to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", 
                        t1.expenditure_amount AS "expenditureAmount",
                        COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                        COALESCE(t1.memo_code, '''') AS "memoCode", 
                        COALESCE(t1.memo_text, '''') AS "memoDescription"
                        FROM public.sched_b t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                        OPEX_REC_STRING +="""
                        UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}' 
                        AND form_type = '{2}' AND sched_type = '{3}';\n""".format(query, tran, 'F3X', 'SB')

                file = open("/tmp/opex_rec_sql.sql", 'w')
                file.write(OPEX_REC_STRING)
                file.close()

                file = open("/tmp/SB_sql.sql", 'w')
                file.write(OPEX_REC_STRING)

                return Response('Success', status=status.HTTP_201_CREATED)
        except Exception as e:
                return Response('Error: ' + str(e), status=status.HTTP_400_BAD_REQUEST)
