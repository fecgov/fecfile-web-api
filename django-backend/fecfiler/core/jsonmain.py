import json
import platform
import requests
import logging
import boto3
import time

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
from django.http import JsonResponse
from datetime import datetime
from boto3.s3.transfer import S3Transfer
from django.conf import settings

from fecfiler.core.views import submit_report

from fecfiler.core.views import (
    NoOPError,
    get_cvg_dates,
    superceded_report_id_list,
)
from fecfiler.password_management.views import treasurer_encrypted_password

# Dictionary mapping form type value to form type in forms_and_schedules table
FORMTYPE_FORM_DICT = {"F3X": "form_3x", "F24": "form_24", "F3L": "form_3l"}

# Dictionary mapping schedules to schedule codes in forms_and_schedules table
SCHED_SCHED_CODES_DICT = {
    "sched_a": "SA",
    "sched_b": "SB",
    "sched_c": "SC",
    "sched_d": "SD",
    "sched_e": "SE",
    "sched_f": "SF",
    "sched_h1": "SH",
    "sched_h2": "SH",
    "sched_h3": "SH",
    "sched_h4": "SH",
    "sched_h5": "SH",
    "sched_h6": "SH",
    "sched_l": "SL",
}

# Dictionary that excludes line numbers from final json
EXCLUDED_LINE_NUMBERS_FROM_JSON_LIST = ["11AII"]

# List of all sched D transction type identifiers. This has no back_ref_transaction_id column
# so modifying SQL based on this list
LIST_OF_TRANSACTION_TYPES_WITH_NO_BACK_REF = [
    "DEBT_TO_VENDOR",
    "LOANS_OWED_TO_CMTE",
    "LOANS_OWED_BY_CMTE",
    "ALLOC_H1",
    "ALLOC_H2_RATIO",
    "TRAN_FROM_NON_FED_ACC",
    "TRAN_FROM_LEVIN_ACC",
    "SCHED_L_SUM",
]

LIST_OF_SL_SA_TRANSACTION_TYPES = [
    "LEVIN_TRIB_REC",
    "LEVIN_PARTN_REC",
    "LEVIN_ORG_REC",
    "LEVIN_INDV_REC",
    "LEVIN_NON_FED_REC",
    "LEVIN_OTH_REC",
    "LEVIN_PAC_REC",
]

LIST_OF_SL_SB_TRANSACTION_TYPES = [
    "LEVIN_VOTER_ID",
    "LEVIN_GOTV",
    "LEVIN_GEN",
    "LEVIN_OTH_DISB",
    "LEVIN_VOTER_REG",
]

DICT_PURPOSE_DESCRIPTION_VALUES = {
    "Bounced": ["PARTY_RET", "PAC_RET", "RET_REC"],
    "Convention Account": [
        "IND_NP_CONVEN_ACC",
        "PAC_NP_CONVEN_ACC",
        "PARTY_NP_CONVEN_ACC",
        "TRIB_NP_CONVEN_ACC",
        "OPEXP_CONV_ACC_OP_EXP_NP",
    ],
    "Convention Account Earmarked Through": ["EAR_REC_CONVEN_ACC"],
    "Convention Account - JF Memo for": [
        "JF_TRAN_NP_CONVEN_IND_MEMO",
        "JF_TRAN_NP_CONVEN_PAC_MEMO",
        "JF_TRAN_NP_CONVEN_TRIB_MEMO",
    ],
    "Convention: Refund": ["OPEXP_CONV_ACC_TRIB_REF", "OPEXP_CONV_ACC_IND_REF"],
    "Credit Card Payment": ["IE_CC_PAY_MEMO"],
    "Credit Card: See Below": ["IE_CC_PAY"],
    "Earmark for": ["PAC_CON_EAR_DEP", "PAC_CON_EAR_UNDEP"],
    "Earmarked for": [
        "CON_EAR_DEP",
        "CON_EAR_UNDEP",
        "CON_EAR_UNDEP_BKP",
        "CON_EAR_UNDEP_BKP",
    ],
    "Earmarked from": [
        "CON_EAR_DEP_MEMO",
        "CON_EAR_UNDEP_MEMO",
        "PAC_CON_EAR_UNDEP_MEMO",
        "PAC_CON_EAR_DEP_MEMO",
    ],
    "Earmarked through": ["EAR_REC", "PAC_EAR_REC"],
    "Headquarters Account Earmarked Through": ["EAR_REC_HQ_ACC"],
    "Headquarters Account": [
        "IND_NP_HQ_ACC",
        "PAC_NP_HQ_ACC",
        "PARTY_NP_HQ_ACC",
        "TRIB_NP_HQ_ACC",
    ],
    "Headquarters Account - JF Memo for": [
        "JF_TRAN_NP_HQ_IND_MEMO",
        "JF_TRAN_NP_HQ_PAC_MEMO",
        "JF_TRAN_NP_HQ_TRIB_MEMO",
    ],
    "Headquarters: Refund": ["OPEXP_HQ_ACC_TRIB_REF", "OPEXP_HQ_ACC_IND_REF"],
    "In-kind": [
        "IK_REC",
        "IK_TRAN",
        "IK_TRAN_FEA",
        "PAC_IK_BC_OUT",
        "PAC_IK_BC_REC",
        "PAC_IK_REC",
        "PARTY_IK_BC_OUT",
        "PARTY_IK_REC",
    ],
    "JF Memo for": [
        "JF_TRAN_IND_MEMO",
        "JF_TRAN_PAC_MEMO",
        "JF_TRAN_PARTY_MEMO",
        "JF_TRAN_TRIB_MEMO",
    ],
    "JF Transfer": ["JF_TRAN"],
    "JF Transfer Convention Account": ["JF_TRAN_NP_CONVEN_ACC"],
    "JF Transfer Headquarters Account": ["JF_TRAN_NP_HQ_ACC"],
    "JF Transfer Recount Account": ["JF_TRAN_NP_RECNT_ACC"],
    "Loan From Ind": ["LOAN_FROM_IND"],
    "Non-Contribution Account Receipt": [
        "BUS_LAB_NON_CONT_ACC",
        "IND_REC_NON_CONT_ACC",
        "OTH_CMTE_NON_CONT_ACC",
    ],
    "Non-Contribution Account": [
        "OTH_DISB_NC_ACC",
        "OTH_DISB_NC_ACC_STAF_REIM",
        "OTH_DISB_NC_ACC_CC_PAY",
        "OTH_DISB_NC_ACC_PMT_TO_PROL",
        "OTH_DISB_NC_ACC_PMT_TO_PROL_MEMO",
        "OTH_DISB_NC_ACC_CC_PAY_MEMO",
        "OTH_DISB_NC_ACC_STAF_REIM_MEMO",
    ],
    "Partnership Memo": ["LEVIN_PARTN_MEMO", "PARTN_MEMO"],
    "Payroll: See Below": ["IE_PMT_TO_PROL"],
    "Recount Account": [
        "IND_NP_RECNT_ACC",
        "PAC_NP_RECNT_ACC",
        "PARTY_NP_RECNT_ACC",
        "TRIB_NP_RECNT_ACC",
    ],
    "Recount Account - JF Memo for": [
        "JF_TRAN_NP_RECNT_PAC_MEMO",
        "JF_TRAN_NP_RECNT_TRIB_MEMO",
        "JF_TRAN_NP_RECNT_IND_MEMO",
    ],
    "Recount Account Earmarked Through": ["EAR_REC_RECNT_ACC"],
    "Recount Receipt": [
        "IND_RECNT_REC",
        "PAC_RECNT_REC",
        "PARTY_RECNT_REC",
        "TRIB_RECNT_REC",
    ],
    "Recount: Refund": [
        "OTH_DISB_NP_RECNT_TRIB_REF",
        "OTH_DISB_NP_RECNT_REG_REF",
        "OTH_DISB_NP_RECNT_IND_REF",
    ],
    "Recount: Purpose of Disbursement": ["OTH_DISB_RECNT"],
    "Return/Void": ["PAC_NON_FED_RET", "PAC_RET"],
    "See Memos Below": ["LEVIN_PARTN_REC", "PARTN_REC"],
    "Staff Reimbursement Memo": ["COEXP_STAF_REIM_MEMO"],
}

logger = logging.getLogger(__name__)


def get_header_details():
    return {
        "version": "8.3",
        "softwareName": "ABC Inc",
        "softwareVersion": "1.02 Beta",
        "additionalInformation": "Any other useful information",
    }


def json_query(query, query_values_list, error_string, empty_list_flag):
    try:
        with connection.cursor() as cursor:
            sql_query = """SELECT json_agg(t) FROM ({}) t""".format(query)
            cursor.execute(sql_query, query_values_list)
            result = cursor.fetchone()[0]
            if result is None:
                # TO Handle zero transactions in sched_a or sched_b for a specific transaction_type_identifer
                # using this condition
                if empty_list_flag:
                    return []
                else:
                    raise NoOPError(
                        "No results are found in "
                        + error_string
                        + " Table. Input received:{}".format(
                            ",".join(query_values_list)
                        )
                    )
            else:
                return result
    except BaseException:
        raise


def get_candidate_details_jsonbuilder(request_dict):
    try:
        if request_dict.get("establishmentStatus") == "Q":
            output_list = []
            for i in range(1, 6):
                column_name = "can" + str(i) + "_id"
                candidate_id = request_dict.get(column_name)
                if candidate_id:
                    candidate_dict = get_sql_candidate_jsonbuilder(candidate_id)
                    candidate_dict["contributionDate"] = request_dict.get(
                        column_name[:-2] + "con"
                    )
                    candidate_dict["candidateNumber"] = i
                    output_list.append(candidate_dict)
                del request_dict[column_name]
                del request_dict[column_name[:-2] + "con"]
            request_dict["candidates"] = output_list
        return request_dict
    except Exception as e:
        raise Exception(
            "The get_candidate_details_jsonbuilder function is throwing an error: "
            + str(e)
        )


def get_sql_candidate_jsonbuilder(candidate_id):
    try:
        sql = """
            SELECT cand_id AS "candidateId", cand_last_name AS "candidateLastName",
            cand_first_name AS "candidateFirstName",
            cand_middle_name AS "candidateMiddleName", cand_prefix AS "candidatePrefix",
            cand_suffix AS "candidateSuffix",
            cand_office AS "candidateOffice", cand_office_state AS "candidateState",
            cand_office_district AS "candidateDistrict"
            FROM public.candidate_master WHERE cand_id=%s
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM ({}) AS t""".format(sql), [candidate_id]
            )
            logger.debug("CANDIDATE TABLE")
            logger.debug(cursor.query)
            output_dict = cursor.fetchone()[0]
            if output_dict:
                return output_dict[0]
            else:
                raise Exception(
                    """The candidateId: {} does not exist in
          candidate table.""".format(
                        candidate_id
                    )
                )
    except Exception as e:
        raise Exception(
            "The get_sql_candidate_jsonbuilder function is throwing an error: " + str(e)
        )


def get_data_details(report_id, cmte_id):
    try:
        query_1 = """
            SELECT cmte_id AS "committeeId",
            COALESCE(cmte_name,'') AS "committeeName",
            COALESCE(street_1,'') AS "street1",
            COALESCE(street_2,'') AS "street2",
            COALESCE(city,'') AS "city",
            COALESCE(state, '') AS "state",
            COALESCE(zip_code, '') AS "zipCode",
            COALESCE(treasurer_last_name, '') AS "treasurerLastName",
            COALESCE(treasurer_first_name, '') AS "treasurerFirstName",
            COALESCE(treasurer_middle_name, '') AS "treasurerMiddleName",
            COALESCE(treasurer_prefix, '') AS "treasurerPrefix",
            COALESCE(treasurer_suffix, '') as "treasurerSuffix"
            FROM public.committee_master Where cmte_id = %s
        """
        values_1 = [cmte_id]
        string_1 = "Committee Master"

        query_3 = """
            SELECT COALESCE(amend_number, 0) AS "amendmentNumber",
            COALESCE(to_char(cvg_start_date,'MM/DD/YYYY'),'') AS "coverageStartDate",
            COALESCE(to_char(cvg_end_date,'MM/DD/YYYY'),'') AS "coverageEndDate",
            form_type AS "formType", report_id AS "reportId", memo_text as "memoText"
            FROM public.reports WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'
            """
        values_3 = [report_id, cmte_id]
        string_3 = "Reports"

        output = {
            **json_query(query_1, values_1, string_1, False)[0],
            **json_query(query_3, values_3, string_3, False)[0],
        }

        if output["formType"] == "F3X":
            query_2 = """
                SELECT COALESCE(cmte_addr_chg_flag,'') AS "changeOfAddress",
                COALESCE(state_of_election,'') AS "electionState",
                COALESCE(report_type,'') AS "reportCode",
                COALESCE(amend_ind,'') AS "amendmentIndicator",
                COALESCE(election_code,'') AS "electionCode",
                COALESCE(qual_cmte_flag,'') AS "qualifiedCommitteeIndicator",
                COALESCE(to_char(date_of_election,'MM/DD/YYYY'),'') AS "electionDate",
                COALESCE(to_char(date_signed,'MM/DD/YYYY'),'') AS "dateSigned"
                FROM public.form_3x Where report_id = %s and cmte_id = %s AND delete_ind is distinct from 'Y'
            """
            values_2 = [report_id, cmte_id]
            string_2 = "Form 3X"
            output = {**output, **json_query(query_2, values_2, string_2, False)[0]}

        elif output["formType"] == "F1M":
            query_2 = """
                SELECT CASE WHEN (SELECT est_status FROM public.form_1m WHERE report_id=%s and cmte_id=%s) = 'A'
                  THEN (SELECT json_agg(t) FROM (SELECT est_status AS "establishmentStatus", aff_cmte_id AS "affiliatedCommitteeId",
                  (SELECT cmte.cmte_name FROM committee_master cmte WHERE cmte.cmte_id = aff_cmte_id) AS "affiliatedCommitteeName",
                  COALESCE(to_char(aff_date,'MM/DD/YYYY'),'') AS "affiliatedDate", sign_id AS "signatureId",
                  COALESCE(to_char(sign_date,'MM/DD/YYYY'),'') AS "signatureDate", committee_type AS "committeeType"
                    FROM public.form_1m WHERE report_id=%s and cmte_id=%s AND delete_ind is distinct from 'Y') t)
                WHEN (SELECT est_status FROM public.form_1m WHERE report_id=%s and cmte_id=%s) = 'Q'
                  THEN (SELECT json_agg(t) FROM (SELECT est_status AS "establishmentStatus", can1_id,
                  COALESCE(to_char(can1_con,'MM/DD/YYYY'),'') AS "can1_con", can2_id,
                  COALESCE(to_char(can2_con,'MM/DD/YYYY'),'') AS "can2_con",
                  can3_id, COALESCE(to_char(can3_con,'MM/DD/YYYY'),'') AS "can3_con", can4_id,
                  COALESCE(to_char(can4_con,'MM/DD/YYYY'),'') AS "can4_con",
                  can5_id, COALESCE(to_char(can5_con,'MM/DD/YYYY'),'') AS "can5_con",
                  COALESCE(to_char(date_51,'MM/DD/YYYY'),'') AS "51stContributorDate",
                  COALESCE(to_char(orig_date,'MM/DD/YYYY'),'') AS "registrationDate",
                  COALESCE(to_char(metreq_date,'MM/DD/YYYY'),'') AS "requirementsMetDate",
                  sign_id AS "signatureId",
                  COALESCE(to_char(sign_date,'MM/DD/YYYY'),'') AS "signatureDate", committee_type AS "committeeType"
                    FROM public.form_1m WHERE report_id=%s and cmte_id=%s AND delete_ind is distinct from 'Y') t)
                END AS "output"
            """
            values_2 = [
                report_id,
                cmte_id,
                report_id,
                cmte_id,
                report_id,
                cmte_id,
                report_id,
                cmte_id,
            ]
            string_2 = "Form 1M"
            f1m_data = json_query(query_2, values_2, string_2, False)[0]["output"]
            if f1m_data:
                f1m_data = f1m_data[0]
                f1m_data = get_candidate_details_jsonbuilder(f1m_data)
                output = {**output, **f1m_data}
            else:
                raise Exception(
                    "There is no form 1m data for this report id: {} and cmte id: {}".format(
                        report_id, cmte_id
                    )
                )

        elif output["formType"] == "F24":
            query_3 = """
                SELECT  cm.cmte_id AS "committeeId", COALESCE(cm.cmte_name,'') AS "committeeName",
                r.report_type AS "reportType", r.amend_ind AS "amendIndicator",
                COALESCE(to_char(filed_date,'MM/DD/YYYY'),'') AS "filedDate",
                COALESCE((CASE WHEN r.previous_report_id IS NOT null THEN
                (SELECT COALESCE(to_char(pr.filed_date,'MM/DD/YYYY'),'')
                 FROM reports pr WHERE pr.report_id=r.previous_report_id) ELSE '' END), '') AS "amendDate"
                FROM committee_master cm, reports r
                WHERE r.cmte_id = cm.cmte_id AND r.report_id=%s AND cm.cmte_id=%s
            """
            values_3 = [report_id, cmte_id]
            string_3 = "Form 24"
            f24_data = json_query(query_3, values_3, string_3, False)
            if f24_data:
                f24_data = f24_data[0]
                output = {**output, **f24_data}
            else:
                raise Exception(
                    "There is no form 24 data for this report id: {} and cmte id: {}".format(
                        report_id, cmte_id
                    )
                )

        elif output["formType"] == "F3L":
            query_3 = """
                SELECT rp.cmte_id as cmteId, rp.report_id as reportId,
                rp.form_type as formType, '' as electionCode,
                rp.report_type as reportCode,  rt.rpt_type_desc as reportTypeDescription,
                f3l.sign_date as date_signed,
                rt.regular_special_report_ind as regularSpecialReportInd,
                x.state_of_election as electionState,
                x.date_of_election::date as electionDate, rp.cvg_start_date as cvgStartDate,
                rp.cvg_end_date as cvgEndDate,
                rp.due_date as dueDate, rp.amend_ind as amend_Indicator, 0 as coh_bop,
                (
                    SELECT CASE WHEN due_date IS NOT NULL
                    THEN to_char(due_date, 'YYYY-MM-DD')::date - to_char(now(), 'YYYY-MM-DD')::date
                    ELSE 0 END
                ) AS daysUntilDue,
                email_1 as email1, email_2 as email2, additional_email_1 as additionalEmail1,
                additional_email_2 as additionalEmail2,
                (
                    SELECT CASE WHEN rp.due_date IS NOT NULL
                    AND rp.due_date < now() THEN True
                    ELSE False END
                ) AS overdue,
                rp.status AS reportStatus, rp.semi_annual_start_date, rp.semi_annual_end_date,
                f3l.election_date, f3l.election_state
                FROM public.reports rp
                LEFT JOIN form_3x x ON rp.report_id = x.report_id
                LEFT JOIN public.ref_rpt_types rt ON rp.report_type=rt.rpt_type
                LEFT JOIN public.form_3l f3l ON f3l.report_id = rp.report_id
                WHERE rp.delete_ind is distinct from 'Y' AND rp.cmte_id =%s AND rp.report_id =%s
            """

            values_3 = [cmte_id, report_id]
            string_3 = "Form 3L"
            f3L_data = json_query(query_3, values_3, string_3, False)
            if f3L_data:
                f3L_data = f3L_data[0]
                output = {**output, **f3L_data}
            else:
                raise Exception(
                    "There is no form 3L data for this report id: {} and cmte id: {}".format(
                        report_id, cmte_id
                    )
                )

        else:
            raise Exception(
                "The JSON Builder has not been implemented for this report type: "
                + output["formType"]
            )

        return output

    except Exception:
        raise


def get_f3l_summary_details(report_id, cmte_id):
    try:
        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)

        contribute_amount_query = """
            SELECT COALESCE(SUM(contribution_amount),0.0) AS "quarterly_monthly_total",
            COALESCE(SUM(semi_annual_refund_bundled_amount),0.0) AS "semi_annual_total"
            FROM public.sched_a
            WHERE cmte_id = %s AND report_id = %s
            AND transaction_type_identifier in ('IND_BNDLR','REG_ORG_BNDLR')
            AND delete_ind IS DISTINCT FROM 'Y'
        """

        values = [cmte_id, report_id]

        return {
            "contribute_amount_query": json_query(
                contribute_amount_query, values, "Form3L", False
            )[0],
            "calAmount": True,
        }

    except NoOPError:
        raise NoOPError(
            "The Committee ID: {} does not exist in Committee Master Table".format(
                cmte_id
            )
        )
    except Exception as e:
        raise e


def get_f3x_summary_details(report_id, cmte_id):
    try:
        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)
        cashOnHandYear = cvg_start_date.year

        colA_query = """
            SELECT COALESCE(coh_bop, 0.0) AS "6b_cashOnHandBeginning",
            COALESCE(ttl_receipts_sum_page_per, 0.0) AS "6c_totalReceipts",
            COALESCE(subttl_sum_page_per, 0.0) AS "6d_subtotal",
            COALESCE(ttl_disb_sum_page_per, 0.0) AS "7_totalDisbursements",
            COALESCE(coh_cop, 0.0) AS "8_cashOnHandAtClose",
            COALESCE(debts_owed_to_cmte, 0.0) AS "9_debtsTo",
            COALESCE(debts_owed_by_cmte, 0.0) AS "10_debtsBy",
            COALESCE(indv_item_contb_per, 0.0) AS "11ai_Itemized",
            COALESCE(indv_unitem_contb_per, 0.0) AS "11aii_Unitemized",
            COALESCE(ttl_indv_contb, 0.0) AS "11aiii_Total",
            COALESCE(pol_pty_cmte_contb_per_i, 0.0) AS "11b_politicalPartyCommittees",
            COALESCE(other_pol_cmte_contb_per_i, 0.0) AS "11c_otherPoliticalCommitteesPACs",
            COALESCE(ttl_contb_col_ttl_per, 0.0) AS "11d_totalContributions",
            COALESCE(tranf_from_affiliated_pty_per, 0.0) AS "12_transfersFromAffiliatedOtherPartyCommittees",
            COALESCE(all_loans_received_per, 0.0) AS "13_allLoansReceived",
            COALESCE(loan_repymts_received_per, 0.0) AS "14_loanRepaymentsReceived",
            COALESCE(offsets_to_op_exp_per_i, 0.0) AS "15_offsetsToOperatingExpendituresRefunds",
            COALESCE(fed_cand_contb_ref_per, 0.0) AS "16_refundsOfFederalContributions",
            COALESCE(other_fed_receipts_per, 0.0) AS "17_otherFederalReceiptsDividends",
            COALESCE(tranf_from_nonfed_acct_per, 0.0) AS "18a_transfersFromNonFederalAccount_h3",
            COALESCE(tranf_from_nonfed_levin_per, 0.0) AS "18b_transfersFromNonFederalLevin_h5",
            COALESCE(ttl_nonfed_tranf_per, 0.0) AS "18c_totalNonFederalTransfers",
            COALESCE(ttl_receipts_per, 0.0) AS "19_totalReceipts",
            COALESCE(ttl_fed_receipts_per, 0.0) AS "20_totalFederalReceipts",
            COALESCE(shared_fed_op_exp_per, 0.0) AS "21ai_federalShare",
            COALESCE(shared_nonfed_op_exp_per, 0.0) AS "21aii_nonFederalShare",
            COALESCE(other_fed_op_exp_per, 0.0) AS "21b_otherFederalOperatingExpenditures",
            COALESCE(ttl_op_exp_per, 0.0) AS "21c_totalOperatingExpenditures",
            COALESCE(tranf_to_affliliated_cmte_per, 0.0) AS "22_transfersToAffiliatedOtherPartyCommittees",
            COALESCE(fed_cand_cmte_contb_per, 0.0) AS "23_contributionsToFederalCandidatesCommittees",
            COALESCE(indt_exp_per, 0.0) AS "24_independentExpenditures",
            COALESCE(coord_exp_by_pty_cmte_per, 0.0) AS "25_coordinatedExpenditureMadeByPartyCommittees",
            COALESCE(loan_repymts_made_per, 0.0) AS "26_loanRepayments",
            COALESCE(loans_made_per, 0.0) AS "27_loansMade",
            COALESCE(indv_contb_ref_per, 0.0) AS "28a_individualsPersons",
            COALESCE(pol_pty_cmte_contb_per_ii, 0.0) AS "28b_politicalPartyCommittees",
            COALESCE(other_pol_cmte_contb_per_ii, 0.0) AS "28c_otherPoliticalCommittees",
            COALESCE(ttl_contb_ref_per_i, 0.0) AS "28d_totalContributionsRefunds",
            COALESCE(other_disb_per, 0.0) AS "29_otherDisbursements",
            COALESCE(shared_fed_actvy_fed_shr_per, 0.0) AS "30ai_sharedFederalActivity_h6_fedShare",
            COALESCE(shared_fed_actvy_nonfed_per, 0.0) AS "30aii_sharedFederalActivity_h6_nonFed",
            COALESCE(non_alloc_fed_elect_actvy_per, 0.0) AS "30b_nonAllocable_100_federalElectionActivity",
            COALESCE(ttl_fed_elect_actvy_per, 0.0) AS "30c_totalFederalElectionActivity",
            COALESCE(ttl_disb_per, 0.0) AS "31_totalDisbursements",
            COALESCE(ttl_fed_disb_per, 0.0) AS "32_totalFederalDisbursements",
            COALESCE(ttl_contb_per, 0.0) AS "33_totalContributions",
            COALESCE(ttl_contb_ref_per_ii, 0.0) AS "34_totalContributionRefunds",
            COALESCE(net_contb_per, 0.0) AS "35_netContributions",
            COALESCE(ttl_fed_op_exp_per, 0.0) AS "36_totalFederalOperatingExpenditures",
            COALESCE(offsets_to_op_exp_per_ii, 0.0) AS "37_offsetsToOperatingExpenditures",
            COALESCE(net_op_exp_per, 0.0) AS "38_netOperatingExpenditures"
            FROM public.form_3x, reports r Where form_3x.report_id = r.report_id and r.cvg_start_date = %s
            and previous_report_id is NULL and form_3x.cmte_id = %s AND form_3x.delete_ind is distinct from 'Y'
            """

        colB_query = """SELECT COALESCE(coh_begin_calendar_yr, 0.0) AS "6a_cashOnHandJan_1",
            COALESCE(ttl_receipts_sum_page_ytd, 0.0) AS "6c_totalReceipts",
            COALESCE(subttl_sum_ytd, 0.0) AS "6d_subtotal",
            COALESCE(ttl_disb_sum_page_ytd, 0.0) AS "7_totalDisbursements",
            COALESCE(coh_coy, 0.0) AS "8_cashOnHandAtClose",
            COALESCE(indv_item_contb_ytd, 0.0) AS "11ai_Itemized",
            COALESCE(indv_unitem_contb_ytd, 0.0) AS "11aii_Unitemized",
            COALESCE(ttl_indv_contb_ytd, 0.0) AS "11aiii_Total",
            COALESCE(pol_pty_cmte_contb_ytd_i, 0.0) AS "11b_politicalPartyCommittees",
            COALESCE(other_pol_cmte_contb_ytd_i, 0.0) AS "11c_otherPoliticalCommitteesPACs",
            COALESCE(ttl_contb_col_ttl_ytd, 0.0) AS "11d_totalContributions",
            COALESCE(tranf_from_affiliated_pty_ytd, 0.0) AS "12_transfersFromAffiliatedOtherPartyCommittees",
            COALESCE(all_loans_received_ytd, 0.0) AS "13_allLoansReceived",
            COALESCE(loan_repymts_received_ytd, 0.0) AS "14_loanRepaymentsReceived",
            COALESCE(offsets_to_op_exp_ytd_i, 0.0) AS "15_offsetsToOperatingExpendituresRefunds",
            COALESCE(fed_cand_cmte_contb_ytd, 0.0) AS "16_refundsOfFederalContributions",
            COALESCE(other_fed_receipts_ytd, 0.0) AS "17_otherFederalReceiptsDividends",
            COALESCE(tranf_from_nonfed_acct_ytd, 0.0) AS "18a_transfersFromNonFederalAccount_h3",
            COALESCE(tranf_from_nonfed_levin_ytd, 0.0) AS "18b_transfersFromNonFederalLevin_h5",
            COALESCE(ttl_nonfed_tranf_ytd, 0.0) AS "18c_totalNonFederalTransfers",
            COALESCE(ttl_receipts_ytd, 0.0) AS "19_totalReceipts",
            COALESCE(ttl_fed_receipts_ytd, 0.0) AS "20_totalFederalReceipts",
            COALESCE(shared_fed_op_exp_ytd, 0.0) AS "21ai_federalShare",
            COALESCE(shared_nonfed_op_exp_ytd, 0.0) AS "21aii_nonFederalShare",
            COALESCE(other_fed_op_exp_ytd, 0.0) AS "21b_otherFederalOperatingExpenditures",
            COALESCE(ttl_op_exp_ytd, 0.0) AS "21c_totalOperatingExpenditures",
            COALESCE(tranf_to_affilitated_cmte_ytd, 0.0) AS "22_transfersToAffiliatedOtherPartyCommittees",
            COALESCE(fed_cand_cmte_contb_ref_ytd, 0.0) AS "23_contributionsToFederalCandidatesCommittees",
            COALESCE(indt_exp_ytd, 0.0) AS "24_independentExpenditures",
            COALESCE(coord_exp_by_pty_cmte_ytd, 0.0) AS "25_coordinatedExpenditureMadeByPartyCommittees",
            COALESCE(loan_repymts_made_ytd, 0.0) AS "26_loanRepayments",
            COALESCE(loans_made_ytd, 0.0) AS "27_loansMade",
            COALESCE(indv_contb_ref_ytd, 0.0) AS "28a_individualsPersons",
            COALESCE(pol_pty_cmte_contb_ytd_ii, 0.0) AS "28b_politicalPartyCommittees",
            COALESCE(other_pol_cmte_contb_ytd_ii, 0.0) AS "28c_otherPoliticalCommittees",
            COALESCE(ttl_contb_ref_ytd_i, 0.0) AS "28d_totalContributionsRefunds",
            COALESCE(other_disb_ytd, 0.0) AS "29_otherDisbursements",
            COALESCE(shared_fed_actvy_fed_shr_ytd, 0.0) AS "30ai_sharedFederalActivity_h6_fedShare",
            COALESCE(shared_fed_actvy_nonfed_ytd, 0.0) AS "30aii_sharedFederalActivity_h6_nonFed",
            COALESCE(non_alloc_fed_elect_actvy_ytd, 0.0) AS "30b_nonAllocable_100_federalElectionActivity",
            COALESCE(ttl_fed_elect_actvy_ytd, 0.0) AS "30c_totalFederalElectionActivity",
            COALESCE(ttl_disb_ytd, 0.0) AS "31_totalDisbursements",
            COALESCE(ttl_fed_disb_ytd, 0.0) AS "32_totalFederalDisbursements",
            COALESCE(ttl_contb_ytd, 0.0) AS "33_totalContributions",
            COALESCE(ttl_contb_ref_ytd_ii, 0.0) AS "34_totalContributionRefunds",
            COALESCE(net_contb_ytd, 0.0) AS "35_netContributions",
            COALESCE(ttl_fed_op_exp_ytd, 0.0) AS "36_totalFederalOperatingExpenditures",
            COALESCE(offsets_to_op_exp_ytd_ii, 0.0) AS "37_offsetsToOperatingExpenditures",
            COALESCE(net_op_exp_ytd, 0.0) AS "38_netOperatingExpenditures"
            FROM public.form_3x, reports r Where form_3x.report_id = r.report_id and r.cvg_start_date = %s
            and previous_report_id is NULL and form_3x.cmte_id = %s AND form_3x.delete_ind is distinct from 'Y'
            """

        values = [cvg_start_date, cmte_id]

        return {
            "cashOnHandYear": cashOnHandYear,
            "colA": json_query(colA_query, values, "Form3X", False)[0],
            "colB": json_query(colB_query, values, "Form3X", False)[0],
        }
    except NoOPError:
        raise NoOPError(
            "The Committee ID: {} does not exist in Committee Master Table".format(
                cmte_id
            )
        )
    except Exception:
        raise


def get_transactions(
    identifier, report_list, cmte_id, back_ref_transaction_id, transaction_id_list
):
    try:
        query_1 = """SELECT query_string FROM public.tran_query_string WHERE tran_type_identifier = %s"""
        query_values_list_1 = [identifier]
        output = json_query(query_1, query_values_list_1, "tran_query_string", False)[0]
        query = output.get("query_string")
        report_string = "t1.report_id in ('{}')".format("', '".join(report_list))
        query = query.replace("t1.report_id = %s", report_string)
        if transaction_id_list:
            query = query + " AND transaction_id in ('{}')".format(
                "', '".join(transaction_id_list)
            )
        # Addressing no back_ref_transaction_id column in sched_D
        if identifier in LIST_OF_TRANSACTION_TYPES_WITH_NO_BACK_REF:
            query_values_list = [cmte_id]
        else:
            query_values_list = [
                cmte_id,
                back_ref_transaction_id,
                back_ref_transaction_id,
            ]
        error_string = identifier + ". Get all transactions"
        return json_query(query, query_values_list, error_string, True)
    except Exception:
        raise


def get_back_ref_transaction_ids(
    db_table, identifier, report_list, cmte_id, transaction_id_list
):
    try:
        output = []
        query = """SELECT DISTINCT(back_ref_transaction_id) FROM {}
            WHERE transaction_type_identifier = %s AND report_id in ('{}') AND cmte_id = %s
            AND transaction_id in ('{}') AND delete_ind is distinct from 'Y'""".format(
            db_table, "', '".join(report_list), "', '".join(transaction_id_list)
        )
        query_values_list = [identifier, cmte_id]
        results = json_query(query, query_values_list, db_table, True)
        for result in results:
            output.append(result["back_ref_transaction_id"])
        return output
    except Exception:
        raise


def get_transaction_type_identifier(
    db_table, report_list, cmte_id, transaction_id_list
):
    try:
        if transaction_id_list:
            # Addressing no back_ref_transaction_id column in sched_D
            # if db_table in ["public.sched_d", "public.sched_c", "public.sched_h1", "public.sched_h2", "public.sched_h3", "public.sched_h5", "public.sched_l"]:
            query = """SELECT DISTINCT(transaction_type_identifier) FROM {} WHERE report_id in ('{}')
                AND cmte_id = %s AND transaction_id in ('{}') AND delete_ind is distinct from 'Y'""".format(
                db_table, "', '".join(report_list), "', '".join(transaction_id_list)
            )
        else:
            # Addressing no back_ref_transaction_id column in sched_D
            if db_table in [
                "public.sched_d",
                "public.sched_c",
                "public.sched_h1",
                "public.sched_h2",
                "public.sched_h3",
                "public.sched_h5",
                "public.sched_l",
            ]:
                query = """SELECT DISTINCT(transaction_type_identifier) FROM {} WHERE report_id in ('{}')
                    AND cmte_id = %s AND delete_ind is distinct from 'Y'""".format(
                    db_table, "', '".join(report_list)
                )
            else:
                query = """SELECT DISTINCT(transaction_type_identifier) FROM {} WHERE report_id in ('{}')
                    AND cmte_id = %s AND back_ref_transaction_id is NULL AND delete_ind is distinct from 'Y'""".format(
                    db_table, "', '".join(report_list)
                )
        query_values_list = [cmte_id]
        result = json_query(query, query_values_list, db_table, True)
        return result
    except Exception as e:
        raise Exception(
            "The get_transaction_type_identifier function is raising the following error: "
            + str(e)
        )


def get_schedules_for_form_type(form_type):
    try:
        query = """
            SELECT DISTINCT(sched_type) FROM public.forms_and_schedules
            WHERE form_type = %s AND json_builder_flag IS TRUE
        """
        query_values_list = [form_type]
        error_string = "forms_and_schedules"
        result = json_query(query, query_values_list, error_string, False)
        return result
    except Exception as e:
        raise Exception(
            "The get_schedules_for_form_type function is raising the following error: "
            + str(e)
        )


def get_child_identifer(identifier, form_type):
    try:
        query = """
            SELECT c.tran_identifier FROM ref_transaction_types p
            LEFT JOIN ref_transaction_types c ON c.parent_tran_id=p.ref_tran_id
            WHERE p.tran_identifier = %s AND p.form_type = %s
            ORDER BY p.line_num,p.ref_tran_id
        """
        query_values_list = [identifier, form_type]
        error_string = "ref_transaction_types"
        result = json_query(query, query_values_list, error_string, True)
        return result
    except Exception as e:
        raise Exception(
            "The get_child_identifer function is raising the following error:" + str(e)
        )


def get_all_child_transaction_identifers(form_type):
    try:
        output = []
        query = """
            SELECT p.tran_identifier FROM ref_transaction_types p
            WHERE p.parent_tran_id IS NOT NULL AND p.form_type = %s ORDER BY p.line_num,p.ref_tran_id
        """
        query_values_list = [form_type]
        error_string = "ref_transaction_types"
        results = json_query(query, query_values_list, error_string, True)
        for result in results:
            output.append(result["tran_identifier"])
        return output
    except Exception as e:
        raise Exception(
            "The get_all_child_transaction_identifers function is raising the following error:"
            + str(e)
        )


def preappending_purpose_description(transaction):
    try:
        for preappend in DICT_PURPOSE_DESCRIPTION_VALUES:
            if (
                transaction["transactionTypeIdentifier"]
                in DICT_PURPOSE_DESCRIPTION_VALUES[preappend]
            ):
                if "contributionPurposeDescription" in transaction:
                    if transaction["contributionPurposeDescription"] in [
                        None,
                        "null",
                        "NULL",
                    ]:
                        transaction["contributionPurposeDescription"] = ""
                    transaction["contributionPurposeDescription"] = (
                        preappend + " " + transaction["contributionPurposeDescription"]
                    )
                if "expenditurePurposeDescription" in transaction:
                    if transaction["expenditurePurposeDescription"] in [
                        None,
                        "null",
                        "NULL",
                    ]:
                        transaction["expenditurePurposeDescription"] = ""
                    transaction["expenditurePurposeDescription"] = (
                        preappend + " " + transaction["expenditurePurposeDescription"]
                    )
            if "child" in transaction:
                for child in transaction["child"]:
                    if (
                        child["transactionTypeIdentifier"]
                        in DICT_PURPOSE_DESCRIPTION_VALUES[preappend]
                    ):
                        if "contributionPurposeDescription" in child:
                            if child["contributionPurposeDescription"] in [
                                None,
                                "null",
                                "NULL",
                            ]:
                                child["contributionPurposeDescription"] = ""
                            child["contributionPurposeDescription"] = (
                                preappend
                                + " "
                                + child["contributionPurposeDescription"]
                            )
                        if "expenditurePurposeDescription" in child:
                            if child["expenditurePurposeDescription"] in [
                                None,
                                "null",
                                "NULL",
                            ]:
                                child["expenditurePurposeDescription"] = ""
                            child["expenditurePurposeDescription"] = (
                                preappend + " " + child["expenditurePurposeDescription"]
                            )
        return transaction
    except Exception as e:
        raise Exception(
            "The preappending_purpose_description function is raising the following error:"
            + str(e)
        )


"""
message_type,
 1-FATAL, 2-ERROR, 3-WARN, 4-INFO, 5-DEBUG, 6-TRACE
"""


def add_log(
    reportid,
    cmte_id,
    message_type,
    message_text,
    response_json,
    error_code,
    error_json,
    app_error,
    host_name=platform.uname()[1],
    process_name="create_json_builders",
):
    with connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO public.upload_logs(
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
            [
                reportid,
                cmte_id,
                process_name,
                message_type,
                message_text,
                response_json,
                error_code,
                error_json,
                app_error,
                host_name,
            ],
        )


def checkForReportSubmission(submission_id):
    filing_status_response = requests.get(
        +settings.DATA_RECEIVE_API_URL
        + settings.DATA_RECEIVE_API_VERSION
        + "track_filing",
        data={"submission_id": submission_id},
    )
    if filing_status_response.ok:
        if filing_status_response.json()["result"][0]["status"] == "PROCESSING":
            time.sleep(5)
            filing_status_response = checkForReportSubmission(submission_id)
    return filing_status_response
