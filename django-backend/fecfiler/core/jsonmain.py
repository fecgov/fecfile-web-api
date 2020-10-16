from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
import maya
from .models import Cmte_Report_Types_View, My_Forms_View  # , GenericDocument
from rest_framework.response import Response
from fecfiler.forms.models import CommitteeInfo
from fecfiler.forms.serializers import CommitteeInfoSerializer
from fecfiler.core.views import submit_report
import json
import datetime
import os
import platform
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
import time
from fecfiler.core.views import (get_list_entity, NoOPError, get_cvg_dates, get_comittee_id)

# conn = boto.connect_s3()

# Dictionary mapping form type value to form type in forms_and_schedules table
FORMTYPE_FORM_DICT = {
    'F3X': 'form_3x',
    'F24': 'form_24',
    'F3L': 'form_3l'
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
list_of_transaction_types_with_no_back_ref = ['DEBT_TO_VENDOR', 'LOANS_OWED_TO_CMTE', 'LOANS_OWED_BY_CMTE', 'ALLOC_H1',
                                              'ALLOC_H2_RATIO', 'TRAN_FROM_NON_FED_ACC', 'TRAN_FROM_LEVIN_ACC',
                                              'SCHED_L_SUM']

list_of_SL_SA_transaction_types = ['LEVIN_TRIB_REC', 'LEVIN_PARTN_REC', 'LEVIN_ORG_REC', 'LEVIN_INDV_REC',
                                   'LEVIN_NON_FED_REC', 'LEVIN_OTH_REC', 'LEVIN_PAC_REC']

list_of_SL_SB_transaction_types = ['LEVIN_VOTER_ID', 'LEVIN_GOTV', 'LEVIN_GEN', 'LEVIN_OTH_DISB', 'LEVIN_VOTER_REG']

DICT_PURPOSE_DESCRIPTION_VALUES = {
    'Bounced': ['PARTY_RET', 'PAC_RET', 'RET_REC'],
    'Convention Account': ['IND_NP_CONVEN_ACC', 'PAC_NP_CONVEN_ACC', 'PARTY_NP_CONVEN_ACC', 'TRIB_NP_CONVEN_ACC',
                           'OPEXP_CONV_ACC_OP_EXP_NP'],
    'Convention Account Earmarked Through': ['EAR_REC_CONVEN_ACC'],
    'Convention Account - JF Memo for': ['JF_TRAN_NP_CONVEN_IND_MEMO', 'JF_TRAN_NP_CONVEN_PAC_MEMO',
                                         'JF_TRAN_NP_CONVEN_TRIB_MEMO'],
    'Convention: Refund': ['OPEXP_CONV_ACC_TRIB_REF', 'OPEXP_CONV_ACC_IND_REF'],
    'Credit Card Payment': ['IE_CC_PAY_MEMO'],
    'Credit Card: See Below': ['IE_CC_PAY'],
    'Earmark for': ['PAC_CON_EAR_DEP', 'PAC_CON_EAR_UNDEP'],
    'Earmarked for': ['CON_EAR_DEP', 'CON_EAR_UNDEP', 'CON_EAR_UNDEP_BKP', 'CON_EAR_UNDEP_BKP'],
    'Earmarked from': ['CON_EAR_DEP_MEMO', 'CON_EAR_UNDEP_MEMO', 'PAC_CON_EAR_UNDEP_MEMO', 'PAC_CON_EAR_DEP_MEMO'],
    'Earmarked through': ['EAR_REC', 'PAC_EAR_REC'],
    'Headquarters Account Earmarked Through': ['EAR_REC_HQ_ACC'],
    'Headquarters Account': ['IND_NP_HQ_ACC', 'PAC_NP_HQ_ACC', 'PARTY_NP_HQ_ACC', 'TRIB_NP_HQ_ACC'],
    'Headquarters Account - JF Memo for': ['JF_TRAN_NP_HQ_IND_MEMO', 'JF_TRAN_NP_HQ_PAC_MEMO',
                                           'JF_TRAN_NP_HQ_TRIB_MEMO'],
    'Headquarters: Refund': ['OPEXP_HQ_ACC_TRIB_REF', 'OPEXP_HQ_ACC_IND_REF'],
    'In-kind': ['IK_REC', 'IK_TRAN', 'IK_TRAN_FEA', 'PAC_IK_BC_OUT', 'PAC_IK_BC_REC', 'PAC_IK_REC', 'PARTY_IK_BC_OUT',
                'PARTY_IK_REC'],
    'JF Memo for': ['JF_TRAN_IND_MEMO', 'JF_TRAN_PAC_MEMO', 'JF_TRAN_PARTY_MEMO', 'JF_TRAN_TRIB_MEMO'],
    'JF Transfer': ['JF_TRAN'],
    'JF Transfer Convention Account': ['JF_TRAN_NP_CONVEN_ACC'],
    'JF Transfer Headquarters Account': ['JF_TRAN_NP_HQ_ACC'],
    'JF Transfer Recount Account': ['JF_TRAN_NP_RECNT_ACC'],
    'Loan From Ind': ['LOAN_FROM_IND'],
    'Non-Contribution Account Receipt': ['BUS_LAB_NON_CONT_ACC', 'IND_REC_NON_CONT_ACC', 'OTH_CMTE_NON_CONT_ACC'],
    'Non-Contribution Account': ['OTH_DISB_NC_ACC', 'OTH_DISB_NC_ACC_STAF_REIM', 'OTH_DISB_NC_ACC_CC_PAY',
                                 'OTH_DISB_NC_ACC_PMT_TO_PROL',
                                 'OTH_DISB_NC_ACC_PMT_TO_PROL_MEMO', 'OTH_DISB_NC_ACC_CC_PAY_MEMO',
                                 'OTH_DISB_NC_ACC_STAF_REIM_MEMO'],
    'Partnership Memo': ['LEVIN_PARTN_MEMO', 'PARTN_MEMO'],
    'Payroll: See Below': ['IE_PMT_TO_PROL'],
    'Recount Account': ['IND_NP_RECNT_ACC', 'PAC_NP_RECNT_ACC', 'PARTY_NP_RECNT_ACC', 'TRIB_NP_RECNT_ACC'],
    'Recount Account - JF Memo for': ['JF_TRAN_NP_RECNT_PAC_MEMO', 'JF_TRAN_NP_RECNT_TRIB_MEMO',
                                      'JF_TRAN_NP_RECNT_IND_MEMO'],
    'Recount Account Earmarked Through': ['EAR_REC_RECNT_ACC'],
    'Recount Receipt': ['IND_RECNT_REC', 'PAC_RECNT_REC', 'PARTY_RECNT_REC', 'TRIB_RECNT_REC'],
    'Recount: Refund': ['OTH_DISB_NP_RECNT_TRIB_REF', 'OTH_DISB_NP_RECNT_REG_REF', 'OTH_DISB_NP_RECNT_IND_REF'],
    'Recount: Purpose of Disbursement': ['OTH_DISB_RECNT'],
    # 'Reimbursement: See Below': ['IE_STAF_REIM'],
    'Return/Void': ['PAC_NON_FED_RET', 'PAC_RET'],
    'See Memos Below': ['LEVIN_PARTN_REC', 'PARTN_REC'],
    # Removing 'EAR_MEMO' from below as it being populated from front-end
    # 'Total Earmarked through Conduit': ['EAR_REC_CONVEN_ACC_MEMO', 'EAR_REC_HQ_ACC_MEMO', 'EAR_REC_RECNT_ACC_MEMO',
    #                                     'PAC_EAR_MEMO'],
    'Staff Reimbursement Memo': ['COEXP_STAF_REIM_MEMO']
}

logger = logging.getLogger(__name__)


def get_header_details():
    return {
        "version": "8.3",
        "softwareName": "ABC Inc",
        "softwareVersion": "1.02 Beta",
        "additionalInformation": "Any other useful information"
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


"""
***************************** CANDIDATE DETAILS API *************************************
"""


def get_candidate_details_jsonbuilder(request_dict):
    try:
        if request_dict.get('establishmentStatus') == 'Q':
            output_list = []
            for i in range(1, 6):
                column_name = 'can' + str(i) + '_id'
                candidate_id = request_dict.get(column_name)
                if candidate_id:
                    candidate_dict = get_sql_candidate_jsonbuilder(candidate_id)
                    candidate_dict['contributionDate'] = request_dict.get(column_name[:-2] + 'con')
                    candidate_dict['candidateNumber'] = i
                    output_list.append(candidate_dict)
                del request_dict[column_name]
                del request_dict[column_name[:-2] + 'con']
            request_dict['candidates'] = output_list
        return request_dict
    except Exception as e:
        raise Exception(
            'The get_candidate_details_jsonbuilder function is throwing an error: ' + str(e))


def get_sql_candidate_jsonbuilder(candidate_id):
    try:
        sql = """SELECT cand_id AS "candidateId", cand_last_name AS "candidateLastName", cand_first_name AS "candidateFirstName", 
    cand_middle_name AS "candidateMiddleName", cand_prefix AS "candidatePrefix", cand_suffix AS "candidateSuffix", 
    cand_office AS "candidateOffice", cand_office_state AS "candidateState", 
    cand_office_district AS "candidateDistrict" FROM public.candidate_master WHERE cand_id=%s"""
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM ({}) AS t""".format(sql), [candidate_id])
            logger.debug("CANDIDATE TABLE")
            logger.debug(cursor.query)
            output_dict = cursor.fetchone()[0]
            if output_dict:
                return output_dict[0]
            else:
                raise Exception("""The candidateId: {} does not exist in 
          candidate table.""".format(candidate_id))
    except Exception as e:
        raise Exception(
            'The get_sql_candidate_jsonbuilder function is throwing an error: ' + str(e))


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

        query_3 = """SELECT COALESCE(amend_number, 0) AS "amendmentNumber", COALESCE(to_char(cvg_start_date,'MM/DD/YYYY'),'') AS "coverageStartDate", COALESCE(to_char(cvg_end_date,'MM/DD/YYYY'),'') AS "coverageEndDate",
                                form_type AS "formType", report_id AS "reportId", memo_text as "memoText" 
                                FROM public.reports WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'"""
        values_3 = [report_id, cmte_id]
        string_3 = "Reports"

        output = {**json_query(query_1, values_1, string_1, False)[0],
                  **json_query(query_3, values_3, string_3, False)[0]}

        if output['formType'] == 'F3X':
            query_2 = """SELECT COALESCE(cmte_addr_chg_flag,'') AS "changeOfAddress", COALESCE(state_of_election,'') AS "electionState",
                                            COALESCE(report_type,'') AS "reportCode", COALESCE(amend_ind,'') AS "amendmentIndicator", COALESCE(election_code,'') AS "electionCode",
                                            COALESCE(qual_cmte_flag,'') AS "qualifiedCommitteeIndicator", COALESCE(to_char(date_of_election,'MM/DD/YYYY'),'') AS "electionDate",
                                            COALESCE(to_char(date_signed,'MM/DD/YYYY'),'') AS "dateSigned"
                                    FROM public.form_3x Where report_id = %s and cmte_id = %s AND delete_ind is distinct from 'Y'"""
            values_2 = [report_id, cmte_id]
            string_2 = "Form 3X"
            output = {**output, **json_query(query_2, values_2, string_2, False)[0]}

        elif output['formType'] == 'F1M':
            query_2 = """SELECT CASE WHEN (SELECT est_status FROM public.form_1m WHERE report_id=%s and cmte_id=%s) = 'A'
                            THEN (SELECT json_agg(t) FROM (SELECT est_status AS "establishmentStatus", aff_cmte_id AS "affiliatedCommitteeId", 
                            (SELECT cmte.cmte_name FROM committee_master cmte WHERE cmte.cmte_id = aff_cmte_id) AS "affiliatedCommitteeName", 
                            COALESCE(to_char(aff_date,'MM/DD/YYYY'),'') AS "affiliatedDate", sign_id AS "signatureId", 
                            COALESCE(to_char(sign_date,'MM/DD/YYYY'),'') AS "signatureDate", committee_type AS "committeeType"
                              FROM public.form_1m WHERE report_id=%s and cmte_id=%s AND delete_ind is distinct from 'Y') t)
                          WHEN (SELECT est_status FROM public.form_1m WHERE report_id=%s and cmte_id=%s) = 'Q'
                            THEN (SELECT json_agg(t) FROM (SELECT est_status AS "establishmentStatus", can1_id, 
                            COALESCE(to_char(can1_con,'MM/DD/YYYY'),'') AS "can1_con", can2_id, COALESCE(to_char(can2_con,'MM/DD/YYYY'),'') AS "can2_con", 
                            can3_id, COALESCE(to_char(can3_con,'MM/DD/YYYY'),'') AS "can3_con", can4_id, COALESCE(to_char(can4_con,'MM/DD/YYYY'),'') AS "can4_con", 
                            can5_id, COALESCE(to_char(can5_con,'MM/DD/YYYY'),'') AS "can5_con", COALESCE(to_char(date_51,'MM/DD/YYYY'),'') AS "51stContributorDate", 
                            COALESCE(to_char(orig_date,'MM/DD/YYYY'),'') AS "registrationDate", COALESCE(to_char(metreq_date,'MM/DD/YYYY'),'') AS "requirementsMetDate", 
                            sign_id AS "signatureId", COALESCE(to_char(sign_date,'MM/DD/YYYY'),'') AS "signatureDate", committee_type AS "committeeType"
                              FROM public.form_1m WHERE report_id=%s and cmte_id=%s AND delete_ind is distinct from 'Y') t)
                          END AS "output" """
            values_2 = [report_id, cmte_id, report_id, cmte_id, report_id, cmte_id, report_id, cmte_id]
            string_2 = "Form 1M"
            f1m_data = json_query(query_2, values_2, string_2, False)[0]['output']
            if f1m_data:
                f1m_data = f1m_data[0]
                f1m_data = get_candidate_details_jsonbuilder(f1m_data)
                output = {**output, **f1m_data}
            else:
                raise Exception(
                    'There is no form 1m data for this report id: {} and cmte id: {}'.format(report_id, cmte_id))

        elif output['formType'] == 'F24':
            query_3 = """SELECT  cm.cmte_id AS "committeeId", COALESCE(cm.cmte_name,'') AS "committeeName", r.report_type AS "reportType", r.amend_ind AS "amendIndicator",
                  COALESCE(to_char(filed_date,'MM/DD/YYYY'),'') AS "filedDate", COALESCE((CASE WHEN r.previous_report_id IS NOT null THEN 
                  (SELECT COALESCE(to_char(pr.filed_date,'MM/DD/YYYY'),'') FROM reports pr WHERE pr.report_id=r.previous_report_id) ELSE '' END), '') AS "amendDate"
                  FROM committee_master cm, reports r WHERE r.cmte_id = cm.cmte_id AND r.report_id=%s AND cm.cmte_id=%s"""
            values_3 = [report_id, cmte_id]
            string_3 = "Form 24"
            f24_data = json_query(query_3, values_3, string_3, False)
            if f24_data:
                f24_data = f24_data[0]
                output = {**output, **f24_data}
            else:
                raise Exception(
                    'There is no form 24 data for this report id: {} and cmte id: {}'.format(report_id, cmte_id))

        elif output['formType'] == 'F3L':
            query_3 = """SELECT rp.cmte_id as cmteId, rp.report_id as reportId, rp.form_type as formType, '' as electionCode, 
                                      rp.report_type as reportCode,  rt.rpt_type_desc as reportTypeDescription, 
                                      f3l.sign_date as date_signed,
                                      rt.regular_special_report_ind as regularSpecialReportInd, x.state_of_election as electionState, 
                                      x.date_of_election::date as electionDate, rp.cvg_start_date as cvgStartDate, rp.cvg_end_date as cvgEndDate, 
                                      rp.due_date as dueDate, rp.amend_ind as amend_Indicator, 0 as coh_bop,
                                      (SELECT CASE WHEN due_date IS NOT NULL THEN to_char(due_date, 'YYYY-MM-DD')::date - to_char(now(), 'YYYY-MM-DD')::date ELSE 0 END ) AS daysUntilDue, 
                                      email_1 as email1, email_2 as email2, additional_email_1 as additionalEmail1, 
                                      additional_email_2 as additionalEmail2, 
                                      (SELECT CASE WHEN rp.due_date IS NOT NULL AND rp.due_date < now() THEN True ELSE False END ) AS overdue,
                                      rp.status AS reportStatus, rp.semi_annual_start_date, rp.semi_annual_end_date, f3l.election_date, f3l.election_state
                                      FROM public.reports rp 
                                      LEFT JOIN form_3x x ON rp.report_id = x.report_id
                                      LEFT JOIN public.ref_rpt_types rt ON rp.report_type=rt.rpt_type
                                      LEFT JOIN public.form_3l f3l ON f3l.report_id = rp.report_id
                                      WHERE rp.delete_ind is distinct from 'Y' AND rp.cmte_id =%s AND rp.report_id =%s"""

            values_3 = [cmte_id, report_id]
            string_3 = "Form 3L"
            f3L_data = json_query(query_3, values_3, string_3, False)
            if f3L_data:
                f3L_data = f3L_data[0]
                output = {**output, **f3L_data}
            else:
                raise Exception(
                    'There is no form 3L data for this report id: {} and cmte id: {}'.format(report_id, cmte_id))

        else:
            raise Exception('The JSON Builder has not been implemented for this report type: ' + output['formType'])

        return output

    except Exception:
        raise

def get_f3l_summary_details(report_id, cmte_id):
    try:
        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)

        contribute_amount_query = """SELECT COALESCE(SUM(contribution_amount),0.0) AS "quarterly_monthly_total",COALESCE(SUM(semi_annual_refund_bundled_amount),0.0) AS "semi_annual_total"FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND transaction_type_identifier in ('IND_BNDLR','REG_ORG_BNDLR') AND delete_ind IS DISTINCT FROM 'Y'"""

        values = [cmte_id, report_id]

        return {
            "contribute_amount_query": json_query(contribute_amount_query, values, "Form3L", False)[0],
            "calAmount": True
        }

    except NoOPError:
        raise NoOPError(
            'The Committee ID: {} does not exist in Committee Master Table'.format(cmte_id))
    except Exception as e:
        raise e


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
        # print('get_transactions...')
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
        # print(query)
        # print(query_values_list)
        return json_query(query, query_values_list, error_string, True)
    except Exception:
        raise


def get_back_ref_transaction_ids(DB_table, identifier, report_id, cmte_id, transaction_id_list):
    try:
        output = []
        query = """SELECT DISTINCT(back_ref_transaction_id) FROM {} 
            WHERE transaction_type_identifier = %s AND report_id = %s AND cmte_id = %s
            AND transaction_id in ('{}') AND delete_ind is distinct from 'Y'""".format(DB_table,
                                                                                       "', '".join(transaction_id_list))
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
            if DB_table in ["public.sched_d", "public.sched_c", "public.sched_h1", "public.sched_h2", "public.sched_h3",
                            "public.sched_h5", "public.sched_l"]:
                query = """SELECT DISTINCT(transaction_type_identifier) FROM {} WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'""".format(
                    DB_table)
            else:
                query = """SELECT DISTINCT(transaction_type_identifier) FROM {} WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id is NULL AND delete_ind is distinct from 'Y'""".format(
                    DB_table)
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


def preappending_purpose_description(transaction):
    try:
        for preappend in DICT_PURPOSE_DESCRIPTION_VALUES:
            if transaction['transactionTypeIdentifier'] in DICT_PURPOSE_DESCRIPTION_VALUES[preappend]:
                if 'contributionPurposeDescription' in transaction:
                    if transaction['contributionPurposeDescription'] in [None, "null", "NULL"]:
                        transaction['contributionPurposeDescription'] = ""
                    transaction['contributionPurposeDescription'] = preappend + ' ' + transaction[
                        'contributionPurposeDescription']
                if 'expenditurePurposeDescription' in transaction:
                    if transaction['expenditurePurposeDescription'] in [None, "null", "NULL"]:
                        transaction['expenditurePurposeDescription'] = ""
                    transaction['expenditurePurposeDescription'] = preappend + ' ' + transaction[
                        'expenditurePurposeDescription']
            if 'child' in transaction:
                for child in transaction['child']:
                    if child['transactionTypeIdentifier'] in DICT_PURPOSE_DESCRIPTION_VALUES[preappend]:
                        if 'contributionPurposeDescription' in child:
                            if child['contributionPurposeDescription'] in [None, "null", "NULL"]:
                                child['contributionPurposeDescription'] = ""
                            child['contributionPurposeDescription'] = preappend + ' ' + child[
                                'contributionPurposeDescription']
                        if 'expenditurePurposeDescription' in child:
                            if child['expenditurePurposeDescription'] in [None, "null", "NULL"]:
                                child['expenditurePurposeDescription'] = ""
                            child['expenditurePurposeDescription'] = preappend + ' ' + child[
                                'expenditurePurposeDescription']
        return transaction
    except Exception as e:
        raise Exception(
            'The preappending_purpose_description function is raising the following error:' + str(e))


@api_view(["POST"])
def create_json_builders(request):
    try:
        # import ipdb;ipdb.set_trace()
        # print("request",request)
        logger.debug('create json builder with {}'.format(request))
        MANDATORY_INPUTS = ['report_id', 'call_from']
        error_string = ""
        output = {}
        transaction_flag = False

        transaction_id_list = []

        committeeId = request.data.get('committeeId')
        password = request.data.get('password')
        formType = request.data.get('formType')
        newAmendIndicator = request.data.get('newAmendIndicator')
        report_id = request.data.get('report_id')
        reportSequence = request.data.get('reportSequence')
        emailAddress1 = request.data.get('emailAddress1')
        reportType = request.data.get('reportType')
        coverageStartDate = request.data.get('coverageStartDate')
        coverageEndDate = request.data.get('coverageEndDate')
        originalFECId = request.data.get('originalFECId')
        backDoorCode = request.data.get('backDoorCode')
        emailAddress2 = request.data.get('emailAddress2')
        wait = request.data.get('wait')

        # Handling Mandatory Inputs required

        for field in MANDATORY_INPUTS:
            if field not in request.data or request.data.get(field) in [None, 'null', '', ""]:
                error_string += ','.join(field)
        if error_string != "":
            raise Exception(
                'The following inputs are mandatory for this API: ' + error_string)
        # Assiging data passed through request
        # report_id = request.data.get('report_id')
        call_from = request.data.get('call_from')

        cmte_id = get_comittee_id(request.user.username)
        # Checking for transaction ids in the request
        if 'transaction_id' in request.data and request.data.get('transaction_id'):
            transaction_flag = True
            transaction_id_string = request.data.get(
                'transaction_id').replace(" ", "")
            transaction_id_list = transaction_id_string.split(',')
        # Populating output json with header and data values
        # print('*** transaction id list***')
        logger.debug('transaction is list:{}'.format(transaction_id_list))
        output['header'] = get_header_details()
        output['data'] = get_data_details(report_id, cmte_id)
        # Figuring out the form type
        form_type = output.get('data').get('formType')
        # Adding Summary data to output based on form type
        if form_type in ['F3X', 'F24', 'F3L']:
            full_form_type = FORMTYPE_FORM_DICT.get(form_type)
            # Figuring out what schedules are to be checked for the form type
            schedule_name_list = get_schedules_for_form_type(full_form_type)
            # List of all the child transactions that need back_ref_transaction_id
            ALL_CHILD_TRANSACTION_TYPES_LIST = get_all_child_transaction_identifers(form_type)

            # *******************************TEMPORARY MODIFICATION FTO CHECK ONLY SCHED A AND SCHED B TABLES************************************
            # schedule_name_list = [
            #     {'sched_type': 'sched_a'}, {'sched_type': 'sched_b'}, {'sched_type': 'sched_c'}, {'sched_type': 'sched_d'},
            #     {'sched_type': 'sched_e'},
            #     {'sched_type': 'sched_f'}, {'sched_type': 'sched_h4'}, {'sched_type': 'sched_h6'},
            #     {'sched_type': 'sched_c1'},
            #     {'sched_type': 'sched_c2'}, {'sched_type': 'sched_h1'}, {'sched_type': 'sched_h2'},
            #     {'sched_type': 'sched_h3'}, {'sched_type': 'sched_h5'},
            #     {'sched_type': 'sched_l'}]
            # Iterating through schedules list and populating data into output
            if form_type == 'F3X' and (not transaction_flag):
                output['data']['summary'] = get_f3x_summary_details(
                    report_id, cmte_id)
            if form_type == 'F24':
                output['data']['reportPrint'] = False if transaction_flag else True
            if form_type == 'F3L' and (not transaction_flag):
                output['data']['summary'] = get_f3l_summary_details(
                    report_id, cmte_id)
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
                    # print('****')
                    # print(list_identifier)
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
                        # print('**********child identifer list')
                        # print(child_identifier_list)
                        # ********************************************
                        # SQL QUERY to get all transactions of the specific identifier
                        if identifier not in ALL_CHILD_TRANSACTION_TYPES_LIST:
                            # print('*****')
                            # print('parent')
                            parent_transactions = get_transactions(
                                identifier, report_id, cmte_id, None, transaction_id_list)
                            # print(parent_transactions)
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
                            # pre-appending the purpose description
                            transaction = preappending_purpose_description(transaction)
                            # Handling electionOtherDescription value for 'primary' and 'general'
                            if 'electionOtherDescription' in transaction and transaction[
                                'electionOtherDescription'] in ['Primary', 'General']:
                                transaction['electionOtherDescription'] = ""
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
        tmp_filename = cmte_id + '_' + str(report_id) + '_' + str(up_datetime) + '.json'
        tmp_path = '/tmp/' + tmp_filename
        json.dump(output, open(tmp_path, 'w'), indent=4)

        # Transfering the local json file to S3 bucket
        client = boto3.client('s3')

        transfer = S3Transfer(client)
        transfer.upload_file(tmp_path, 'dev-efile-repo', tmp_filename)
        # return Response("Success", status=status.HTTP_201_CREATED)
        if call_from == "PrintPreviewPDF":
            data_obj = {'form_type': form_type}
            file_obj = {'json_file': ('data.json', open(
                tmp_path, 'rb'), 'application/json')}

            # print("data_obj = ", data_obj)
            # print("file_obj = ", file_obj)
            resp = requests.post(settings.NXG_FEC_PRINT_API_URL +
                                 settings.NXG_FEC_PRINT_API_VERSION, data=data_obj, files=file_obj)
        elif call_from == "Submit":
            committeeId = request.data.get("committeeid")
            password = request.data.get('password')
            if not password:
                password = settings.NXG_COMMITTEE_DEFAULT_PASSWORD
            formType = request.data.get("form_type")
            newAmendIndicator = request.data.get("amend_ind")
            report_id = request.data.get("report_id")
            reportSequence = request.data.get('reportSequence')
            emailAddress1 = request.data.get('emailAddress1')
            emailAddress2 = request.data.get('emailAddress2')
            reportType = request.data.get("report_type")
            coverageStartDate = request.data.get("cvg_start_dt")
            coverageEndDate = request.data.get("cvg_end_dt")
            originalFECId = request.data.get('originalFECId')
            backDoorCode = ""  # request.data.get('backDoorCode')
            wait = settings.SUBMIT_REPORT_WAIT_FLAG
            # print("committeeId :" + committeeId)
            # print("password: " + password)
            # print("formType: " + formType)
            # print("newAmendIndicator: " + newAmendIndicator)
            # print("report_id: " + report_id)
            # print("reportSequence: " + reportSequence)
            # print("emailAddress1: " + emailAddress1)
            # print("reportType: " + reportType)
            # print("coverageStartDate: " + coverageStartDate)
            # print("coverageEndDate: " + coverageEndDate)
            # print("originalFECId: " + originalFECId)
            # print("backDoorCode: " + backDoorCode)
            # print("emailAddress2: " + emailAddress2)
            # print("wait: " + wait)
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
            add_log(report_id,
                    cmte_id,
                    4,
                    " create_json_builders calling data Validatior with data_obj",
                    json.dumps(data_obj),
                    '',
                    '',
                    ''
                    )
            resp = requests.post(settings.DATA_RECEIVE_API_URL + settings.DATA_RECEIVE_API_VERSION +
                                 "upload_filing", data=data_obj, files=file_obj)
            # print(resp)
            # print(resp.ok)
            # print(resp.json())
        if not resp.ok:
            return Response(resp.json(), status=status.HTTP_400_BAD_REQUEST)
        else:
            submissionId = resp.json()['result']['submissionId']
            submission_response = checkForReportSubmission(submissionId)
            if (submission_response.json()['result'][0]['status'] == 'ACCEPTED'):
                # update frontend database with Filing_id, Filed_by user
                submission_id = submission_response.json()['result'][0]['submissionId']
                beginning_image_number = submission_response.json()['result'][0]['beginningImageNumber']
                fec_id = submission_response.json()['result'][0]['reportId']
                return submit_report(request, submission_id, beginning_image_number, fec_id)
            return JsonResponse(submission_response.json(), status=status.HTTP_201_CREATED)
            # if submission_response.ok:
            #     dictprint = submission_response.json()
            #     print(dictprint)
            #     return JsonResponse(dictprint, status=status.HTTP_201_CREATED)
            # dictprint = resp.json()
            # return JsonResponse(dictprint, status=status.HTTP_201_CREATED)
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
            host_name=platform.uname()[1],
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
                       [reportid, cmte_id, process_name, message_type, message_text, response_json, error_code,
                        error_json, app_error, host_name])


def checkForReportSubmission(submissionId):
    filing_status_response = requests.get(settings.DATA_RECEIVE_API_URL + settings.DATA_RECEIVE_API_VERSION +
                                        "track_filing", data={'submissionId': submissionId})
    if filing_status_response.ok:
        if filing_status_response.json()['result'][0]['status'] == 'PROCESSING':
            time.sleep(5)
            filing_status_response = checkForReportSubmission(submissionId)
    return filing_status_response
