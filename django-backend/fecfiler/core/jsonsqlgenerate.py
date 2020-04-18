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
from django.conf import settings
import re
import csv

@api_view(["GET"])
def sample_sql_generate(request):
        try:
                List_SA_similar_INDV_REC = ["INDV_REC", "PARTN_MEMO", "IK_REC", "REATT_FROM", "REATT_MEMO", "RET_REC", "EAR_REC",
                            "CON_EAR_UNDEP", "CON_EAR_DEP", "IND_RECNT_REC", "IND_NP_RECNT_ACC", "IND_NP_HQ_ACC", "IND_NP_CONVEN_ACC",
                            "IND_REC_NON_CONT_ACC", "JF_TRAN_IND_MEMO", "JF_TRAN_NP_RECNT_IND_MEMO", "JF_TRAN_NP_CONVEN_IND_MEMO",
                            "JF_TRAN_NP_HQ_IND_MEMO", "EAR_REC_RECNT_ACC", "EAR_REC_CONVEN_ACC", "EAR_REC_HQ_ACC"]
                INDV_REC_STRING = ""
                for tran in List_SA_similar_INDV_REC:
                    query = """SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                    COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(to_char(t1.contribution_date,''MM/DD/YYYY''), '''') AS "contributionDate", 
                    t1.contribution_amount AS "contributionAmount", 
                    COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                    COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", 
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription",
                    COALESCE(t2.entity_type, '''') AS "entityType", 
                    COALESCE(t2.last_name, '''') AS "contributorLastName", 
                    COALESCE(t2.first_name, '''') AS "contributorFirstName",
                    COALESCE(t2.middle_name, '''') AS "contributorMiddleName", 
                    COALESCE(t2.preffix, '''') AS "contributorPrefix", 
                    COALESCE(t2.suffix, '''') AS "contributorSuffix",
                    COALESCE(t2.street_1, '''') AS "contributorStreet1", 
                    COALESCE(t2.street_2, '''') AS "contributorStreet2", 
                    COALESCE(t2.city, '''') AS "contributorCity",
                    COALESCE(t2.state, '''') AS "contributorState", 
                    COALESCE(t2.zip_code, '''') AS "contributorZipCode", 
                    COALESCE(t2.employer, '''') AS "contributorEmployer",
                    COALESCE(t2.occupation, '''') AS "contributorOccupation"
                    FROM public.sched_a t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                    INDV_REC_STRING += """
                    UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                    AND form_type = '{2}' AND sched_type = '{3}';\n
                    """.format(query, tran, 'F3X', 'SA')
                    INDV_REC_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/indv_rec_sql.sql", 'w')
                file.write(INDV_REC_STRING)
                file.close()

                list_SA_similar_PAR_CON = ["PARTN_REC", "TRIB_REC", "TRIB_NP_RECNT_ACC", "TRIB_NP_HQ_ACC", "TRIB_NP_CONVEN_ACC",
                            "BUS_LAB_NON_CONT_ACC", "JF_TRAN_TRIB_MEMO", "JF_TRAN_NP_RECNT_TRIB_MEMO", "JF_TRAN_NP_CONVEN_TRIB_MEMO",
                            "JF_TRAN_NP_HQ_TRIB_MEMO", "LOAN_FROM_BANK"]
                PAR_CON_STRING = ""
                for tran in list_SA_similar_PAR_CON:

                        query = """
                        SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                        COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                        t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                        COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.contribution_date,''MM/DD/YYYY'') AS "contributionDate", t1.contribution_amount AS "contributionAmount", COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                        COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", COALESCE(t1.memo_code, '''') AS "memoCode", 
                        COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "contributorOrgName",
                        COALESCE(t2.street_1, '''') AS "contributorStreet1", COALESCE(t2.street_2, '''') AS "contributorStreet2", COALESCE(t2.city, '''') AS "contributorCity",
                        COALESCE(t2.state, '''') AS "contributorState", COALESCE(t2.zip_code, '''') AS "contributorZipCode"
                        FROM public.sched_a t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        # PAR_CON_STRING += """
                        # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        # AND form_type = '{2}' AND sched_type = '{3}';\n
                        # """.format(query, tran, 'F3X', 'SA')
                        PAR_CON_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

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
                        SELECT COALESCE(t1.line_number, '''') AS "lineNumber", COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
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
                        # COND_EARM_PAC_STRING += """
                        # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        # AND form_type = '{2}' AND sched_type = '{3}';\n
                        # """.format(query, tran, 'F3X', 'SA')
                        COND_EARM_PAC_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/con_earm_sql.sql", 'w')
                file.write(COND_EARM_PAC_STRING)
                file.close()

                list_SA_similar_OFFSET = ["OFFSET_TO_OPEX", "LOAN_REPAY_RCVD"]
                list_SA_similar_REF_FED_CAN = ["REF_TO_FED_CAN"]
                list_SA_similar_OTH_REC = ["OTH_REC", "OTH_REC_DEBT"]
                list_SA_similar_REF_NFED_CAN = ["REF_TO_OTH_CMTE"]

                SA_OTHER_STRING = ""
                for tran in list_SA_similar_OFFSET:

                        query = """
                        SELECT COALESCE(t1.line_number, '''') AS "lineNumber", COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
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
                        # SA_OTHER_STRING += """
                        # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        # AND form_type = '{2}' AND sched_type = '{3}';\n
                        # """.format(query, tran, 'F3X', 'SA')
                        SA_OTHER_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SA_similar_OTH_REC:

                        query = """
                        SELECT COALESCE(t1.line_number, '''') AS "lineNumber", COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
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
                        # SA_OTHER_STRING += """
                        # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        # AND form_type = '{2}' AND sched_type = '{3}';\n
                        # """.format(query, tran, 'F3X', 'SA')
                        SA_OTHER_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SA_similar_REF_NFED_CAN:

                        query = """
                        SELECT COALESCE(t1.line_number, '''') AS "lineNumber", COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
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
                        # SA_OTHER_STRING += """
                        # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        # AND form_type = '{2}' AND sched_type = '{3}';\n
                        # """.format(query, tran, 'F3X', 'SA')
                        SA_OTHER_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SA_similar_REF_FED_CAN:

                        query = """
                        SELECT COALESCE(t1.line_number, '''') AS "lineNumber", COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
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
                        # SA_OTHER_STRING += """
                        # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        # AND form_type = '{2}' AND sched_type = '{3}';\n
                        # """.format(query, tran, 'F3X', 'SA')
                        SA_OTHER_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

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
                        SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                        COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                        t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                        COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", 
                        t1.expenditure_amount AS "expenditureAmount",
                        COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription", 
                        COALESCE(t1.category_code, '''') AS "categoryCode",
                        COALESCE(t1.memo_code, '''') AS "memoCode", 
                        COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", 
                        COALESCE(t2.last_name, '''') AS "payeeLastName", 
                        COALESCE(t2.first_name, '''') AS "payeeFirstName",
                        COALESCE(t2.middle_name, '''') AS "payeeMiddleName", 
                        COALESCE(t2.preffix, '''') AS "payeePrefix", 
                        COALESCE(t2.suffix, '''') AS "payeeSuffix",
                        COALESCE(t2.street_1, '''') AS "payeeStreet1", 
                        COALESCE(t2.street_2, '''') AS "payeeStreet2", 
                        COALESCE(t2.city, '''') AS "payeeCity",
                        COALESCE(t2.state, '''') AS "payeeState", 
                        COALESCE(t2.zip_code, '''') AS "payeeZipCode"
                        FROM public.sched_b t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                        # SB_SA_CHILD_STRING += """
                        # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        # AND form_type = '{2}' AND sched_type = '{3}';\n
                        # """.format(query, tran, 'F3X', 'SB')
                        SB_SA_CHILD_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SB', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SB_similar_IK_TF_OUT:

                        query = """
                        SELECT COALESCE(t1.line_number, '''') AS "lineNumber", COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", t1.expenditure_amount AS "expenditureAmount",
                        COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription", COALESCE(t1.category_code, '''') AS "categoryCode",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                        COALESCE(t2.street_1, '''') AS "payeeStreet1", COALESCE(t2.street_2, '''') AS "payeeStreet2", COALESCE(t2.city, '''') AS "payeeCity",
                        COALESCE(t2.state, '''') AS "payeeState", COALESCE(t2.zip_code, '''') AS "payeeZipCode"
                        FROM public.sched_b t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        # SB_SA_CHILD_STRING += """
                        # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        # AND form_type = '{2}' AND sched_type = '{3}';\n
                        # """.format(query, tran, 'F3X', 'SB')
                        SB_SA_CHILD_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SB', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SB_similar_EAR_OUT:

                        query = """
                        SELECT COALESCE(t1.line_number, '''') AS "lineNumber", COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
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
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                        COALESCE(t2.street_1, '''') AS "payeeStreet1", COALESCE(t2.street_2, '''') AS "payeeStreet2", COALESCE(t2.city, '''') AS "payeeCity",
                        COALESCE(t2.state, '''') AS "payeeState", COALESCE(t2.zip_code, '''') AS "payeeZipCode"
                        FROM public.sched_b t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        LEFT JOIN public.candidate_master t3 ON t3.cand_id = t1.beneficiary_cand_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        # SB_SA_CHILD_STRING += """
                        # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        # AND form_type = '{2}' AND sched_type = '{3}';\n
                        # """.format(query, tran, 'F3X', 'SB')
                        SB_SA_CHILD_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SB', '{0}', '{1}');\n""".format(tran, query)

                for tran in list_SB_similar_IK_OUT_PTY:

                        query = """
                        SELECT COALESCE(t1.line_number, '''') AS "lineNumber", COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", t1.transaction_type_identifier AS "transactionTypeIdentifier",
                        t1.transaction_id AS "transactionId",
                        COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                        to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", t1.expenditure_amount AS "expenditureAmount", COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                        COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription", COALESCE(t1.category_code, '''') AS "categoryCode",
                        COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                        COALESCE(t1.memo_code, '''') AS "memoCode", COALESCE(t1.memo_text, '''') AS "memoDescription",
                        COALESCE(t2.entity_type, '''') AS "entityType", COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                        COALESCE(t2.street_1, '''') AS "payeeStreet1", COALESCE(t2.street_2, '''') AS "payeeStreet2", COALESCE(t2.city, '''') AS "payeeCity",
                        COALESCE(t2.state, '''') AS "payeeState", COALESCE(t2.zip_code, '''') AS "payeeZipCode"
                        FROM public.sched_b t1
                        LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                        WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                        (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                        """.format(tran)
                        # SB_SA_CHILD_STRING += """
                        # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                        # AND form_type = '{2}' AND sched_type = '{3}';\n
                        # """.format(query, tran, 'F3X', 'SB')
                        SB_SA_CHILD_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SB', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/sb_sa_child_sql.sql", 'w')
                file.write(SB_SA_CHILD_STRING)
                file.close()

                file = open("/tmp/SA_sql.sql", 'w')
                file.write(INDV_REC_STRING)
                file.write(SB_SA_CHILD_STRING)
                file.write(PAR_CON_STRING)
                file.write(COND_EARM_PAC_STRING)
                file.write(SA_OTHER_STRING)
                file.close()

                List_SB_similar_OPEX_REC = ['OPEXP', 'OPEXP_CC_PAY_MEMO', 'OPEXP_STAF_REIM', 'OPEXP_STAF_REIM_MEMO', 'OPEXP_PMT_TO_PROL_VOID', 'OTH_DISB', 
                'OTH_DISB_CC_PAY_MEMO', 'OTH_DISB_STAF_REIM', 'OTH_DISB_STAF_REIM_MEMO', 'OPEXP_HQ_ACC_OP_EXP_NP', 
                'OPEXP_CONV_ACC_OP_EXP_NP', 'OTH_DISB_NC_ACC', 'OTH_DISB_NC_ACC_CC_PAY_MEMO', 'OTH_DISB_NC_ACC_STAF_REIM', 
                'OTH_DISB_NC_ACC_STAF_REIM_MEMO', 'OTH_DISB_NC_ACC_PMT_TO_PROL_VOID', 'OPEXP_DEBT', 'OTH_DISB_DEBT', 'LOAN_REPAY_MADE', 'LOANS_MADE']

                OPEX_REC_STRING = ""
                for tran in List_SB_similar_OPEX_REC:
                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
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
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)
            
                    OPEX_REC_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/opex_rec_sql.sql", 'w')
                file.write(OPEX_REC_STRING)
                file.close()

                List_SB_similar_OPEX__CC = ['OPEXP_CC_PAY','OPEXP_PMT_TO_PROL','OTH_DISB_CC_PAY','OTH_DISB_PMT_TO_PROL','OTH_DISB_RECNT', 
                'OTH_DISB_NP_RECNT_ACC', 'OTH_DISB_NC_ACC_CC_PAY', 'OTH_DISB_NC_ACC_PMT_TO_PROL', 'OPEXP_HQ_ACC_TRIB_REF', 
                'OPEXP_CONV_ACC_TRIB_REF', 'OTH_DISB_NP_RECNT_TRIB_REF']


                OPEX__CC_STRING = ""
                for tran in List_SB_similar_OPEX__CC:
                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",

                    COALESCE(t2.entity_type, '''') AS "entityType", 
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
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
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)
                    #print(query)
                    OPEX__CC_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n
                    """.format(tran, query)
      
                file = open("/tmp/opex_cc_sql.sql", 'w')
                file.write(OPEX__CC_STRING)
                file.close()

                List_SB_similar_PAY_MEMO = ['OPEXP_PMT_TO_PROL_MEMO','REF_CONT_IND', 'REF_CONT_IND_VOID','OTH_DISB_PMT_TO_PROL_MEMO', 
                'OTH_DISB_NC_ACC_PMT_TO_PROL_MEMO', 'OPEXP_HQ_ACC_IND_REF', 'OPEXP_CONV_ACC_IND_REF', 'OTH_DISB_NP_RECNT_IND_REF']

                PAY_MEMO_STRING = ""
                for tran in List_SB_similar_PAY_MEMO:
                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",

                    COALESCE(t2.entity_type, '''') AS "entityType", 
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
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    PAY_MEMO_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/pay_memo_sql.sql", 'w')
                file.write(PAY_MEMO_STRING)
                file.close()

                List_SB_similar_OPEX_TRAN = ['TRAN_TO_AFFI', 'CONT_TO_OTH_CMTE', 'REF_CONT_PARTY', 'REF_CONT_PARTY_VOID', 'OPEXP_HQ_ACC_REG_REF', 
                'OPEXP_CONV_ACC_REG_REF', 'OTH_DISB_NP_RECNT_REG_REF']

                OPEX_TRAN_STRING = ""
                for tran in List_SB_similar_OPEX_TRAN:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",

                    COALESCE(t2.entity_type, '''') AS "entityType", 
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                    COALESCE(t2.street_1, '''') AS "payeeStreet1", 
                    COALESCE(t2.street_2, '''') AS "payeeStreet2", 
                    COALESCE(t2.city, '''') AS "payeeCity",
                    COALESCE(t2.state, '''') AS "payeeState", 
                    COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                    to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", 
                    t1.expenditure_amount AS "expenditureAmount",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", 
                    COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_b t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    OPEX_TRAN_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/opex_tran_sql.sql", 'w')
                file.write(OPEX_TRAN_STRING)
                file.close()
                
                List_SB_similar_NONFED_PAC_RFD = ['REF_CONT_PAC', 'REF_CONT_NON_FED']

                NONFED_PAC_RFD_STRING = ""
                for tran in List_SB_similar_NONFED_PAC_RFD:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",

                    COALESCE(t2.entity_type, '''') AS "entityType", 
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                    COALESCE(t2.street_1, '''') AS "payeeStreet1", 
                    COALESCE(t2.street_2, '''') AS "payeeStreet2", 
                    COALESCE(t2.city, '''') AS "payeeCity",
                    COALESCE(t2.state, '''') AS "payeeState", 
                    COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                    to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", 
                    t1.expenditure_amount AS "expenditureAmount",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", 
                    COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                    COALESCE(t1.beneficiary_cand_id, '''') AS "beneficiaryCandidateId",
                    COALESCE(t3.cand_last_name, '''') AS "beneficiaryCandidateLastName", 
                    COALESCE(t3.cand_first_name, '''') AS "beneficiaryCandidateFirstName", 
                    COALESCE(t3.cand_middle_name, '''') AS "beneficiaryCandidateMiddleName", 
                    COALESCE(t3.cand_prefix, '''') AS "beneficiaryCandidatePrefix",
                    COALESCE(t3.cand_suffix, '''') AS "beneficiaryCandidateSuffix",
                    COALESCE(t3.cand_office, '''') AS "beneficiaryCandidateOffice",
                    COALESCE(t3.cand_office_state, '''') AS "beneficiaryCandidateState",
                    COALESCE(t3.cand_office_district, '''') AS "beneficiaryCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_b t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    LEFT JOIN public.candidate_master t3 ON t3.cand_id = t1.beneficiary_cand_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    NONFED_PAC_RFD_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/nonfed_pac_sql.sql", 'w')
                file.write(NONFED_PAC_RFD_STRING)
                file.close()
               
                List_SB_similar_CONTR_CAND = ['CONT_TO_CAN', 'CONT_TO_OTH_CMTE_VOID']
                #import ipdb;ipdb.set_trace()
                CONTR_CAND_STRING = ""
                for tran in List_SB_similar_CONTR_CAND:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",

                    COALESCE(t2.entity_type, '''') AS "entityType", 
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                    COALESCE(t2.street_1, '''') AS "payeeStreet1", 
                    COALESCE(t2.street_2, '''') AS "payeeStreet2", 
                    COALESCE(t2.city, '''') AS "payeeCity",
                    COALESCE(t2.state, '''') AS "payeeState", 
                    COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                    COALESCE(t1.election_code, '''') AS "electionCode", 
                    COALESCE(t1.election_other_description, '''') AS "electionOtherDescription",
                    to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", 
                    t1.expenditure_amount AS "expenditureAmount",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", 
                    COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                    COALESCE(t1.beneficiary_cand_id, '''') AS "beneficiaryCandidateId",
                    COALESCE(t3.cand_last_name, '''') AS "beneficiaryCandidateLastName", 
                    COALESCE(t3.cand_first_name, '''') AS "beneficiaryCandidateFirstName", 
                    COALESCE(t3.cand_middle_name, '''') AS "beneficiaryCandidateMiddleName", 
                    COALESCE(t3.cand_prefix, '''') AS "beneficiaryCandidatePrefix",
                    COALESCE(t3.cand_suffix, '''') AS "beneficiaryCandidateSuffix",
                    COALESCE(t3.cand_office, '''') AS "beneficiaryCandidateOffice",
                    COALESCE(t3.cand_office_state, '''') AS "beneficiaryCandidateState",
                    COALESCE(t3.cand_office_district, '''') AS "beneficiaryCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_b t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    LEFT JOIN public.candidate_master t3 ON t3.cand_id = t1.beneficiary_cand_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)
                    
                    CONTR_CAND_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/contr_can_sql.sql", 'w')
                file.write(CONTR_CAND_STRING)
                file.close()

                List_SB_similar_VOID_RFND_PAC = ['REF_CONT_PAC_VOID', 'REF_CONT_NON_FED_VOID']

                VOID_RFND_PAC_STRING = ""
                for tran in List_SB_similar_VOID_RFND_PAC:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",

                    COALESCE(t2.entity_type, '''') AS "entityType", 
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                    COALESCE(t2.street_1, '''') AS "payeeStreet1", 
                    COALESCE(t2.street_2, '''') AS "payeeStreet2", 
                    COALESCE(t2.city, '''') AS "payeeCity",
                    COALESCE(t2.state, '''') AS "payeeState", 
                    COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                    to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", 
                    t1.expenditure_amount AS "expenditureAmount",
                    t1.semi_annual_refund_bundled_amount AS "semiAnnualRefundedBundledAmount",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", 
                    COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                    COALESCE(t1.beneficiary_cand_id, '''') AS "beneficiaryCandidateId",
                    COALESCE(t3.cand_last_name, '''') AS "beneficiaryCandidateLastName", 
                    COALESCE(t3.cand_first_name, '''') AS "beneficiaryCandidateFirstName", 
                    COALESCE(t3.cand_middle_name, '''') AS "beneficiaryCandidateMiddleName", 
                    COALESCE(t3.cand_prefix, '''') AS "beneficiaryCandidatePrefix",
                    COALESCE(t3.cand_suffix, '''') AS "beneficiaryCandidateSuffix",
                    COALESCE(t3.cand_office, '''') AS "beneficiaryCandidateOffice",
                    COALESCE(t3.cand_office_state, '''') AS "beneficiaryCandidateState",
                    COALESCE(t3.cand_office_district, '''') AS "beneficiaryCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_b t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    LEFT JOIN public.candidate_master t3 ON t3.cand_id = t1.beneficiary_cand_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    VOID_RFND_PAC_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/void_pac_sql.sql", 'w')
                file.write(VOID_RFND_PAC_STRING)
                file.close()

                List_SB_similar_FEA_PAYM = ['FEA_100PCT_PAY']

                FEA_PAYM_STRING = ""
                for tran in List_SB_similar_FEA_PAYM:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
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
                    COALESCE(t1.election_code, '''') AS "electionCode", 
                    COALESCE(t1.election_other_description, '''') AS "electionOtherDescription",
                    to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", 
                    t1.expenditure_amount AS "expenditureAmount",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", 
                    COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                    COALESCE(t1.beneficiary_cand_id, '''') AS "beneficiaryCandidateId",
                    COALESCE(t3.cand_last_name, '''') AS "beneficiaryCandidateLastName", 
                    COALESCE(t3.cand_first_name, '''') AS "beneficiaryCandidateFirstName", 
                    COALESCE(t3.cand_middle_name, '''') AS "beneficiaryCandidateMiddleName", 
                    COALESCE(t3.cand_prefix, '''') AS "beneficiaryCandidatePrefix",
                    COALESCE(t3.cand_suffix, '''') AS "beneficiaryCandidateSuffix",
                    COALESCE(t3.cand_office, '''') AS "beneficiaryCandidateOffice",
                    COALESCE(t3.cand_office_state, '''') AS "beneficiaryCandidateState",
                    COALESCE(t3.cand_office_district, '''') AS "beneficiaryCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_b t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    LEFT JOIN public.candidate_master t3 ON t3.cand_id = t1.beneficiary_cand_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    FEA_PAYM_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/fea_apym_sql.sql", 'w')
                file.write(FEA_PAYM_STRING)
                file.close()

                List_SB_similar_FEA_CC = ['FEA_PAY_TO_PROL', 'FEA_CC_PAY']

                FEA_CC_STRING = ""
                for tran in List_SB_similar_FEA_CC:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",

                    COALESCE(t2.entity_type, '''') AS "entityType", 
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                    COALESCE(t2.street_1, '''') AS "payeeStreet1", 
                    COALESCE(t2.street_2, '''') AS "payeeStreet2", 
                    COALESCE(t2.city, '''') AS "payeeCity",
                    COALESCE(t2.state, '''') AS "payeeState", 
                    COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                    COALESCE(t1.election_code, '''') AS "electionCode", 
                    COALESCE(t1.election_other_description, '''') AS "electionOtherDescription",
                    to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", 
                    t1.expenditure_amount AS "expenditureAmount",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", 
                    COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                    COALESCE(t1.beneficiary_cand_id, '''') AS "beneficiaryCandidateId",
                    COALESCE(t3.cand_last_name, '''') AS "beneficiaryCandidateLastName", 
                    COALESCE(t3.cand_first_name, '''') AS "beneficiaryCandidateFirstName", 
                    COALESCE(t3.cand_middle_name, '''') AS "beneficiaryCandidateMiddleName", 
                    COALESCE(t3.cand_prefix, '''') AS "beneficiaryCandidatePrefix",
                    COALESCE(t3.cand_suffix, '''') AS "beneficiaryCandidateSuffix",
                    COALESCE(t3.cand_office, '''') AS "beneficiaryCandidateOffice",
                    COALESCE(t3.cand_office_state, '''') AS "beneficiaryCandidateState",
                    COALESCE(t3.cand_office_district, '''') AS "beneficiaryCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_b t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    LEFT JOIN public.candidate_master t3 ON t3.cand_id = t1.beneficiary_cand_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    FEA_CC_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/fea_rcc_sql.sql", 'w')
                file.write(FEA_CC_STRING)
                file.close()

                List_SB_similar_FEA_CC_MEMO = ['FEA_CC_PAY_MEMO', 'FEA_STAF_REIM', 'FEA_STAF_REIM_MEMO', 'FEA_PAY_TO_PROL_VOID', 'FEA_100PCT_DEBT_PAY', 
                    'PAC_CON_EAR_DEP_MEMO']

                FEA_CC_MEMO_STRING = ""
                for tran in List_SB_similar_FEA_CC_MEMO:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
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
                    COALESCE(t1.election_code, '''') AS "electionCode", 
                    COALESCE(t1.election_other_description, '''') AS "electionOtherDescription",
                    to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", 
                    t1.expenditure_amount AS "expenditureAmount",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", 
                    COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                    COALESCE(t1.beneficiary_cand_id, '''') AS "beneficiaryCandidateId",
                    COALESCE(t3.cand_last_name, '''') AS "beneficiaryCandidateLastName", 
                    COALESCE(t3.cand_first_name, '''') AS "beneficiaryCandidateFirstName", 
                    COALESCE(t3.cand_middle_name, '''') AS "beneficiaryCandidateMiddleName", 
                    COALESCE(t3.cand_prefix, '''') AS "beneficiaryCandidatePrefix",
                    COALESCE(t3.cand_suffix, '''') AS "beneficiaryCandidateSuffix",
                    COALESCE(t3.cand_office, '''') AS "beneficiaryCandidateOffice",
                    COALESCE(t3.cand_office_state, '''') AS "beneficiaryCandidateState",
                    COALESCE(t3.cand_office_district, '''') AS "beneficiaryCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_b t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    LEFT JOIN public.candidate_master t3 ON t3.cand_id = t1.beneficiary_cand_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    FEA_CC_MEMO_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/fea_cc_memo_sql.sql", 'w')
                file.write(FEA_CC_MEMO_STRING)
                file.close()

                List_SB_similar_FEA_PAY_MEMO = ['FEA_PAY_TO_PROL_MEMO']

                FEA_PAY_MEMO_STRING = ""
                for tran in List_SB_similar_FEA_PAY_MEMO:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",

                    COALESCE(t2.entity_type, '''') AS "entityType", 
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
                    COALESCE(t1.election_code, '''') AS "electionCode", 
                    COALESCE(t1.election_other_description, '''') AS "electionOtherDescription",
                    to_char(t1.expenditure_date,''MM/DD/YYYY'') AS "expenditureDate", 
                    t1.expenditure_amount AS "expenditureAmount",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.beneficiary_cmte_id, '''') AS "beneficiaryCommitteeId", 
                    COALESCE(t1.beneficiary_cmte_name, '''') AS "beneficiaryCommitteeName",
                    COALESCE(t1.beneficiary_cand_id, '''') AS "beneficiaryCandidateId",
                    COALESCE(t3.cand_last_name, '''') AS "beneficiaryCandidateLastName", 
                    COALESCE(t3.cand_first_name, '''') AS "beneficiaryCandidateFirstName", 
                    COALESCE(t3.cand_middle_name, '''') AS "beneficiaryCandidateMiddleName", 
                    COALESCE(t3.cand_prefix, '''') AS "beneficiaryCandidatePrefix",
                    COALESCE(t3.cand_suffix, '''') AS "beneficiaryCandidateSuffix",
                    COALESCE(t3.cand_office, '''') AS "beneficiaryCandidateOffice",
                    COALESCE(t3.cand_office_state, '''') AS "beneficiaryCandidateState",
                    COALESCE(t3.cand_office_district, '''') AS "beneficiaryCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_b t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    LEFT JOIN public.candidate_master t3 ON t3.cand_id = t1.beneficiary_cand_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    FEA_PAY_MEMO_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SB', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/fea_pay_memo_sql.sql", 'w')
                file.write(FEA_PAY_MEMO_STRING)
                file.close()

                file = open("/tmp/SB_sql.sql", 'w')
                file.write(OPEX_REC_STRING)
                file.write(OPEX__CC_STRING)
                file.write(PAY_MEMO_STRING)
                file.write(OPEX_TRAN_STRING)
                file.write(NONFED_PAC_RFD_STRING)
                file.write(CONTR_CAND_STRING)
                file.write(VOID_RFND_PAC_STRING)
                file.write(FEA_PAYM_STRING)
                file.write(FEA_CC_STRING)
                file.write(FEA_CC_MEMO_STRING)
                file.write(FEA_PAY_MEMO_STRING)
                file.close()

                List_SE_similar_IE = ['IE', 'IE_CC_PAY_MEMO', 'IE_STAF_REIM_MEMO', 'IE_VOID', 'IE_B4_DISSE_MEMO']
                IE_STRING = ""
                for tran in List_SE_similar_IE:
                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",  
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
                    COALESCE(t1.election_code, '''') AS "electionCode", 
                    COALESCE(t1.election_other_desc, '''') AS "electionOtherDescription",
                    COALESCE(to_char(t1.dissemination_date, ''MM/DD/YYYY''), '''') AS "disseminationDate",
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(to_char(t1.disbursement_date,''MM/DD/YYYY''), '''') AS "disbursementDate",
                    COALESCE(t1.calendar_ytd_amount, 0.0) AS "calendarYTDPerElectionForOffice",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.support_oppose_code, '''') AS "support/opposeCode",
                    COALESCE(t1.so_cand_id, '''') AS "candidateId",
                    COALESCE(t1.so_cand_last_name, '''') AS "candidateLastName", 
                    COALESCE(t1.so_cand_fist_name, '''') AS "candidateFirstName", 
                    COALESCE(t1.so_cand_middle_name, '''') AS "candidateMiddleName", 
                    COALESCE(t1.so_cand_prefix, '''') AS "candidatePrefix",
                    COALESCE(t1.so_cand_suffix, '''') AS "candidateSuffix",
                    COALESCE(t1.so_cand_office, '''') AS "candidateOffice",
                    COALESCE(t1.so_cand_state, '''') AS "candidateState",
                    COALESCE(t1.so_cand_district, '''') AS "candidateDistrict",
                    COALESCE(t3.last_name, '''') AS "completingLastName", 
                    COALESCE(t3.first_name, '''') AS "completingFirstName",
                    COALESCE(t3.middle_name, '''') AS "completingMiddleName", 
                    COALESCE(t3.preffix, '''') AS "completingPrefix", 
                    COALESCE(t3.suffix, '''') AS "completingSuffix",
                    COALESCE(to_char(t1.date_signed,''MM/DD/YYYY''), '''') AS "dateSigned",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_e t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    LEFT JOIN public.entity t3 ON t3.entity_id = t1.completing_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    IE_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SE', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/IE_sql.sql", 'w')
                file.write(IE_STRING)
                file.close()

                List_SE_similar_IE_CC = ['IE_CC_PAY', 'IE_PMT_TO_PROL']
                IE_CC_STRING = ""
                for tran in List_SE_similar_IE_CC:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t2.entity_type, '''') AS "entityType", 
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                    COALESCE(t2.street_1, '''') AS "payeeStreet1", 
                    COALESCE(t2.street_2, '''') AS "payeeStreet2", 
                    COALESCE(t2.city, '''') AS "payeeCity",
                    COALESCE(t2.state, '''') AS "payeeState", 
                    COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                    COALESCE(t1.election_code, '''') AS "electionCode",
                    COALESCE(t1.election_code, '''') AS "electionCode",
                    COALESCE(t1.election_other_desc, '''') AS "electionOtherDescription",
                    COALESCE(to_char(t1.dissemination_date, ''MM/DD/YYYY''), '''') AS "disseminationDate",
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(to_char(t1.disbursement_date,''MM/DD/YYYY''), '''') AS "disbursementDate",
                    COALESCE(t1.calendar_ytd_amount, 0.0) AS "calendarYTDPerElectionForOffice",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.support_oppose_code, '''') AS "support/opposeCode",
                    COALESCE(t1.so_cand_id, '''') AS "candidateId",
                    COALESCE(t1.so_cand_last_name, '''') AS "candidateLastName", 
                    COALESCE(t1.so_cand_fist_name, '''') AS "candidateFirstName", 
                    COALESCE(t1.so_cand_middle_name, '''') AS "candidateMiddleName", 
                    COALESCE(t1.so_cand_prefix, '''') AS "candidatePrefix",
                    COALESCE(t1.so_cand_suffix, '''') AS "candidateSuffix",
                    COALESCE(t1.so_cand_office, '''') AS "candidateOffice",
                    COALESCE(t1.so_cand_state, '''') AS "candidateState",
                    COALESCE(t1.so_cand_district, '''') AS "candidateDistrict",
                    COALESCE(t3.last_name, '''') AS "completingLastName", 
                    COALESCE(t3.first_name, '''') AS "completingFirstName",
                    COALESCE(t3.middle_name, '''') AS "completingMiddleName", 
                    COALESCE(t3.preffix, '''') AS "completingPrefix", 
                    COALESCE(t3.suffix, '''') AS "completingSuffix",
                    COALESCE(to_char(t1.date_signed,''MM/DD/YYYY''), '''') AS "dateSigned",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_e t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    LEFT JOIN public.entity t3 ON t3.entity_id = t1.completing_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    IE_CC_STRING  += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SE', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/IE_CC_sql.sql", 'w')
                file.write(IE_CC_STRING)
                file.close()


                List_SE_similar_IE_STAF_REIM = ['IE_STAF_REIM', 'IE_PMT_TO_PROL_MEMO']
                IE_STAF_REIM_STRING = ""
                for tran in List_SE_similar_IE_STAF_REIM:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t2.entity_type, '''') AS "entityType",
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
                    COALESCE(t1.election_code, '''') AS "electionCode", 
                    COALESCE(t1.election_other_desc, '''') AS "electionOtherDescription",
                    COALESCE(to_char(t1.dissemination_date, ''MM/DD/YYYY''), '''') AS "disseminationDate",
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(to_char(t1.disbursement_date,''MM/DD/YYYY''), '''') AS "disbursementDate",
                    COALESCE(t1.calendar_ytd_amount, 0.0) AS "calendarYTDPerElectionForOffice",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.support_oppose_code, '''') AS "support/opposeCode",
                    COALESCE(t1.so_cand_id, '''') AS "candidateId",
                    COALESCE(t1.so_cand_last_name, '''') AS "candidateLastName", 
                    COALESCE(t1.so_cand_fist_name, '''') AS "candidateFirstName", 
                    COALESCE(t1.so_cand_middle_name, '''') AS "candidateMiddleName", 
                    COALESCE(t1.so_cand_prefix, '''') AS "candidatePrefix",
                    COALESCE(t1.so_cand_suffix, '''') AS "candidateSuffix",
                    COALESCE(t1.so_cand_office, '''') AS "candidateOffice",
                    COALESCE(t1.so_cand_state, '''') AS "candidateState",
                    COALESCE(t1.so_cand_district, '''') AS "candidateDistrict",
                    COALESCE(t3.last_name, '''') AS "completingLastName", 
                    COALESCE(t3.first_name, '''') AS "completingFirstName",
                    COALESCE(t3.middle_name, '''') AS "completingMiddleName", 
                    COALESCE(t3.preffix, '''') AS "completingPrefix", 
                    COALESCE(t3.suffix, '''') AS "completingSuffix",
                    COALESCE(to_char(t1.date_signed,''MM/DD/YYYY''), '''') AS "dateSigned",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_e t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    LEFT JOIN public.entity t3 ON t3.entity_id = t1.completing_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    IE_STAF_REIM_STRING+= """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SE', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/IE_STAF_REIM_sql.sql", 'w')
                file.write(IE_STAF_REIM_STRING)
                file.close()

                file = open("/tmp/SE_sql.sql", 'w')
                file.write(IE_STRING)
                file.write(IE_CC_STRING)
                file.write(IE_STAF_REIM_STRING)
                file.close()

                List_SF_similar_CORD_EXP = ['COEXP_PARTY', 'COEXP_PARTY_DEBT']
                CORD_EXP_STRING = ""
                for tran in List_SF_similar_CORD_EXP:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",  
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t1.coordinated_exp_ind, '''') AS "coordinateExpenditure",
                    COALESCE(t1.designating_cmte_id, '''') AS "designatingCommitteeId",
                    COALESCE(t1.designating_cmte_name, '''') AS "designatingCommitteeName",
                    COALESCE(t1.subordinate_cmte_id, '''') AS "subordinateCommitteeId",
                    COALESCE(t1.subordinate_cmte_name, '''') AS "subordinateCommitteeName",
                    COALESCE(t1.subordinate_cmte_street_1, '''') AS "subordinateCommitteeStreet1",
                    COALESCE(t1.subordinate_cmte_street_2, '''') AS "subordinateCommitteeStreet2",
                    COALESCE(t1.subordinate_cmte_city, '''') AS "subordinateCommitteeCity",
                    COALESCE(t1.subordinate_cmte_state, '''') AS "subordinateCommitteeState",
                    COALESCE(t1.subordinate_cmte_zip,  '''') AS "subordinateCommitteeZipCode",
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
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(t1.aggregate_general_elec_exp, 0.0) AS "aggregateGeneralElectionExpended",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.payee_cand_id, '''') AS "candidateId",
                    COALESCE(t1.payee_cand_last_name, '''') AS "payeeCandidateLastName", 
                    COALESCE(t1.payee_cand_fist_name, '''') AS "payeeCandidateFirstName", 
                    COALESCE(t1.payee_cand_middle_name, '''') AS "payeeCandidateMiddleName", 
                    COALESCE(t1.payee_cand_prefix, '''') AS "payeeCandidatePrefix",
                    COALESCE(t1.payee_cand_suffix, '''') AS "payeeCandidateSuffix",
                    COALESCE(t1.payee_cand_office, '''') AS "payeeCandidateOffice",
                    COALESCE(t1.payee_cand_state, '''') AS "payeeCandidateState",
                    COALESCE(t1.payee_cand_district, '''') AS "payeeCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_f t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    CORD_EXP_STRING+= """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SF', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/CORD_EXP_sql.sql", 'w')
                file.write(CORD_EXP_STRING)
                file.close()


                List_SF_similar_CORD_EXP_CC = ['COEXP_CC_PAY', 'COEXP_PMT_PROL']

                CORD_EXP_CC_STRING = ""
                for tran in List_SF_similar_CORD_EXP_CC:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",  
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t1.coordinated_exp_ind, '''') AS "coordinateExpenditure",
                    COALESCE(t1.designating_cmte_id, '''') AS "designatingCommitteeId",
                    COALESCE(t1.designating_cmte_name, '''') AS "designatingCommitteeName",
                    COALESCE(t1.subordinate_cmte_id, '''') AS "subordinateCommitteeId",
                    COALESCE(t1.subordinate_cmte_name, '''') AS "subordinateCommitteeName",
                    COALESCE(t1.subordinate_cmte_street_1, '''') AS "subordinateCommitteeStreet1",
                    COALESCE(t1.subordinate_cmte_street_2, '''') AS "subordinateCommitteeStreet2",
                    COALESCE(t1.subordinate_cmte_city, '''') AS "subordinateCommitteeCity",
                    COALESCE(t1.subordinate_cmte_state, '''') AS "subordinateCommitteeState",
                    COALESCE(t1.subordinate_cmte_zip,  '''') AS "subordinateCommitteeZipCode",
                    COALESCE(t2.entity_type, '''') AS "entityType",
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                    COALESCE(t2.street_1, '''') AS "payeeStreet1", 
                    COALESCE(t2.street_2, '''') AS "payeeStreet2", 
                    COALESCE(t2.city, '''') AS "payeeCity",
                    COALESCE(t2.state, '''') AS "payeeState", 
                    COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(t1.aggregate_general_elec_exp, 0.0) AS "aggregateGeneralElectionExpended",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.payee_cand_id, '''') AS "candidateId",
                    COALESCE(t1.payee_cand_last_name, '''') AS "payeeCandidateLastName", 
                    COALESCE(t1.payee_cand_fist_name, '''') AS "payeeCandidateFirstName", 
                    COALESCE(t1.payee_cand_middle_name, '''') AS "payeeCandidateMiddleName", 
                    COALESCE(t1.payee_cand_prefix, '''') AS "payeeCandidatePrefix",
                    COALESCE(t1.payee_cand_suffix, '''') AS "payeeCandidateSuffix",
                    COALESCE(t1.payee_cand_office, '''') AS "payeeCandidateOffice",
                    COALESCE(t1.payee_cand_state, '''') AS "payeeCandidateState",
                    COALESCE(t1.payee_cand_district, '''') AS "payeeCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_f t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    CORD_EXP_STRING+= """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SF', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/CORD_EXP_CC_sql.sql", 'w')
                file.write(CORD_EXP_CC_STRING)
                file.close()

                List_SF_similar_CORD_CC_MEMO = ['COEXP_CC_PAY_MEMO', 'COEXP_STAF_REIM_MEMO', 'COEXP_PARTY_VOID']

                CORD_CC_MEMO_STRING = ""
                for tran in List_SF_similar_CORD_CC_MEMO:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t1.coordinated_exp_ind, '''') AS "coordinateExpenditure",
                    COALESCE(t1.designating_cmte_id, '''') AS "designatingCommitteeId",
                    COALESCE(t1.designating_cmte_name, '''') AS "designatingCommitteeName",
                    COALESCE(t1.subordinate_cmte_id, '''') AS "subordinateCommitteeId",
                    COALESCE(t1.subordinate_cmte_name, '''') AS "subordinateCommitteeName",
                    COALESCE(t1.subordinate_cmte_street_1, '''') AS "subordinateCommitteeStreet1",
                    COALESCE(t1.subordinate_cmte_street_2, '''') AS "subordinateCommitteeStreet2",
                    COALESCE(t1.subordinate_cmte_city, '''') AS "subordinateCommitteeCity",
                    COALESCE(t1.subordinate_cmte_state, '''') AS "subordinateCommitteeState",
                    COALESCE(t1.subordinate_cmte_zip,  '''') AS "subordinateCommitteeZipCode",
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
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(t1.aggregate_general_elec_exp, 0.0) AS "aggregateGeneralElectionExpended",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.payee_cand_id, '''') AS "candidateId",
                    COALESCE(t1.payee_cand_last_name, '''') AS "payeeCandidateLastName", 
                    COALESCE(t1.payee_cand_fist_name, '''') AS "payeeCandidateFirstName", 
                    COALESCE(t1.payee_cand_middle_name, '''') AS "payeeCandidateMiddleName", 
                    COALESCE(t1.payee_cand_prefix, '''') AS "payeeCandidatePrefix",
                    COALESCE(t1.payee_cand_suffix, '''') AS "payeeCandidateSuffix",
                    COALESCE(t1.payee_cand_office, '''') AS "payeeCandidateOffice",
                    COALESCE(t1.payee_cand_state, '''') AS "payeeCandidateState",
                    COALESCE(t1.payee_cand_district, '''') AS "payeeCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_f t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    CORD_CC_MEMO_STRING+= """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SF', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/CORD_CC_MEMO_sql.sql", 'w')
                file.write(CORD_CC_MEMO_STRING)
                file.close()

                List_SF_similar_CORD_REIM = ['COEXP_STAF_REIM', 'COEXP_PMT_PROL_MEMO']
                CORD_REIM_STRING = ""
                for tran in List_SF_similar_CORD_REIM:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t1.coordinated_exp_ind, '''') AS "coordinateExpenditure",
                    COALESCE(t1.designating_cmte_id, '''') AS "designatingCommitteeId",
                    COALESCE(t1.designating_cmte_name, '''') AS "designatingCommitteeName",
                    COALESCE(t1.subordinate_cmte_id, '''') AS "subordinateCommitteeId",
                    COALESCE(t1.subordinate_cmte_name, '''') AS "subordinateCommitteeName",
                    COALESCE(t1.subordinate_cmte_street_1, '''') AS "subordinateCommitteeStreet1",
                    COALESCE(t1.subordinate_cmte_street_2, '''') AS "subordinateCommitteeStreet2",
                    COALESCE(t1.subordinate_cmte_city, '''') AS "subordinateCommitteeCity",
                    COALESCE(t1.subordinate_cmte_state, '''') AS "subordinateCommitteeState",
                    COALESCE(t1.subordinate_cmte_zip,  '''') AS "subordinateCommitteeZipCode",
                    COALESCE(t2.entity_type, '''') AS "entityType",
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
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(t1.aggregate_general_elec_exp, 0.0) AS "aggregateGeneralElectionExpended",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.payee_cand_id, '''') AS "candidateId",
                    COALESCE(t1.payee_cand_last_name, '''') AS "payeeCandidateLastName", 
                    COALESCE(t1.payee_cand_fist_name, '''') AS "payeeCandidateFirstName", 
                    COALESCE(t1.payee_cand_middle_name, '''') AS "payeeCandidateMiddleName", 
                    COALESCE(t1.payee_cand_prefix, '''') AS "payeeCandidatePrefix",
                    COALESCE(t1.payee_cand_suffix, '''') AS "payeeCandidateSuffix",
                    COALESCE(t1.payee_cand_office, '''') AS "payeeCandidateOffice",
                    COALESCE(t1.payee_cand_state, '''') AS "payeeCandidateState",
                    COALESCE(t1.payee_cand_district, '''') AS "payeeCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_f t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    CORD_REIM_STRING+= """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SF', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/CORD_REIM_sql.sql", 'w')
                file.write(CORD_REIM_STRING)
                file.close()
                
                file = open("/tmp/SF_sql.sql", 'w')
                file.write(CORD_EXP_STRING)
                file.write(CORD_EXP_CC_STRING)
                file.write(CORD_CC_MEMO_STRING)
                file.write(CORD_REIM_STRING)
                file.close()

                List_SD_similar_DEBT= ['DEBT_TO_VENDOR', 'DEBT_BY_VENDOR']
                DEBT_STRING = ""
                for tran in List_SD_similar_DEBT:

                    query = """
                    SELECT COALESCE(t1.line_num, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    t1.transaction_type_identifier AS "transactionTypeIdentifier",
                    t1.transaction_id AS "transactionId",
                    COALESCE(t2.entity_type, '''') AS "entityType",
                    COALESCE(t2.entity_name, '''') AS "creditorOrganizationName",
                    COALESCE(t2.last_name, '''') AS "creditorLastName",
                    COALESCE(t2.first_name, '''') AS "creditorFirstName",
                    COALESCE(t2.middle_name, '''') AS "creditorMiddleName",
                    COALESCE(t2.preffix, '''') AS "creditorPrefix",
                    COALESCE(t2.suffix, '''') AS "creditorSuffix",
                    COALESCE(t2.street_1, '''') AS "creditorStreet1",
                    COALESCE(t2.street_2, '''') AS "creditorStreet2",
                    COALESCE(t2.city, '''') AS "creditorCity",
                    COALESCE(t2.state, '''') AS "creditorState",
                    COALESCE(t2.zip_code, '''') AS "creditorZipCode",
                    COALESCE(t1.purpose, '''') AS "purposeOfDebtOrObligation",
                    COALESCE(t1.beginning_balance, 0.0) AS "beginningBalance",
                    COALESCE(t1.incurred_amount, 0.0) AS "incurredAmount",
                    COALESCE(t1.payment_amount, 0.0) AS "paymentAmount",
                    COALESCE(t1.balance_at_close, 0.0) AS "balanceAtClose"
                    FROM public.sched_d t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    DEBT_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SD', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/SD_DEBT_STRING_sql.sql", 'w')
                file.write(DEBT_STRING)
                file.close()


                List_SH6_similar_ALLOC_FEA_DEBT_VEN= ['ALLOC_FEA_DISB_DEBT'] 
                ALLOC_FEA_DEBT_VEN_STRING = ""
                for tran in List_SH6_similar_ALLOC_FEA_DEBT_VEN:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
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
                    COALESCE(t1.account_event_identifier, '''') AS "accountEventIdentifier",
                    COALESCE(to_char(t1.expenditure_date,''MM/DD/YYYY''), '''') AS "expenditureDate",
                    COALESCE(t1.total_fed_levin_amount, 0.0) AS "totalFedLevinAmount",
                    COALESCE(t1.federal_share, 0.0) AS "federalShare",
                    COALESCE(t1.levin_share, 0.0) AS "levinShare",
                    COALESCE(t1.activity_event_total_ytd, 0.0) AS "activityEventTotalYTD",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.activity_event_type, '''') AS "activityEventType",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_h6 t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    ALLOC_FEA_DEBT_VEN_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SH6', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/SH6_ALLOC_FEA_DEBT_VEN_STRING_sql.sql", 'w')
                file.write(ALLOC_FEA_DEBT_VEN_STRING)
                file.close()

                List_SH4_similar_ALLOC_EXP_DEBT= ['ALLOC_EXP_DEBT']
                ALLOC_EXP_DEBT_STRING = ""
                for tran in List_SH4_similar_ALLOC_EXP_DEBT:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
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
                    COALESCE(t1.activity_event_identifier, '''') AS "accountEventIdentifier",
                    COALESCE(to_char(t1.expenditure_date,''MM/DD/YYYY''), '''') AS "expenditureDate",
                    COALESCE(t1.total_amount, 0.0) AS "totalFedNonfedAmount",
                    COALESCE(t1.fed_share_amount, 0.0) AS "federalShare",
                    COALESCE(t1.non_fed_share_amount, 0.0) AS "nonfederalShare",
                    COALESCE(t1.activity_event_amount_ytd, 0.0) AS "activityEventTotalYTD",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.activity_event_type, '''') AS "activityEventType",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_h4 t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    ALLOC_EXP_DEBT_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SH4', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/SH4_ALLOC_EXP_DEBT_STRING_sql.sql", 'w')
                file.write(ALLOC_EXP_DEBT_STRING)
                file.close()

                List_SC_similar_LOANS_OWED_BY_CMTE= ['LOANS_OWED_BY_CMTE']
                LOANS_OWED_BY_CMTE_STRING = ""
                for tran in List_SC_similar_LOANS_OWED_BY_CMTE:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
                    COALESCE(t1.transaction_id, '''') AS "transactionId",
                    COALESCE(t2.entity_type, '''') AS "entityType",
                    COALESCE(t2.entity_name, '''') AS "lenderOrganizationName",
                    COALESCE(t2.last_name, '''') AS "lenderLastName",
                    COALESCE(t2.first_name, '''') AS "lenderFirstName",
                    COALESCE(t2.middle_name, '''') AS "lenderMiddleName",
                    COALESCE(t2.preffix, '''') AS "lenderPrefix",
                    COALESCE(t2.suffix, '''') AS "lenderSuffix",
                    COALESCE(t2.street_1, '''') AS "lenderStreet1",
                    COALESCE(t2.street_2, '''') AS "lenderStreet2",
                    COALESCE(t2.city, '''') AS "lenderCity",
                    COALESCE(t2.state, '''') AS "lenderState",
                    COALESCE(t2.zip_code, '''') AS "lenderZipCode",
                    COALESCE(t1.election_code, '''') AS "electionCode",
                    COALESCE(t1.election_other_description, '''') AS "electionOtherDescription",
                    COALESCE(t1.loan_amount_original, 0.0) AS "loanAmountOriginal",
                    COALESCE(t1.loan_payment_to_date, 0.0) AS "loanPaymentToDate",
                    COALESCE(t1.loan_balance, 0.0) AS "loanBalance",
                    COALESCE(to_char(t1.loan_incurred_date,''MM/DD/YYYY''), '''') AS "loanIncurredDate",
                    COALESCE(t1.loan_due_date, '''') AS "loanDueDate",
                    COALESCE(t1.loan_intrest_rate, ''0.0'') AS "loanInterestRate",
                    COALESCE(t1.is_loan_secured, '''') AS "isLoanSecured",
                    COALESCE(t1.lender_cmte_id, '''') AS "lenderCommitteeId",
                    COALESCE(t1.lender_cand_id, '''') AS "lenderCandidateId",
                    COALESCE(t1.lender_cand_last_name, '''') AS "lenderCandidateLastName",
                    COALESCE(t1.lender_cand_first_name, '''') AS "lenderCandidateFirstName",
                    COALESCE(t1.lender_cand_middle_name, '''') AS "lenderCandidateMiddleName",
                    COALESCE(t1.lender_cand_prefix, '''') AS "lenderCandidatePrefix",
                    COALESCE(t1.lender_cand_suffix, '''') AS "lenderCandidateSuffix",
                    COALESCE(t1.lender_cand_office, '''') AS "lenderCandidateOffice",
                    COALESCE(t1.lender_cand_state, '''') AS "lenderCandidateState",
                    COALESCE(t1.lender_cand_district, 0) AS "lenderCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_c t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    # LOANS_OWED_BY_CMTE_STRING += """
                    # INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    # VALUES ('F3X', 'SC', '{0}', '{1}');\n
                    # """.format(tran, query)
                    LOANS_OWED_BY_CMTE_STRING += """
                    UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                    AND form_type = '{2}' AND sched_type = '{3}';\n
                    """.format(query, tran, 'F3X', 'SC')

                List_SC_similar_LOANS_OWED_TO_CMTE = ['LOANS_OWED_TO_CMTE']
                LOANS_OWED_TO_CMTE_STRING = ""
                for tran in List_SC_similar_LOANS_OWED_TO_CMTE:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
                    COALESCE(t1.transaction_id, '''') AS "transactionId",
                    COALESCE(t1.loan_amount_original, 0.0) AS "loanAmountOriginal",
                    COALESCE(t1.loan_payment_to_date, 0.0) AS "loanPaymentToDate",
                    COALESCE(t1.loan_balance, 0.0) AS "loanBalance",
                    COALESCE(to_char(t1.loan_incurred_date,''MM/DD/YYYY''), '''') AS "loanIncurredDate",
                    COALESCE(t1.loan_due_date, '''') AS "loanDueDate",
                    COALESCE(t1.loan_intrest_rate, ''0.0'') AS "loanInterestRate",
                    COALESCE(t1.is_loan_secured, '''') AS "isLoanSecured",
                    COALESCE(t1.lender_cmte_id, '''') AS "lenderCommitteeId",
                    COALESCE(t1.lender_cand_id, '''') AS "lenderCandidateId",
                    COALESCE(t1.lender_cand_last_name, '''') AS "lenderCandidateLastName",
                    COALESCE(t1.lender_cand_first_name, '''') AS "lenderCandidateFirstName",
                    COALESCE(t1.lender_cand_middle_name, '''') AS "lenderCandidateMiddleName",
                    COALESCE(t1.lender_cand_prefix, '''') AS "lenderCandidatePrefix",
                    COALESCE(t1.lender_cand_suffix, '''') AS "lenderCandidateSuffix",
                    COALESCE(t1.lender_cand_office, '''') AS "lenderCandidateOffice",
                    COALESCE(t1.lender_cand_state, '''') AS "lenderCandidateState",
                    COALESCE(t1.lender_cand_district, 0) AS "lenderCandidateDistrict",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_c t1
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    # LOANS_OWED_TO_CMTE_STRING += """
                    # INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    # VALUES ('F3X', 'SC', '{0}', '{1}');\n
                    # """.format(tran, query)
                    LOANS_OWED_TO_CMTE_STRING += """
                    UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                    AND form_type = '{2}' AND sched_type = '{3}';\n
                    """.format(query, tran, 'F3X', 'SC')

                List_SA_SC_similar_LOAN_FROM_IND = ['LOAN_FROM_IND']
                SA_LOAN_FROM_IND_STRING = ""
                for tran in List_SA_SC_similar_LOAN_FROM_IND:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
                    COALESCE(t1.transaction_id, '''') AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber",
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(to_char(t1.contribution_date,''MM/DD/YYYY''), '''') AS "contributionDate",
                    COALESCE(t1.contribution_amount, 0.0) AS "contributionAmount",
                    COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
                    COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription",
                    COALESCE(t2.entity_type, '''') AS "entityType",
                    COALESCE(t2.last_name, '''') AS "contributorLastName",
                    COALESCE(t2.first_name, '''') AS "contributorFirstName",
                    COALESCE(t2.middle_name, '''') AS "contributorMiddleName",
                    COALESCE(t2.preffix, '''') AS "contributorPrefix",
                    COALESCE(t2.suffix, '''') AS "contributorSuffix",
                    COALESCE(t2.street_1, '''') AS "contributorStreet1",
                    COALESCE(t2.street_2, '''') AS "contributorStreet2",
                    COALESCE(t2.city, '''') AS "contributorCity",
                    COALESCE(t2.state, '''') AS "contributorState",
                    COALESCE(t2.zip_code, '''') AS "contributorZipCode"
                    FROM public.sched_a t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SA_LOAN_FROM_IND_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                List_SC1_similar_SC1 = ['SC1']
                SC1_STRING = ""
                for tran in List_SC1_similar_SC1:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
                    COALESCE(t1.transaction_id, '''') AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber",
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t2.entity_name, '''') AS "lenderOrganizationName",
                    COALESCE(t2.street_1, '''') AS "lenderStreet1",
                    COALESCE(t2.street_2, '''') AS "lenderStreet2",
                    COALESCE(t2.city, '''') AS "lenderCity",
                    COALESCE(t2.state, '''') AS "lenderState",
                    COALESCE(t2.zip_code, '''') AS "lenderZipCode",
                    COALESCE(t1.loan_amount, 0.0) AS "loanAmount",
                    COALESCE(t1.loan_intrest_rate, ''0.0'') AS "loanInterestRate",
                    COALESCE(to_char(t1.loan_incurred_date,''MM/DD/YYYY''), '''') AS "loanIncurredDate",
                    COALESCE(to_char(t1.loan_due_date,''MM/DD/YYYY''), '''') AS "loanDueDate",
                    COALESCE(t1.is_loan_restructured, '''') AS "isLoanRestructured",
                    COALESCE(to_char(t1.original_loan_date,''MM/DD/YYYY''), '''') AS "originalLoanDate",
                    COALESCE(t1.credit_amount_this_draw, 0.0) AS "creditAmountThisDraw",
                    COALESCE(t1.total_outstanding_balance, 0.0) AS "totalOutstandingBalance",
                    COALESCE(t1.other_parties_liable, '''') AS "otherPartiesLiable",
                    COALESCE(t1.pledged_collateral_ind, '''') AS "pledgedCollateralIndicator",
                    COALESCE(t1.pledge_collateral_desc, '''') AS "pledgeCollateralDescription",
                    COALESCE(t1.pledge_collateral_amount, 0.0) AS "pledgeCollateralAmount",
                    COALESCE(t1.perfected_intrest_ind, '''') AS "perfectedInterestIndicator",
                    COALESCE(t1.future_income_ind, '''') AS "futureIncomeIndicator",
                    COALESCE(t1.future_income_desc, '''') AS "futureIncomeDescription",
                    COALESCE(t1.future_income_estimate, 0.0) AS "futureIncomeEstimate",
                    COALESCE(to_char(t1.depository_account_established_date,''MM/DD/YYYY''), '''') AS "depositoryAccountEstablishedDate",
                    COALESCE(t1.depository_account_location, '''') AS "depositoryAccountLocation",
                    COALESCE(t1.depository_account_street_1, '''') AS "depositoryAccountStreet1",
                    COALESCE(t1.depository_account_street_2, '''') AS "depositoryAccountStreet2",
                    COALESCE(t1.depository_account_city, '''') AS "depositoryAccountCity",
                    COALESCE(t1.depository_account_state, '''') AS "depositoryAccountState",
                    COALESCE(t1.depository_account_zip, '''') AS "depositoryAccountZipCode",
                    COALESCE(to_char(t1.depository_account_auth_date,''MM/DD/YYYY''), '''') AS "depositoryAccountAuthorizedDate",
                    COALESCE(t1.basis_of_loan_desc, '''') AS "basisOfLoanDescription",
                    COALESCE(t3.last_name, '''') AS "treasurerLastName",
                    COALESCE(t3.first_name, '''') AS "treasurerFirstName",
                    COALESCE(t3.middle_name, '''') AS "treasurerMiddleName",
                    COALESCE(t3.preffix, '''') AS "treasurerPrefix",
                    COALESCE(t3.suffix, '''') AS "treasurerSuffix",
                    COALESCE(to_char(t1.treasurer_signed_date,''MM/DD/YYYY''), '''') AS "treasurerSignedDate",
                    COALESCE(t4.last_name, '''') AS "authorizedLastName",
                    COALESCE(t4.first_name, '''') AS "authorizedFirstName",
                    COALESCE(t4.middle_name, '''') AS "authorizedMiddleName",
                    COALESCE(t4.preffix, '''') AS "authorizedPrefix",
                    COALESCE(t4.suffix, '''') AS "authorizedSuffix",
                    COALESCE(t1.authorized_entity_title, '''') AS "authorizedTitle",
                    COALESCE(to_char(t1.authorized_signed_date,''MM/DD/YYYY''), '''') AS "authorizedSignedDate"
                    FROM public.sched_c1 t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.lender_entity_id
                    LEFT JOIN public.entity t3 ON t3.entity_id = t1.treasurer_entity_id
                    LEFT JOIN public.entity t4 ON t4.entity_id = t1.authorized_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SC1_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                List_SC2_similar_SC2 = ['SC2']
                SC2_STRING = ""
                for tran in List_SC2_similar_SC2:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
                    COALESCE(t1.transaction_id, '''') AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber",
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t2.last_name, '''') AS "lastName",
                    COALESCE(t2.first_name, '''') AS "firstName",
                    COALESCE(t2.middle_name, '''') AS "middleName",
                    COALESCE(t2.preffix, '''') AS "preffix",
                    COALESCE(t2.suffix, '''') AS "suffix",
                    COALESCE(t2.street_1, '''') AS "street1",
                    COALESCE(t2.street_2, '''') AS "street2",
                    COALESCE(t2.city, '''') AS "city",
                    COALESCE(t2.state, '''') AS "state",
                    COALESCE(t2.zip_code, '''') AS "zipCode",
                    COALESCE(t2.employer, '''') AS "employer",
                    COALESCE(t2.occupation, '''') AS "occupation",
                    COALESCE(t1.guaranteed_amount, 0.0) AS "guaranteedAmount"
                    FROM public.sched_c2 t1
                    LEFT JOIN public.entity t2 ON t1.guarantor_entity_id = t2.entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SC2_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SA', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/SC_sql.sql", 'w')
                file.write(LOANS_OWED_BY_CMTE_STRING)
                file.write(LOANS_OWED_TO_CMTE_STRING)
                file.write(SA_LOAN_FROM_IND_STRING)
                file.write(SC1_STRING)
                file.write(SC2_STRING)
                file.close()


                List_SH_similar_SH1 = ['ALLOC_H1']
                List_SH_similar_SH2 = ['ALLOC_H2_RATIO']
                List_SH_similar_SH3 = ['TRAN_FROM_NON_FED_ACC']
                List_SH_similar_SH5 = ['TRAN_FROM_LEVIN_ACC']
                parent = {'ALLOC_EXP_CC_PAY': 'ALLOC_EXP_CC_PAY_MEMO', 'ALLOC_EXP_STAF_REIM' :'ALLOC_EXP_STAF_REIM_MEMO', 
                'ALLOC_EXP_PMT_TO_PROL': 'ALLOC_EXP_PMT_TO_PROL_MEMO', 'ALLOC_FEA_CC_PAY': 'ALLOC_FEA_CC_PAY_MEMO',
                'ALLOC_FEA_STAF_REIM': 'ALLOC_FEA_STAF_REIM_MEMO'
                }

                SH1_STRING = ""
                for tran in List_SH_similar_SH1:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
                    COALESCE(t1.transaction_id, '''') AS "transactionId",
                    COALESCE(t1.presidential_only, '''') AS "presidentialOnly",
                    COALESCE(t1.presidential_and_senate, '''') AS "presidentialAndSenate",
                    COALESCE(t1.senate_only, '''') AS "senateOnly",
                    COALESCE(t1.non_pres_and_non_senate, '''') AS "nonPresidentialAndNonSenate",
                    COALESCE(t1.federal_percent, 0.0) AS "federalPercent",
                    COALESCE(t1.non_federal_percent, 0.0) AS "nonFederalPercent",
                    COALESCE(t1.administrative, '''') AS "administrative",
                    COALESCE(t1.generic_voter_drive, '''') AS "genericVoterDrive",
                    COALESCE(t1.public_communications, '''') AS "publicCommunications"
                    FROM public.sched_h1 t1
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SH1_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SH1', '{0}', '{1}');\n""".format(tran, query)

                SH2_STRING = ""
                for tran in List_SH_similar_SH2:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
                    COALESCE(t1.transaction_id, '''') AS "transactionId",
                    COALESCE(t1.activity_event_name, '''') AS "activityEventName",
                    COALESCE(t1.fundraising, '''') AS "fundraising",
                    COALESCE(t1.direct_cand_support, '''') AS "directCandidateSupport",
                    COALESCE(t1.ratio_code, '''') AS "ratioCode",
                    COALESCE(t1.federal_percent, 0.0) AS "federalPercent",
                    COALESCE(t1.non_federal_percent, 0.0) AS "nonFederalPercent"
                    FROM public.sched_h2 t1
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SH2_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SH2', '{0}', '{1}');\n""".format(tran, query)

                SH3_STRING = ""
                for tran in List_SH_similar_SH3:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
                    COALESCE(t1.transaction_id, '''') AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber",
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t1.account_name, '''') AS "accountName",
                    COALESCE(t1.activity_event_type, '''') AS "activityEventType",
                    COALESCE(t1.activity_event_name, '''') AS "activityEventName",
                    COALESCE(to_char(t1.receipt_date,''MM/DD/YYYY''), '''') AS "receiptDate",
                    COALESCE(t1.total_amount_transferred, 0.0) AS "totalAmountTransferred",
                    COALESCE(t1.transferred_amount, 0.0) AS "transferredAmount",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_h3 t1
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SH3_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SH3', '{0}', '{1}');\n""".format(tran, query)

                SH5_STRING = ""
                for tran in List_SH_similar_SH5:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
                    COALESCE(t1.transaction_id, '''') AS "transactionId",
                    COALESCE(t1.account_name, '''') AS "accountName",
                    COALESCE(to_char(t1.receipt_date,''MM/DD/YYYY''), '''') AS "receiptDate",
                    COALESCE(t1.total_amount_transferred, 0.0) AS "totalAmountTransferred",
                    COALESCE(t1.voter_registration_amount, 0.0) AS "voterRegistrationAmount",
                    COALESCE(t1.voter_id_amount, 0.0) AS "voterIdAmount",
                    COALESCE(t1.gotv_amount, 0.0) AS "gotvAmount",
                    COALESCE(t1.generic_campaign_amount, 0.0) AS "genericCampaignAmount",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_h5 t1
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SH5_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SH5', '{0}', '{1}');\n""".format(tran, query)

                List_SH_similar_SH4_ALLOC_EXP = ['ALLOC_EXP', 'ALLOC_EXP_CC_PAY_MEMO', 'ALLOC_EXP_STAF_REIM', 'ALLOC_EXP_STAF_REIM_MEMO', 
                'ALLOC_EXP_PMT_TO_PROL', 'ALLOC_EXP_VOID']
                SH4_ALLOC_EXP_STRING = ""
                for tran in List_SH_similar_SH4_ALLOC_EXP:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
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
                    COALESCE(t1.activity_event_identifier, '''') AS "accountEventIdentifier",
                    COALESCE(to_char(t1.expenditure_date,''MM/DD/YYYY''), '''') AS "expenditureDate",
                    COALESCE(t1.total_amount, 0.0) AS "totalFedNonfedAmount",
                    COALESCE(t1.fed_share_amount, 0.0) AS "federalShare",
                    COALESCE(t1.non_fed_share_amount, 0.0) AS "nonfederalShare",
                    COALESCE(t1.activity_event_amount_ytd, 0.0) AS "activityEventTotalYTD",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.activity_event_type, '''') AS "activityEventType",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_h4 t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SH4_ALLOC_EXP_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SH4', '{0}', '{1}');\n
                    """.format(tran, query)

                List_SH_similar_SH4_ALLOC_EXP_CC_PAY = ['ALLOC_EXP_CC_PAY']
                SH4_ALLOC_EXP_CC_PAY_STRING = ""
                for tran in List_SH_similar_SH4_ALLOC_EXP_CC_PAY:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    t1.transaction_type_identifier AS "transactionTypeIdentifier",
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber",
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t2.entity_type, '''') AS "entityType",
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                    COALESCE(t2.street_1, '''') AS "payeeStreet1",
                    COALESCE(t2.street_2, '''') AS "payeeStreet2",
                    COALESCE(t2.city, '''') AS "payeeCity",
                    COALESCE(t2.state, '''') AS "payeeState",
                    COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                    COALESCE(t1.activity_event_identifier, '''') AS "accountEventIdentifier",
                    COALESCE(to_char(t1.expenditure_date,''MM/DD/YYYY''), '''') AS "expenditureDate",
                    COALESCE(t1.total_amount, 0.0) AS "totalFedNonfedAmount",
                    COALESCE(t1.fed_share_amount, 0.0) AS "federalShare",
                    COALESCE(t1.non_fed_share_amount, 0.0) AS "nonfederalShare",
                    COALESCE(t1.activity_event_amount_ytd, 0.0) AS "activityEventTotalYTD",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.activity_event_type, '''') AS "activityEventType",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_h4 t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SH4_ALLOC_EXP_CC_PAY_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SH4', '{0}', '{1}');\n
                    """.format(tran, query)

                List_SH_similar_SH4_ALLOC_EXP_PMT_TO_PROL_MEMO = ['ALLOC_EXP_PMT_TO_PROL_MEMO']
                SH4_ALLOC_EXP_PMT_TO_PROL_MEMO_STRING = ""
                for tran in List_SH_similar_SH4_ALLOC_EXP_PMT_TO_PROL_MEMO:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    t1.transaction_type_identifier AS "transactionTypeIdentifier",
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber",
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t2.entity_type, '''') AS "entityType",
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
                    COALESCE(t1.activity_event_identifier, '''') AS "accountEventIdentifier",
                    COALESCE(to_char(t1.expenditure_date,''MM/DD/YYYY''), '''') AS "expenditureDate",
                    COALESCE(t1.total_amount, 0.0) AS "totalFedNonfedAmount",
                    COALESCE(t1.fed_share_amount, 0.0) AS "federalShare",
                    COALESCE(t1.non_fed_share_amount, 0.0) AS "nonfederalShare",
                    COALESCE(t1.activity_event_amount_ytd, 0.0) AS "activityEventTotalYTD",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.activity_event_type, '''') AS "activityEventType",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_h4 t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SH4_ALLOC_EXP_PMT_TO_PROL_MEMO_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SH4', '{0}', '{1}');\n
                    """.format(tran, query)

                List_SH_similar_SH6 = ['ALLOC_FEA_DISB', 'ALLOC_FEA_CC_PAY_MEMO', 'ALLOC_FEA_STAF_REIM', 'ALLOC_FEA_STAF_REIM_MEMO', 
                'ALLOC_FEA_VOID']

                SH6_STRING = ""
                for tran in List_SH_similar_SH6:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
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
                    COALESCE(t1.account_event_identifier, '''') AS "accountEventIdentifier",
                    COALESCE(to_char(t1.expenditure_date,''MM/DD/YYYY''), '''') AS "expenditureDate",
                    COALESCE(t1.total_fed_levin_amount, 0.0) AS "totalFedLevinAmount",
                    COALESCE(t1.federal_share, 0.0) AS "federalShare",
                    COALESCE(t1.levin_share, 0.0) AS "levinShare",
                    COALESCE(t1.activity_event_total_ytd, 0.0) AS "activityEventTotalYTD",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.activity_event_type, '''') AS "activityEventType",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_h6 t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SH6_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SH6', '{0}', '{1}');\n
                    """.format(tran, query)

                List_SH_similar_SH6_ALLOC_FEA_CC_PAY = ['ALLOC_FEA_CC_PAY']
                SH6_ALLOC_FEA_CC_PAY_STRING = ""
                for tran in List_SH_similar_SH6_ALLOC_FEA_CC_PAY:

                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    COALESCE(t1.transaction_type, '''') AS "transactionTypeCode",
                    t1.transaction_type_identifier AS "transactionTypeIdentifier",
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber",
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t2.entity_type, '''') AS "entityType",
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                    COALESCE(t2.street_1, '''') AS "payeeStreet1",
                    COALESCE(t2.street_2, '''') AS "payeeStreet2",
                    COALESCE(t2.city, '''') AS "payeeCity",
                    COALESCE(t2.state, '''') AS "payeeState",
                    COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                    COALESCE(t1.account_event_identifier, '''') AS "accountEventIdentifier",
                    COALESCE(to_char(t1.expenditure_date,''MM/DD/YYYY''), '''') AS "expenditureDate",
                    COALESCE(t1.total_fed_levin_amount, 0.0) AS "totalFedLevinAmount",
                    COALESCE(t1.federal_share, 0.0) AS "federalShare",
                    COALESCE(t1.levin_share, 0.0) AS "levinShare",
                    COALESCE(t1.activity_event_total_ytd, 0.0) AS "activityEventTotalYTD",
                    COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.category_code, '''') AS "categoryCode",
                    COALESCE(t1.activity_event_type, '''') AS "activityEventType",
                    COALESCE(t1.memo_code, '''') AS "memoCode",
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_h6 t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SH6_ALLOC_FEA_CC_PAY_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SH6', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/SH_sql.sql", 'w')
                file.write(SH1_STRING)
                file.write(SH2_STRING)
                file.write(SH3_STRING)
                file.write(SH5_STRING)
                file.write(SH4_ALLOC_EXP_STRING)
                file.write(SH4_ALLOC_EXP_CC_PAY_STRING)
                file.write(SH4_ALLOC_EXP_PMT_TO_PROL_MEMO_STRING)
                file.write(SH6_STRING)
                file.write(SH6_ALLOC_FEA_CC_PAY_STRING)
                file.close()

                List_SL_similar_SL = ['SCHED_L_SUM']
                SL_STRING = ""
                for tran in List_SL_similar_SL:

                    query = """
                    SELECT t1.transaction_type_identifier AS "transactionTypeIdentifier",
                    t1.transaction_id AS "transactionId",
                    t1.record_id AS "recordId",
                    COALESCE(t1.account_name, '''') AS "accountName", 
                    COALESCE(to_char(t1.cvg_from_date,''MM/DD/YYYY''), '''') AS "coverageFromDate",
                    COALESCE(to_char(t1.cvg_end_date,''MM/DD/YYYY''), '''') AS "coverageThroughDate",
                    COALESCE(t1.item_receipts, 0.0) AS "itemizedReceiptsFromPersons", 
                    COALESCE(t1.unitem_receipts, 0.0) AS "unitemizedReceiptsFromPersons", 
                    COALESCE(t1.total_c_receipts, 0.0) AS "totalReceiptsFromPersons", 
                    COALESCE(t1.other_receipts, 0.0) AS "otherReceipts", 
                    COALESCE(t1.total_receipts, 0.0) AS "totalReceipts", 
                    COALESCE(t1.voter_reg_disb_amount, 0.0) AS "voterRegistrationDisbursements", 
                    COALESCE(t1.voter_id_disb_amount, 0.0) AS "voterIdDisbursements", 
                    COALESCE(t1.gotv_disb_amount, 0.0) AS "gotvDisbursements", 
                    COALESCE(t1.generic_campaign_disb_amount, 0.0) AS "genericCampaignDisbursements", 
                    COALESCE(t1.total_disb_sub, 0.0) AS "totalSubDisbursements", 
                    COALESCE(t1.other_disb, 0.0) AS "otherDisbursements", 
                    COALESCE(t1.total_disb, 0.0) AS "totalDisbursements", 
                    COALESCE(t1.coh_bop, 0.0) AS "beginningCashOnHand", 
                    COALESCE(t1.receipts, 0.0) AS "receipts", 
                    COALESCE(t1.subtotal, 0.0) AS "subtotal", 
                    COALESCE(t1.disbursements, 0.0) AS "disbursements", 
                    COALESCE(t1.coh_cop, 0.0) AS "endingCashOnHand", 
                    COALESCE(t1.item_receipts_ytd, 0.0) AS "itemizedReceiptsFromPersonsYTD", 
                    COALESCE(t1.unitem_receipts_ytd, 0.0) AS "unitemizedReceiptsFromPersonsYTD", 
                    COALESCE(t1.total_c_receipts_ytd, 0.0) AS "totalReceiptsFromPersonsYTD", 
                    COALESCE(t1.other_receipts_ytd, 0.0) AS "otherReceiptsYTD", 
                    COALESCE(t1.total_receipts_ytd, 0.0) AS "totalReceiptsYTD", 
                    COALESCE(t1.voter_reg_disb_amount_ytd, 0.0) AS "voterRegistrationDisbursementsYTD", 
                    COALESCE(t1.voter_id_disb_amount_ytd, 0.0) AS "voterIdDisbursementsYTD", 
                    COALESCE(t1.gotv_disb_amount_ytd, 0.0) AS "gotvDisbursementsYTD", 
                    COALESCE(t1.generic_campaign_disb_amount_ytd, 0.0) AS "genericCampaignDisbursementsYTD", 
                    COALESCE(t1.total_disb_sub_ytd, 0.0) AS "totalSubDisbursementsYTD", 
                    COALESCE(t1.other_disb_ytd, 0.0) AS "otherDisbursementsYTD", 
                    COALESCE(t1.total_disb_ytd, 0.0) AS "totalDisbursementsYTD", 
                    COALESCE(t1.coh_coy, 0.0) AS "beginningCashOnHandYTD", 
                    COALESCE(t1.receipts_ytd, 0.0) AS "receiptsYTD", 
                    COALESCE(t1.sub_total_ytd, 0.0) AS "subtotalYTD", 
                    COALESCE(t1.disbursements_ytd, 0.0) AS "disbursementsYTD", 
                    COALESCE(t1.coh_cop_ytd, 0.0) AS "endingCashOnHandYTD"
                    FROM public.sched_l t1
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)

                    SL_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SL', '{0}', '{1}');\n
                    """.format(tran, query)

                file = open("/tmp/SL_sql.sql", 'w')
                file.write(SL_STRING)
                file.close()

                List_SA_similar_INDV_REC = ["LEVIN_INDV_REC", "LEVIN_PARTN_MEMO"]
                INDV_REC_STRING = ""
                for tran in List_SA_similar_INDV_REC:
                    query = """SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
t1.transaction_id AS "transactionId",
COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
COALESCE(to_char(t1.contribution_date,''MM/DD/YYYY''), '''') AS "contributionDate", 
t1.contribution_amount AS "contributionAmount", 
COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", 
COALESCE(t1.memo_code, '''') AS "memoCode", 
COALESCE(t1.memo_text, '''') AS "memoDescription",
COALESCE(t2.entity_type, '''') AS "entityType", 
COALESCE(t2.last_name, '''') AS "contributorLastName", 
COALESCE(t2.first_name, '''') AS "contributorFirstName",
COALESCE(t2.middle_name, '''') AS "contributorMiddleName", 
COALESCE(t2.preffix, '''') AS "contributorPrefix", 
COALESCE(t2.suffix, '''') AS "contributorSuffix",
COALESCE(t2.street_1, '''') AS "contributorStreet1", 
COALESCE(t2.street_2, '''') AS "contributorStreet2", 
COALESCE(t2.city, '''') AS "contributorCity",
COALESCE(t2.state, '''') AS "contributorState", 
COALESCE(t2.zip_code, '''') AS "contributorZipCode", 
COALESCE(t2.employer, '''') AS "contributorEmployer",
COALESCE(t2.occupation, '''') AS "contributorOccupation"
FROM public.sched_a t1
LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
(t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                    # INDV_REC_STRING += """
                    # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                    # AND form_type = '{2}' AND sched_type = '{3}';\n
                    # """.format(query, tran, 'F3X', 'SA')
                    INDV_REC_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SL-A', '{0}', '{1}');\n""".format(tran, query)

                List_SA_similar_BUS = ["LEVIN_ORG_REC"]
                BUS_STRING = ""
                for tran in List_SA_similar_BUS:
                    query = """SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
t1.transaction_id AS "transactionId",
COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
COALESCE(to_char(t1.contribution_date,''MM/DD/YYYY''), '''') AS "contributionDate", 
t1.contribution_amount AS "contributionAmount", 
COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", 
COALESCE(t1.memo_code, '''') AS "memoCode", 
COALESCE(t1.memo_text, '''') AS "memoDescription",
COALESCE(t2.entity_type, '''') AS "entityType",
COALESCE(t2.entity_name, '''') AS "contributorOrgName",
COALESCE(t2.street_1, '''') AS "contributorStreet1", 
COALESCE(t2.street_2, '''') AS "contributorStreet2", 
COALESCE(t2.city, '''') AS "contributorCity",
COALESCE(t2.state, '''') AS "contributorState", 
COALESCE(t2.zip_code, '''') AS "contributorZipCode", 
COALESCE(t2.employer, '''') AS "contributorEmployer",
COALESCE(t2.occupation, '''') AS "contributorOccupation"
FROM public.sched_a t1
LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
(t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                    # INDV_REC_STRING += """
                    # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                    # AND form_type = '{2}' AND sched_type = '{3}';\n
                    # """.format(query, tran, 'F3X', 'SA')
                    BUS_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SL-A', '{0}', '{1}');\n""".format(tran, query)

                List_SA_similar_PAR_REC = ["LEVIN_PARTN_REC", "LEVIN_TRIB_REC"]
                PAR_REC_STRING = ""
                for tran in List_SA_similar_PAR_REC:
                    query = """SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
t1.transaction_id AS "transactionId",
COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
COALESCE(to_char(t1.contribution_date,''MM/DD/YYYY''), '''') AS "contributionDate", 
t1.contribution_amount AS "contributionAmount", 
COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", 
COALESCE(t1.memo_code, '''') AS "memoCode", 
COALESCE(t1.memo_text, '''') AS "memoDescription",
COALESCE(t2.entity_type, '''') AS "entityType",
COALESCE(t2.entity_name, '''') AS "contributorOrgName",
COALESCE(t2.street_1, '''') AS "contributorStreet1", 
COALESCE(t2.street_2, '''') AS "contributorStreet2", 
COALESCE(t2.city, '''') AS "contributorCity",
COALESCE(t2.state, '''') AS "contributorState", 
COALESCE(t2.zip_code, '''') AS "contributorZipCode"
FROM public.sched_a t1
LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
(t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                    # INDV_REC_STRING += """
                    # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                    # AND form_type = '{2}' AND sched_type = '{3}';\n
                    # """.format(query, tran, 'F3X', 'SA')
                    PAR_REC_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SL-A', '{0}', '{1}');\n""".format(tran, query)

                List_SA_similar_PAC_REC = ["LEVIN_PAC_REC", "LEVIN_NON_FED_REC"]
                PAC_REC_STRING = ""
                for tran in List_SA_similar_PAC_REC:
                    query = """SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
t1.transaction_id AS "transactionId",
COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
COALESCE(to_char(t1.contribution_date,''MM/DD/YYYY''), '''') AS "contributionDate", 
t1.contribution_amount AS "contributionAmount", 
COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", 
COALESCE(t1.donor_cmte_id, '''') AS "donorCommitteeId", 
COALESCE(t1.donor_cmte_name, '''') AS "donorCommitteeName",
COALESCE(t1.memo_code, '''') AS "memoCode", 
COALESCE(t1.memo_text, '''') AS "memoDescription",
COALESCE(t2.entity_type, '''') AS "entityType",
COALESCE(t2.entity_name, '''') AS "contributorOrgName",
COALESCE(t2.street_1, '''') AS "contributorStreet1", 
COALESCE(t2.street_2, '''') AS "contributorStreet2", 
COALESCE(t2.city, '''') AS "contributorCity",
COALESCE(t2.state, '''') AS "contributorState", 
COALESCE(t2.zip_code, '''') AS "contributorZipCode"
FROM public.sched_a t1
LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
(t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                    # INDV_REC_STRING += """
                    # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                    # AND form_type = '{2}' AND sched_type = '{3}';\n
                    # """.format(query, tran, 'F3X', 'SA')
                    PAC_REC_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SL-A', '{0}', '{1}');\n""".format(tran, query)

                List_SA_similar_OTH_REC = ["LEVIN_OTH_REC"]
                OTH_REC_STRING = ""
                for tran in List_SA_similar_OTH_REC:
                    query = """SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
t1.transaction_id AS "transactionId",
COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
COALESCE(to_char(t1.contribution_date,''MM/DD/YYYY''), '''') AS "contributionDate", 
t1.contribution_amount AS "contributionAmount", 
COALESCE(t1.aggregate_amt, 0.0) AS "contributionAggregate",
COALESCE(t1.purpose_description, '''') AS "contributionPurposeDescription", 
COALESCE(t1.memo_code, '''') AS "memoCode", 
COALESCE(t1.memo_text, '''') AS "memoDescription",
COALESCE(t2.entity_type, '''') AS "entityType",
COALESCE(t2.entity_name, '''') AS "contributorOrgName", 
COALESCE(t2.last_name, '''') AS "contributorLastName", 
COALESCE(t2.first_name, '''') AS "contributorFirstName",
COALESCE(t2.middle_name, '''') AS "contributorMiddleName", 
COALESCE(t2.preffix, '''') AS "contributorPrefix", 
COALESCE(t2.suffix, '''') AS "contributorSuffix",
COALESCE(t2.street_1, '''') AS "contributorStreet1", 
COALESCE(t2.street_2, '''') AS "contributorStreet2", 
COALESCE(t2.city, '''') AS "contributorCity",
COALESCE(t2.state, '''') AS "contributorState", 
COALESCE(t2.zip_code, '''') AS "contributorZipCode"
FROM public.sched_a t1
LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
(t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                    # INDV_REC_STRING += """
                    # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                    # AND form_type = '{2}' AND sched_type = '{3}';\n
                    # """.format(query, tran, 'F3X', 'SA')
                    OTH_REC_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SL-A', '{0}', '{1}');\n""".format(tran, query)

                List_SB_similar_VOTER = ["LEVIN_VOTER_REG", "LEVIN_VOTER_ID", "LEVIN_GOTV", "LEVIN_GEN", "LEVIN_OTH_DISB"]
                VOTER_STRING = ""
                for tran in List_SB_similar_VOTER:
                    query = """SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
COALESCE(t1.transaction_type, '''') AS "transactionTypeCode", 
COALESCE(t1.transaction_type_identifier, '''') AS "transactionTypeIdentifier",
t1.transaction_id AS "transactionId",
COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
COALESCE(to_char(t1.expenditure_date,''MM/DD/YYYY''), '''') AS "expenditureDate", 
t1.expenditure_amount AS "expenditureAmount",
COALESCE(t1.expenditure_purpose, '''') AS "expenditurePurposeDescription", 
COALESCE(t1.category_code, '''') AS "categoryCode",
COALESCE(t1.memo_code, '''') AS "memoCode", 
COALESCE(t1.memo_text, '''') AS "memoDescription",
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
COALESCE(t2.zip_code, '''') AS "payeeZipCode"
FROM public.sched_b t1
LEFT JOIN public.entity t2 ON t2.entity_id = t1.entity_id
WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
(t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''""".format(tran)
                    # INDV_REC_STRING += """
                    # UPDATE public.tran_query_string SET query_string = '{0}' WHERE tran_type_identifier = '{1}'
                    # AND form_type = '{2}' AND sched_type = '{3}';\n
                    # """.format(query, tran, 'F3X', 'SA')
                    VOTER_STRING += """INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
VALUES ('F3X', 'SL-B', '{0}', '{1}');\n""".format(tran, query)

                file = open("/tmp/sl_a_sql.sql", 'w')
                file.write(INDV_REC_STRING)
                file.write(BUS_STRING)
                file.write(PAR_REC_STRING)
                file.write(PAC_REC_STRING)
                file.write(OTH_REC_STRING)
                file.write(VOTER_STRING)
                file.close()

                List_SE_similar_IE = ['IE', 'IE_CC_PAY_MEMO', 'IE_STAF_REIM_MEMO', 'IE_VOID', 'IE_B4_DISSE']
                IE_STRING = ""
                for tran in List_SE_similar_IE:
                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",  
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
                    COALESCE(t1.election_code, '''') AS "electionCode", 
                    COALESCE(t1.election_other_desc, '''') AS "electionOtherDescription",
                    COALESCE(to_char(t1.dissemination_date, ''MM/DD/YYYY''), '''') AS "disseminationDate",
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(to_char(t1.disbursement_date,''MM/DD/YYYY''), '''') AS "disbursementDate",
                    COALESCE(t1.calendar_ytd_amount, 0.0) AS "calendarYTDPerElectionForOffice",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.support_oppose_code, '''') AS "support/opposeCode",
                    COALESCE(t1.so_cand_id, '''') AS "candidateId",
                    COALESCE(t1.so_cand_last_name, '''') AS "candidateLastName", 
                    COALESCE(t1.so_cand_first_name, '''') AS "candidateFirstName", 
                    COALESCE(t1.so_cand_middle_name, '''') AS "candidateMiddleName", 
                    COALESCE(t1.so_cand_prefix, '''') AS "candidatePrefix",
                    COALESCE(t1.so_cand_suffix, '''') AS "candidateSuffix",
                    COALESCE(t1.so_cand_office, '''') AS "candidateOffice",
                    COALESCE(t1.so_cand_state, '''') AS "candidateState",
                    COALESCE(t1.so_cand_district, '''') AS "candidateDistrict",
                    COALESCE(t3.last_name, '''') AS "completingLastName", 
                    COALESCE(t3.first_name, '''') AS "completingFirstName",
                    COALESCE(t3.middle_name, '''') AS "completingMiddleName", 
                    COALESCE(t3.preffix, '''') AS "completingPrefix", 
                    COALESCE(t3.suffix, '''') AS "completingSuffix",
                    COALESCE(to_char(t1.date_signed,''MM/DD/YYYY''), '''') AS "dateSigned",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_e t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    LEFT JOIN public.entity t3 ON t3.entity_id = t1.completing_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)
                    IE_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SE', '{0}', '{1}');\n
                    """.format(tran, query)
                file = open("/tmp/IE_sql.sql", 'w')
                file.write(IE_STRING)
                file.close()
                List_SE_similar_MULTI_IE = ['IE_MULTI']
                MULTI_IE_STRING = ""
                for tran in List_SE_similar_MULTI_IE:
                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",  
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
                    COALESCE(t1.election_code, '''') AS "electionCode", 
                    COALESCE(t1.election_other_desc, '''') AS "electionOtherDescription",
                    COALESCE(to_char(t1.dissemination_date, ''MM/DD/YYYY''), '''') AS "disseminationDate",
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(to_char(t1.disbursement_date,''MM/DD/YYYY''), '''') AS "disbursementDate",
                    COALESCE(t1.calendar_ytd_amount, 0.0) AS "calendarYTDPerElectionForOffice",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.support_oppose_code, '''') AS "support/opposeCode",
                    COALESCE(t1.so_cand_id, '''') AS "candidateId",
                    COALESCE(t1.so_cand_last_name, '''') AS "candidateLastName", 
                    COALESCE(t1.so_cand_first_name, '''') AS "candidateFirstName", 
                    COALESCE(t1.so_cand_middle_name, '''') AS "candidateMiddleName", 
                    COALESCE(t1.so_cand_prefix, '''') AS "candidatePrefix",
                    COALESCE(t1.so_cand_suffix, '''') AS "candidateSuffix",
                    COALESCE(t1.so_cand_office, '''') AS "candidateOffice",
                    COALESCE(t1.so_cand_state, '''') AS "candidateState",
                    COALESCE(t1.so_cand_district, '''') AS "candidateDistrict",
                    COALESCE(t3.last_name, '''') AS "completingLastName", 
                    COALESCE(t3.first_name, '''') AS "completingFirstName",
                    COALESCE(t3.middle_name, '''') AS "completingMiddleName", 
                    COALESCE(t3.preffix, '''') AS "completingPrefix", 
                    COALESCE(t3.suffix, '''') AS "completingSuffix",
                    COALESCE(to_char(t1.date_signed,''MM/DD/YYYY''), '''') AS "dateSigned",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_e t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    LEFT JOIN public.entity t3 ON t3.entity_id = t1.completing_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)
                    MULTI_IE_STRING += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SE', '{0}', '{1}');\n
                    """.format(tran, query)
                file = open("/tmp/MULTI_IE_sql.sql", 'w')
                file.write(MULTI_IE_STRING)
                file.close()
                List_SE_similar_IE_CC = ['IE_CC_PAY', 'IE_PMT_TO_PROL']
                IE_CC_STRING = ""
                for tran in List_SE_similar_IE_CC:
                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber",
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t2.entity_type, '''') AS "entityType", 
                    COALESCE(t2.entity_name, '''') AS "payeeOrganizationName",
                    COALESCE(t2.street_1, '''') AS "payeeStreet1", 
                    COALESCE(t2.street_2, '''') AS "payeeStreet2", 
                    COALESCE(t2.city, '''') AS "payeeCity",
                    COALESCE(t2.state, '''') AS "payeeState", 
                    COALESCE(t2.zip_code, '''') AS "payeeZipCode",
                    COALESCE(t1.election_code, '''') AS "electionCode",
                    COALESCE(t1.election_code, '''') AS "electionCode",
                    COALESCE(t1.election_other_desc, '''') AS "electionOtherDescription",
                    COALESCE(to_char(t1.dissemination_date, ''MM/DD/YYYY''), '''') AS "disseminationDate",
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(to_char(t1.disbursement_date,''MM/DD/YYYY''), '''') AS "disbursementDate",
                    COALESCE(t1.calendar_ytd_amount, 0.0) AS "calendarYTDPerElectionForOffice",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.support_oppose_code, '''') AS "support/opposeCode",
                    COALESCE(t1.so_cand_id, '''') AS "candidateId",
                    COALESCE(t1.so_cand_last_name, '''') AS "candidateLastName", 
                    COALESCE(t1.so_cand_first_name, '''') AS "candidateFirstName", 
                    COALESCE(t1.so_cand_middle_name, '''') AS "candidateMiddleName", 
                    COALESCE(t1.so_cand_prefix, '''') AS "candidatePrefix",
                    COALESCE(t1.so_cand_suffix, '''') AS "candidateSuffix",
                    COALESCE(t1.so_cand_office, '''') AS "candidateOffice",
                    COALESCE(t1.so_cand_state, '''') AS "candidateState",
                    COALESCE(t1.so_cand_district, '''') AS "candidateDistrict",
                    COALESCE(t3.last_name, '''') AS "completingLastName", 
                    COALESCE(t3.first_name, '''') AS "completingFirstName",
                    COALESCE(t3.middle_name, '''') AS "completingMiddleName", 
                    COALESCE(t3.preffix, '''') AS "completingPrefix", 
                    COALESCE(t3.suffix, '''') AS "completingSuffix",
                    COALESCE(to_char(t1.date_signed,''MM/DD/YYYY''), '''') AS "dateSigned",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_e t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    LEFT JOIN public.entity t3 ON t3.entity_id = t1.completing_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)
                    IE_CC_STRING  += """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SE', '{0}', '{1}');\n
                    """.format(tran, query)
                file = open("/tmp/IE_CC_sql.sql", 'w')
                file.write(IE_CC_STRING)
                file.close()
                List_SE_similar_IE_STAF_REIM = ['IE_STAF_REIM', 'IE_PMT_TO_PROL_MEMO']
                IE_STAF_REIM_STRING = ""
                for tran in List_SE_similar_IE_STAF_REIM:
                    query = """
                    SELECT COALESCE(t1.line_number, '''') AS "lineNumber", 
                    t1.transaction_type_identifier AS "transactionTypeIdentifier", 
                    t1.transaction_id AS "transactionId",
                    COALESCE(t1.back_ref_transaction_id, '''') AS "backReferenceTransactionIdNumber", 
                    COALESCE(t1.back_ref_sched_name, '''') AS "backReferenceScheduleName",
                    COALESCE(t2.entity_type, '''') AS "entityType",
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
                    COALESCE(t1.election_code, '''') AS "electionCode", 
                    COALESCE(t1.election_other_desc, '''') AS "electionOtherDescription",
                    COALESCE(to_char(t1.dissemination_date, ''MM/DD/YYYY''), '''') AS "disseminationDate",
                    COALESCE(t1.expenditure_amount, 0.0) AS "expenditureAmount",
                    COALESCE(to_char(t1.disbursement_date,''MM/DD/YYYY''), '''') AS "disbursementDate",
                    COALESCE(t1.calendar_ytd_amount, 0.0) AS "calendarYTDPerElectionForOffice",
                    COALESCE(t1.purpose, '''') AS "expenditurePurposeDescription",
                    COALESCE(t1.payee_cmte_id, '''') AS "payeeCommitteeId",
                    COALESCE(t1.support_oppose_code, '''') AS "support/opposeCode",
                    COALESCE(t1.so_cand_id, '''') AS "candidateId",
                    COALESCE(t1.so_cand_last_name, '''') AS "candidateLastName", 
                    COALESCE(t1.so_cand_first_name, '''') AS "candidateFirstName", 
                    COALESCE(t1.so_cand_middle_name, '''') AS "candidateMiddleName", 
                    COALESCE(t1.so_cand_prefix, '''') AS "candidatePrefix",
                    COALESCE(t1.so_cand_suffix, '''') AS "candidateSuffix",
                    COALESCE(t1.so_cand_office, '''') AS "candidateOffice",
                    COALESCE(t1.so_cand_state, '''') AS "candidateState",
                    COALESCE(t1.so_cand_district, '''') AS "candidateDistrict",
                    COALESCE(t3.last_name, '''') AS "completingLastName", 
                    COALESCE(t3.first_name, '''') AS "completingFirstName",
                    COALESCE(t3.middle_name, '''') AS "completingMiddleName", 
                    COALESCE(t3.preffix, '''') AS "completingPrefix", 
                    COALESCE(t3.suffix, '''') AS "completingSuffix",
                    COALESCE(to_char(t1.date_signed,''MM/DD/YYYY''), '''') AS "dateSigned",
                    COALESCE(t1.memo_code, '''') AS "memoCode", 
                    COALESCE(t1.memo_text, '''') AS "memoDescription"
                    FROM public.sched_e t1
                    LEFT JOIN public.entity t2 ON t2.entity_id = t1.payee_entity_id
                    LEFT JOIN public.entity t3 ON t3.entity_id = t1.completing_entity_id
                    WHERE t1.transaction_type_identifier = ''{}'' AND t1.report_id = %s AND t1.cmte_id = %s AND (t1.back_ref_transaction_id = %s OR
                    (t1.back_ref_transaction_id IS NULL AND %s IS NULL)) AND t1.delete_ind is distinct from ''Y''
                    """.format(tran)
                    IE_STAF_REIM_STRING+= """
                    INSERT INTO public.tran_query_string(form_type, sched_type, tran_type_identifier, query_string)
                    VALUES ('F3X', 'SE', '{0}', '{1}');\n
                    """.format(tran, query)
                file = open("/tmp/IE_STAF_REIM_sql.sql", 'w')
                file.write(IE_STAF_REIM_STRING)
                file.close()
                file = open("/tmp/SE_sql.sql", 'w')
                file.write(IE_STRING)
                file.write(MULTI_IE_STRING)
                file.write(IE_CC_STRING)
                file.write(IE_STAF_REIM_STRING)
                file.close()

                return Response('Success', status=status.HTTP_201_CREATED)
        except Exception as e:
                return Response('Error: ' + str(e), status=status.HTTP_400_BAD_REQUEST)
