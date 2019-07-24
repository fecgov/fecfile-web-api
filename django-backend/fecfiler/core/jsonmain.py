from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
import maya
from .models import Cmte_Report_Types_View, My_Forms_View #, GenericDocument
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
from fecfiler.core.views import get_list_entity
# from .jsonbuilder import *


up_datetime=datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
logger = logging.getLogger(__name__)
# aws s3 bucket connection
conn = boto.connect_s3()

class NoOPError(Exception):
    def __init__(self, *args, **kwargs):
        default_message = 'Raising Custom Exception NoOPError: There are no results found for the specified parameters!'
        if not (args or kwargs): args = (default_message,)
        super().__init__(*args, **kwargs)

"""
*****************************************************************************************************************************************
"""
def get_entity_sched_a_data(report_id, cmte_id, transaction_id):
    try:
        # GET all rows from schedA table
        forms_obj = []
        if not transaction_id:
            query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, (CASE WHEN aggregate_amt IS NULL THEN 0.0 ELSE aggregate_amt END) AS aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, transaction_type_identifier, donor_cmte_id, donor_cmte_name
                        FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id is NULL """
        else:
            query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, (CASE WHEN aggregate_amt IS NULL THEN 0.0 ELSE aggregate_amt END) AS aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, transaction_type_identifier, donor_cmte_id, donor_cmte_name
                        FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s """
        # if type_identifier:
        #     query_string = query_string + "AND transaction_type_identifier = '"+str(type_identifier)+"'"
        # query_string = query_string + "AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"
        #print(query_string)
        with connection.cursor() as cursor:
            if not transaction_id:
                cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id])
            else:
                cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id, transaction_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj = data_row[0]
                if forms_obj is not None:
                    for d in forms_obj:
                        for i in d:
                            if not d[i] and i != 'aggregate_amt':
                                d[i] = ''
        if forms_obj is None:
            pass
            #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))
        # print(forms_obj)   
        return forms_obj
    except Exception:
        raise

def get_entity_sched_b_data(report_id, cmte_id, transaction_id):
    try:
        # GET all rows from schedB table
        forms_obj = []
        if not transaction_id:
            query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, expenditure_date, expenditure_amount, (CASE WHEN aggregate_amt IS NULL THEN 0.0 ELSE aggregate_amt END) AS aggregate_amt, expenditure_purpose, memo_code, memo_text, election_code, election_other_description, create_date, category_code, transaction_type_identifier, beneficiary_cmte_id, beneficiary_cand_id, beneficiary_cand_office, beneficiary_cand_state, beneficiary_cand_district
                        FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id is NULL"""
        else:
            query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, expenditure_date, expenditure_amount, (CASE WHEN aggregate_amt IS NULL THEN 0.0 ELSE aggregate_amt END) AS aggregate_amt, expenditure_purpose, memo_code, memo_text, election_code, election_other_description, create_date, category_code, transaction_type_identifier, beneficiary_cmte_id, beneficiary_cand_id, beneficiary_cand_office, beneficiary_cand_state, beneficiary_cand_district
                        FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s """
        
        # if type_identifier:
        #     query_string = query_string + "AND transaction_type_identifier = '"+str(type_identifier)+"'"
        # query_string = query_string + "AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"
        #print(query_string)
        with connection.cursor() as cursor:
            if not transaction_id:
                cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id])
            else:
                cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id, transaction_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj = data_row[0]
                if forms_obj is not None:
                    for d in forms_obj:
                        for i in d:
                            if not d[i] and i != 'aggregate_amt':
                                d[i] = ''
                # forms_obj.append(data_row)
        if forms_obj is None:
            pass
            #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))   
        return forms_obj
    except Exception:
        raise


def get_summary_dict(form3x_header_data):
    form3x_data_string ='{'
    form3x_data_string = form3x_data_string + '"cashOnHandYear": 2019,'
    form3x_data_string = form3x_data_string + '"colA": {'
    form3x_data_string = form3x_data_string + '"6b_cashOnHandBeginning": '+ str(form3x_header_data.get('coh_bop', 0)) + ','
    form3x_data_string = form3x_data_string + '"6c_totalReceipts":'+ str(form3x_header_data.get('ttl_receipts_sum_page_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"6d_subtotal":'+ str(form3x_header_data.get('subttl_sum_page_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"7_totalDisbursements":'+ str(form3x_header_data.get('ttl_disb_sum_page_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"8_cashOnHandAtClose":'+ str(form3x_header_data.get('coh_cop', 0)) + ','
    form3x_data_string = form3x_data_string + '"9_debtsTo":'+ str(form3x_header_data.get('debts_owed_to_cmte', 0)) + ','
    form3x_data_string = form3x_data_string + '"10_debtsBy":'+ str(form3x_header_data.get('debts_owed_by_cmte', 0)) + ','
    form3x_data_string = form3x_data_string + '"11ai_Itemized":'+ str(form3x_header_data.get('indv_item_contb_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"11aii_Unitemized":'+ str(form3x_header_data.get('indv_unitem_contb_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"11aiii_Total":'+ str(form3x_header_data.get('ttl_indv_contb', 0)) + ','
    form3x_data_string = form3x_data_string + '"11b_politicalPartyCommittees":'+ str(form3x_header_data.get('pol_pty_cmte_contb_per_i', 0)) + ','
    form3x_data_string = form3x_data_string + '"11c_otherPoliticalCommitteesPACs":'+ str(form3x_header_data.get('other_pol_cmte_contb_per_i', 0)) + ','
    form3x_data_string = form3x_data_string + '"11d_totalContributions":'+ str(form3x_header_data.get('ttl_contb_col_ttl_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"12_transfersFromAffiliatedOtherPartyCommittees":'+ str(form3x_header_data.get('tranf_from_affiliated_pty_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"13_allLoansReceived":'+ str(form3x_header_data.get('all_loans_received_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"14_loanRepaymentsReceived":'+ str(form3x_header_data.get('loan_repymts_received_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"15_offsetsToOperatingExpendituresRefunds":'+ str(form3x_header_data.get('offsets_to_op_exp_per_i', 0)) + ','
    form3x_data_string = form3x_data_string + '"16_refundsOfFederalContributions":'+ str(form3x_header_data.get('fed_cand_contb_ref_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"17_otherFederalReceiptsDividends":'+ str(form3x_header_data.get('other_fed_receipts_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"18a_transfersFromNonFederalAccount_h3":'+ str(form3x_header_data.get('tranf_from_nonfed_acct_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"18b_transfersFromNonFederalLevin_h5":'+ str(form3x_header_data.get('tranf_from_nonfed_levin_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"18c_totalNonFederalTransfers":'+ str(form3x_header_data.get('ttl_nonfed_tranf_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"19_totalReceipts":'+ str(form3x_header_data.get('ttl_receipts_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"20_totalFederalReceipts":'+ str(form3x_header_data.get('ttl_fed_receipts_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"21ai_federalShare":'+ str(form3x_header_data.get('shared_fed_op_exp_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"21aii_nonFederalShare":'+ str(form3x_header_data.get('shared_nonfed_op_exp_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"21b_otherFederalOperatingExpenditures":'+ str(form3x_header_data.get('other_fed_op_exp_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"21c_totalOperatingExpenditures":'+ str(form3x_header_data.get('ttl_op_exp_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"22_transfersToAffiliatedOtherPartyCommittees":'+ str(form3x_header_data.get('tranf_to_affliliated_cmte_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"23_contributionsToFederalCandidatesCommittees":'+ str(form3x_header_data.get('fed_cand_cmte_contb_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"24_independentExpenditures":'+ str(form3x_header_data.get('indt_exp_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"25_coordinatedExpenditureMadeByPartyCommittees":'+ str(form3x_header_data.get('coord_exp_by_pty_cmte_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"26_loanRepayments":'+ str(form3x_header_data.get('loan_repymts_made_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"27_loansMade":'+ str(form3x_header_data.get('loans_made_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"28a_individualsPersons":'+ str(form3x_header_data.get('indv_contb_ref_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"28b_politicalPartyCommittees":'+ str(form3x_header_data.get('pol_pty_cmte_contb_per_ii', 0)) + ','
    form3x_data_string = form3x_data_string + '"28c_otherPoliticalCommittees":'+ str(form3x_header_data.get('other_pol_cmte_contb_per_ii', 0)) + ','
    form3x_data_string = form3x_data_string + '"28d_totalContributionsRefunds":'+ str(form3x_header_data.get('ttl_contb_ref_per_i', 0)) + ','
    form3x_data_string = form3x_data_string + '"29_otherDisbursements":'+ str(form3x_header_data.get('other_disb_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"30ai_sharedFederalActivity_h6_fedShare":'+ str(form3x_header_data.get('shared_fed_actvy_fed_shr_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"30aii_sharedFederalActivity_h6_nonFed":'+ str(form3x_header_data.get('shared_fed_actvy_nonfed_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"30b_nonAllocable_100_federalElectionActivity":'+ str(form3x_header_data.get('non_alloc_fed_elect_actvy_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"30c_totalFederalElectionActivity":'+ str(form3x_header_data.get('ttl_fed_elect_actvy_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"31_totalDisbursements":'+ str(form3x_header_data.get('ttl_disb_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"32_totalFederalDisbursements":'+ str(form3x_header_data.get('ttl_fed_disb_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"33_totalContributions":'+ str(form3x_header_data.get('ttl_contb_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"34_totalContributionRefunds":'+ str(form3x_header_data.get('ttl_contb_ref_per_ii', 0)) + ','
    form3x_data_string = form3x_data_string + '"35_netContributions":'+ str(form3x_header_data.get('net_contb_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"36_totalFederalOperatingExpenditures":'+ str(form3x_header_data.get('ttl_fed_op_exp_per', 0)) + ','
    form3x_data_string = form3x_data_string + '"37_offsetsToOperatingExpenditures":'+ str(form3x_header_data.get('offsets_to_op_exp_per_ii', 0)) + ','
    form3x_data_string = form3x_data_string + '"38_netOperatingExpenditures":'+ str(form3x_header_data.get('net_op_exp_per'))
    form3x_data_string = form3x_data_string + '},'
    form3x_data_string = form3x_data_string + '"colB": {'
    form3x_data_string = form3x_data_string + '"6a_cashOnHandJan_1":'+ str(form3x_header_data.get('coh_begin_calendar_yr', 0))+','
    form3x_data_string = form3x_data_string + '"6c_totalReceipts":'+ str(form3x_header_data.get('ttl_receipts_sum_page_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"6d_subtotal":'+ str(form3x_header_data.get('subttl_sum_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"7_totalDisbursements":'+ str(form3x_header_data.get('ttl_disb_sum_page_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"8_cashOnHandAtClose":'+ str(form3x_header_data.get('coh_coy', 0)) + ','
    form3x_data_string = form3x_data_string + '"11ai_itemized":'+ str(form3x_header_data.get('indv_item_contb_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"11aii_unitemized":'+ str(form3x_header_data.get('indv_unitem_contb_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"11aiii_total":'+ str(form3x_header_data.get('ttl_indv_contb_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"11b_politicalPartyCommittees":'+ str(form3x_header_data.get('pol_pty_cmte_contb_ytd_i')) + ','
    form3x_data_string = form3x_data_string + '"11c_otherPoliticalCommitteesPACs":'+ str(form3x_header_data.get('other_pol_cmte_contb_ytd_i', 0)) + ','
    form3x_data_string = form3x_data_string + '"11d_totalContributions":'+ str(form3x_header_data.get('ttl_contb_col_ttl_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"12_transfersFromAffiliatedOtherPartyCommittees":'+ str(form3x_header_data.get('tranf_from_affiliated_pty_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"13_allLoansReceived":'+ str(form3x_header_data.get('all_loans_received_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"14_loanRepaymentsReceived":'+ str(form3x_header_data.get('loan_repymts_received_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"15_offsetsToOperatingExpendituresRefunds":'+ str(form3x_header_data.get('offsets_to_op_exp_ytd_i', 0)) + ','
    form3x_data_string = form3x_data_string + '"16_refundsOfFederalContributions":'+ str(form3x_header_data.get('fed_cand_cmte_contb_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"17_otherFederalReceiptsDividends":'+ str(form3x_header_data.get('other_fed_receipts_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"18a_transfersFromNonFederalAccount_h3":'+ str(form3x_header_data.get('tranf_from_nonfed_acct_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"18b_transfersFromNonFederalLevin_h5":'+ str(form3x_header_data.get('tranf_from_nonfed_levin_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"18c_totalNonFederalTransfers":'+ str(form3x_header_data.get('ttl_nonfed_tranf_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"19_totalReceipts":'+ str(form3x_header_data.get('ttl_receipts_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"20_totalFederalReceipts":'+ str(form3x_header_data.get('ttl_fed_receipts_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"21ai_federalShare":'+ str(form3x_header_data.get('shared_fed_op_exp_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"21aii_nonFederalShare":'+ str(form3x_header_data.get('shared_nonfed_op_exp_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"21b_otherFederalOperatingExpenditures":'+ str(form3x_header_data.get('other_fed_op_exp_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"21c_totalOperatingExpenditures":'+ str(form3x_header_data.get('ttl_op_exp_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"22_transfersToAffiliatedOtherPartyCommittees":'+ str(form3x_header_data.get('tranf_to_affilitated_cmte_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"23_contributionsToFederalCandidatesCommittees":'+ str(form3x_header_data.get('fed_cand_cmte_contb_ref_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"24_independentExpenditures":'+ str(form3x_header_data.get('indt_exp_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"25_coordinatedExpendituresMadeByPartyCommittees":'+ str(form3x_header_data.get('coord_exp_by_pty_cmte_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"26_loanRepayments":'+ str(form3x_header_data.get('loan_repymts_made_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"27_loansMade":'+ str(form3x_header_data.get('loans_made_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"28a_individualPersons":'+ str(form3x_header_data.get('indv_contb_ref_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"28b_politicalPartyCommittees":'+ str(form3x_header_data.get('pol_pty_cmte_contb_ytd_ii', 0)) + ','
    form3x_data_string = form3x_data_string + '"28c_otherPoliticalCommittees":'+ str(form3x_header_data.get('other_pol_cmte_contb_ytd_ii', 0)) + ','
    form3x_data_string = form3x_data_string + '"28d_totalContributionRefunds":'+ str(form3x_header_data.get('ttl_contb_ref_ytd_i', 0)) + ','
    form3x_data_string = form3x_data_string + '"29_otherDisbursements":'+ str(form3x_header_data.get('other_disb_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"30ai_sharedFederalActivity_h6_federalShare":'+ str(form3x_header_data.get('shared_fed_actvy_fed_shr_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"30aii_sharedFederalActivity_h6_nonFederal":'+ str(form3x_header_data.get('shared_fed_actvy_nonfed_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"30b_nonAllocable_100_federalElectionActivity":'+ str(form3x_header_data.get('non_alloc_fed_elect_actvy_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"30c_totalFederalElectionActivity":'+ str(form3x_header_data.get('ttl_fed_elect_actvy_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"31_totalDisbursements":'+ str(form3x_header_data.get('ttl_disb_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"32_totalFederalDisbursements":'+ str(form3x_header_data.get('ttl_fed_disb_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"33_totalContributions":'+ str(form3x_header_data.get('ttl_contb_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"34_totalContributionRefunds":'+ str(form3x_header_data.get('ttl_contb_ref_ytd_ii', 0)) + ','
    form3x_data_string = form3x_data_string + '"35_netContributions":'+ str(form3x_header_data.get('net_contb_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"36_totalFederalOperatingExpenditures":'+ str(form3x_header_data.get('ttl_fed_op_exp_ytd', 0)) + ','
    form3x_data_string = form3x_data_string + '"37_offsetsToOperatingExpenditures":'+ str(form3x_header_data.get('offsets_to_op_exp_ytd_ii', 0)) + ','
    form3x_data_string = form3x_data_string + '"38_netOperatingExpenditures":'+ str(form3x_header_data.get('net_op_exp_ytd', 0))
    form3x_data_string = form3x_data_string + '}'
    form3x_data_string = form3x_data_string + '}'
    return form3x_data_string


def get_committee_master_values(cmte_id):
    try:
        query_string = """SELECT cmte_id, cmte_name, street_1, street_2, city, state, zip_code,
                        cmte_type, cmte_filed_type, treasurer_last_name, treasurer_first_name,
                       treasurer_middle_name, treasurer_prefix, treasurer_suffix 
                    FROM public.committee_master Where cmte_id = %s"""
        forms_obj = []
        #committee_info_dict = {}
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is []:
            pass
            #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))
        else:
            forms_obj = forms_obj[0]
            committee_info_dict = {}
            committee_info_dict['committeeId'] = forms_obj['cmte_id']
            committee_info_dict['committeeName'] = forms_obj['cmte_name']
            committee_info_dict['street1'] = forms_obj['street_1']
            committee_info_dict['street2'] = forms_obj['street_2']
            committee_info_dict['city'] = forms_obj['city']
            committee_info_dict['state'] = forms_obj['state']
            committee_info_dict['zipCode'] = forms_obj['zip_code']
            committee_info_dict['treasurerLastName'] = forms_obj['treasurer_last_name']
            committee_info_dict['treasurerFirstName'] = forms_obj['treasurer_first_name']
            committee_info_dict['treasurerMiddleName'] = forms_obj['treasurer_middle_name']
            committee_info_dict['treasurerPrefix'] = forms_obj['treasurer_prefix']
            committee_info_dict['treasurerSuffix'] = forms_obj['treasurer_suffix']
        return committee_info_dict
    except Exception:
        raise


def get_f3x_report_data(cmte_id, report_id):
    try:
        query_string = """SELECT * FROM public.form_3x WHERE cmte_id = %s AND report_id = %s"""
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id, report_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            pass
            #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))   
        return forms_obj
    except Exception:
        raise

def get_list_report(report_id, cmte_id):
    try:
        query_string = """SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type
                     FROM public.reports WHERE report_id = %s AND cmte_id = %s """
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [report_id, cmte_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            raise NoOPError('The Entity ID: {} does not exist or is deleted'.format(report_id))   
        return forms_obj
    except Exception:
        raise


#api_view(["POST"])
def task_sched_a(request):
     #creating a JSON file so that it is handy for all the public API's   
    try:
        report_id = request.data.get('report_id')
        #import ipdb;ipdb.set_trace()
        #comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username, is_submitted=True).last()
        #comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username)
        comm_info = True
        if comm_info:
            committeeid = request.user.username
            # serializer = CommitteeInfoSerializer(comm_info)
            comm_info_obj = get_committee_master_values(committeeid)
            header = {
                "version":"8.3",
                "softwareName":"ABC Inc",
                "softwareVersion":"1.02 Beta",
                "additionalInfomation":"Any other useful information"
            }
            f_3x_list = get_f3x_report_data(committeeid, report_id)
            report_info = get_list_report(report_id, committeeid)
            response_inkind_receipt_list = []
            reponse_sched_b_data = []
            response_inkind_out_list = []
            response_dict_receipt = {}
            for f3_i in f_3x_list:
                #print (f3_i['report_id'])

                entity_id_list = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'], None)
                entity_id_sched_b_list = get_entity_sched_b_data(f3_i['report_id'], f3_i['cmte_id'], None)

                #print('parent sched A trans:',len(entity_id_list))
                
                #entity_id_list = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'])

                if entity_id_list:
                    
                    print ("we got the data")
                    #import ipdb;ipdb.set_trace()
                    # comm_id = Committee.objects.get(committeeid=request.user.username)
                    for entity_obj in entity_id_list:
                        response_dict_out = {}
                        response_dict_receipt = {}
                        list_entity = get_list_entity(entity_obj['entity_id'], entity_obj['cmte_id'])
                        if not list_entity:
                            response_dict_receipt['transactionTypeCode'] = entity_obj['transaction_type']
                            response_dict_receipt['transactionId'] = entity_obj['transaction_id']
                            response_dict_receipt['backReferenceTransactionIdNumber'] = entity_obj['back_ref_transaction_id']
                            response_dict_receipt['backReferenceScheduleName'] = entity_obj['back_ref_sched_name']
                            response_dict_receipt['entityType'] = ''
                            response_dict_receipt['lineNumber'] = entity_obj['line_number']
                            response_dict_receipt['contributorOranizationName'] = ''

                            response_dict_receipt['contributorLastName'] = ''
                            response_dict_receipt['contributorFirstName'] = ''
                            response_dict_receipt['contributorMiddleName'] = ''
                            response_dict_receipt['contributorPrefix'] = ''
                            response_dict_receipt['contributorSuffix'] = ''
                            response_dict_receipt['contributorStreet1 '] = ''
                            response_dict_receipt['contributorStreet2'] = ''
                            response_dict_receipt['contributorCity'] = ''
                            response_dict_receipt['contributorState'] = ''
                            response_dict_receipt['contributorZip'] = ''
                            response_dict_receipt['contributionDate'] = datetime.strptime(entity_obj['contribution_date'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
                            response_dict_receipt['contributionAmount'] = round(entity_obj['contribution_amount'],2)
                            response_dict_receipt['contributionAggregate'] = round(entity_obj['aggregate_amt'],2)
                            response_dict_receipt['contributionPurposeDescription'] = entity_obj['purpose_description']
                            response_dict_receipt['contributorEmployer'] = ''
                            response_dict_receipt['contributorOccupation'] = ''
                            response_dict_receipt['donorFecCommitteeId'] = entity_obj['donor_cmte_id']
                            response_dict_receipt['donorFecCommitteeName'] = entity_obj['donor_cmte_name'] 
                            response_dict_receipt['memoCode'] = entity_obj['memo_code']
                            response_dict_receipt['memoDescription'] = entity_obj['memo_text']

                            # continue # Needs a fail condition implemented
                        else:
                            list_entity = list_entity[0]
                            response_dict_receipt['transactionTypeCode'] = entity_obj['transaction_type']
                            response_dict_receipt['transactionId'] = entity_obj['transaction_id']
                            response_dict_receipt['backReferenceTransactionIdNumber'] = entity_obj['back_ref_transaction_id']
                            response_dict_receipt['backReferenceScheduleName'] = entity_obj['back_ref_sched_name']
                            response_dict_receipt['entityType'] = list_entity['entity_type']
                            response_dict_receipt['lineNumber'] = entity_obj['line_number']
                            response_dict_receipt['contributorOranizationName'] = list_entity['entity_name']

                            response_dict_receipt['contributorLastName'] = list_entity['last_name']
                            response_dict_receipt['contributorFirstName'] = list_entity['first_name']
                            response_dict_receipt['contributorMiddleName'] = list_entity['middle_name']
                            response_dict_receipt['contributorPrefix'] = list_entity['prefix']
                            response_dict_receipt['contributorSuffix'] = list_entity['suffix']
                            response_dict_receipt['contributorStreet1 '] = list_entity['street_1']
                            response_dict_receipt['contributorStreet2'] = list_entity['street_2']
                            response_dict_receipt['contributorCity'] = list_entity['city']
                            response_dict_receipt['contributorState'] = list_entity['state']
                            response_dict_receipt['contributorZip'] = list_entity['zip_code']
                            response_dict_receipt['contributionDate'] = datetime.strptime(entity_obj['contribution_date'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
                            response_dict_receipt['contributionAmount'] = round(entity_obj['contribution_amount'],2)
                            response_dict_receipt['contributionAggregate'] = round(entity_obj['aggregate_amt'],2)
                            response_dict_receipt['contributionPurposeDescription'] = entity_obj['purpose_description']
                            response_dict_receipt['contributorEmployer'] = list_entity['employer']
                            response_dict_receipt['contributorOccupation'] = list_entity['occupation']
                            response_dict_receipt['donorFecCommitteeId'] = entity_obj['donor_cmte_id']
                            response_dict_receipt['donorFecCommitteeName'] = entity_obj['donor_cmte_name'] 
                            response_dict_receipt['memoCode'] = entity_obj['memo_code']
                            response_dict_receipt['memoDescription'] = entity_obj['memo_text']


                        
                        # entity_id_child_list = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'], entity_obj['transaction_id'])
                        entity_id_child_list = get_entity_sched_b_data(f3_i['report_id'], f3_i['cmte_id'], entity_obj['transaction_id'])

                        if entity_id_child_list:

                            response_dict_receipt['child'] = []
                            #print('Child sched B trans:' + entity_obj['transaction_id'] + ', length:',len(entity_id_list))
                            for entity_child_obj in entity_id_child_list:
                                response_dict_out = {}
                                list_child_entity = get_list_entity(entity_child_obj['entity_id'], entity_child_obj['cmte_id'])
                                if not list_child_entity:
                                    
                                    response_dict_out['transactionTypeCode'] = entity_child_obj['transaction_type']
                                    response_dict_out['transactionId'] = entity_child_obj['transaction_id']
                                    response_dict_out['backReferenceTransactionIdNumber'] = entity_child_obj['back_ref_transaction_id']
                                    response_dict_out['backReferenceScheduleName'] = entity_child_obj['back_ref_sched_name']
                                    response_dict_out['entityType'] = ''
                                    response_dict_out['lineNumber'] = entity_child_obj['line_number']
                                    response_dict_out['payeeOranizationName'] = ''

                                    response_dict_out['payeeLastName'] = ''
                                    response_dict_out['payeeFirstName'] = ''
                                    response_dict_out['payeeMiddleName'] = ''
                                    response_dict_out['payeePrefix'] = ''
                                    response_dict_out['payeeSuffix'] = ''
                                    response_dict_out['payeeStreet1'] = ''
                                    response_dict_out['payeeStreet2'] = ''
                                    response_dict_out['payeeCity'] = ''
                                    response_dict_out['payeeState'] = ''
                                    response_dict_out['payeezip'] = ''
                                    response_dict_out['expenditureDate'] = datetime.strptime(entity_child_obj['expenditure_date'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
                                    response_dict_out['expenditureAmount'] = round(entity_child_obj['expenditure_amount'],2)
                                    response_dict_out['expenditurePurposeDescription'] = entity_child_obj['expenditure_purpose']
                                    response_dict_out['contributionAggregate'] = round(entity_child_obj['aggregate_amt'],2)
                                    response_dict_out['categoryCode'] = '15G'
                                    response_dict_out['electionCode'] = entity_child_obj['election_code']
                                    response_dict_out['electionOtherDescription'] = entity_child_obj['election_other_description']
                                    response_dict_out['beneficiaryCommitteeFecId'] = entity_child_obj['beneficiary_cmte_id']
                                    response_dict_out['beneficiaryCommitteeName'] = comm_info_obj.get('committeeName')
                                    response_dict_out['beneficiaryCandidateFecId'] = entity_child_obj['beneficiary_cand_id']
                                    response_dict_out['benificiaryCandidateLastName'] = ''
                                    response_dict_out['benificiaryCandidateFirstName'] = ''
                        

                                    response_dict_out['benificiaryCandidateMiddleName'] = ''
                                    response_dict_out['benificiaryCandidatePrefix'] = ''
                                    response_dict_out['benificiaryCandidateSuffix'] = ''
                                    response_dict_out['benificiaryCandidateOffice'] = entity_child_obj['beneficiary_cand_office']
                                    response_dict_out['benificiaryCandidateState'] = entity_child_obj['beneficiary_cand_state']
                                    response_dict_out['benificiaryCandidateDistrict'] = entity_child_obj['beneficiary_cand_district']
                                    response_dict_out['memoCode'] = entity_child_obj['memo_code']
                                    response_dict_out['memoDescription'] = entity_child_obj['memo_text']
                                    # continue # Needs a fail condition implemented
                                else:
                                    list_child_entity = list_child_entity[0]
                                    response_dict_out['transactionTypeCode'] = entity_child_obj['transaction_type']
                                    response_dict_out['transactionId'] = entity_child_obj['transaction_id']
                                    response_dict_out['backReferenceTransactionIdNumber'] = entity_child_obj['back_ref_transaction_id']
                                    response_dict_out['backReferenceScheduleName'] = entity_child_obj['back_ref_sched_name']
                                    response_dict_out['entityType'] = list_child_entity['entity_type']
                                    response_dict_out['lineNumber'] = entity_child_obj['line_number']
                                    response_dict_out['payeeOranizationName'] = list_child_entity['entity_name']

                                    response_dict_out['payeeLastName'] = list_child_entity['last_name']
                                    response_dict_out['payeeFirstName'] = list_child_entity['first_name']
                                    response_dict_out['payeeMiddleName'] = list_child_entity['middle_name']
                                    response_dict_out['payeePrefix'] = list_child_entity['prefix']
                                    response_dict_out['payeeSuffix'] = list_child_entity['suffix']
                                    response_dict_out['payeeStreet1'] = list_child_entity['street_1']
                                    response_dict_out['payeeStreet2'] = list_child_entity['street_2']
                                    response_dict_out['payeeCity'] = list_child_entity['city']
                                    response_dict_out['payeeState'] = list_child_entity['state']
                                    response_dict_out['payeezip'] = list_child_entity['zip_code']
                                    response_dict_out['expenditureDate'] = datetime.strptime(entity_child_obj['expenditure_date'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
                                    response_dict_out['expenditureAmount'] = round(entity_child_obj['expenditure_amount'],2)
                                    response_dict_out['contributionAggregate'] = round(entity_child_obj['aggregate_amt'],2)
                                    response_dict_out['expenditurePurposeDescription'] = entity_child_obj['expenditure_purpose']
                                    response_dict_out['electionCode'] = entity_child_obj['election_code']
                                    response_dict_out['electionOtherDescription'] = entity_child_obj['election_other_description']
                                    response_dict_out['expenditurePurposeDescription'] = entity_child_obj['expenditure_purpose']
                                    response_dict_out['categoryCode'] = '15G'
                                    response_dict_out['beneficiaryCommitteeFecId'] = entity_child_obj['beneficiary_cmte_id']
                                    response_dict_out['beneficiaryCommitteeName'] = comm_info_obj.get('committeeName')
                                    response_dict_out['beneficiaryCandidateFecId'] = entity_child_obj['beneficiary_cand_id']
                                    response_dict_out['benificiaryCandidateLastName'] = list_child_entity['last_name']
                                    response_dict_out['benificiaryCandidateFirstName'] = list_child_entity['first_name']
                        

                                    response_dict_out['benificiaryCandidateMiddleName'] = list_child_entity['middle_name']
                                    response_dict_out['benificiaryCandidatePrefix'] = list_child_entity['prefix']
                                    response_dict_out['benificiaryCandidateSuffix'] = list_child_entity['suffix']
                                    response_dict_out['benificiaryCandidateOffice'] = entity_child_obj['beneficiary_cand_office']
                                    response_dict_out['benificiaryCandidateState'] = entity_child_obj['beneficiary_cand_state']
                                    response_dict_out['benificiaryCandidateDistrict'] = entity_child_obj['beneficiary_cand_district']
                                    response_dict_out['memoCode'] = entity_child_obj['memo_code']
                                    response_dict_out['memoDescription'] = entity_child_obj['memo_text']
                                response_dict_receipt['child'].append(response_dict_out)
                            # print(entity_obj['transaction_id'])
                        
                        entity_id_child_list_a = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'], entity_obj['transaction_id'])

                        if entity_id_child_list_a: 
                            if not 'child' in response_dict_receipt:
                                response_dict_receipt['child'] = []
                            #print('Child sched A trans:' + entity_obj['transaction_id'] + ', length:',len(entity_id_list))
                            for entity_child_obj in entity_id_child_list_a:
                                response_dict_out = {}
                                list_child_entity = get_list_entity(entity_child_obj['entity_id'], entity_child_obj['cmte_id'])
                                if not list_child_entity:
                                    response_dict_out['transactionTypeCode'] = entity_child_obj['transaction_type']
                                    response_dict_out['transactionId'] = entity_child_obj['transaction_id']
                                    response_dict_out['backReferenceTransactionIdNumber'] = entity_child_obj['back_ref_transaction_id']
                                    response_dict_out['backReferenceScheduleName'] = entity_child_obj['back_ref_sched_name']
                                    response_dict_out['entityType'] = ''
                                    response_dict_out['lineNumber'] = entity_child_obj['line_number']
                                    response_dict_out['contributorOranizationName'] = ''    

                                    response_dict_out['contributorLastName'] = ''
                                    response_dict_out['contributorFirstName'] = ''
                                    response_dict_out['contributorMiddleName'] = ''
                                    response_dict_out['contributorPrefix'] = ''
                                    response_dict_out['contributorSuffix'] = ''
                                    response_dict_out['contributorStreet1 '] = ''
                                    response_dict_out['contributorStreet2'] = ''
                                    response_dict_out['contributorCity'] = ''
                                    response_dict_out['contributorState'] = ''
                                    response_dict_out['contributorZip'] = ''
                                    response_dict_out['contributionDate'] =  datetime.strptime(entity_child_obj['contribution_date'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
                                    response_dict_out['contributionAmount'] = round(entity_child_obj['contribution_amount'],2)
                                    response_dict_out['contributionAggregate'] = entity_child_obj['aggregate_amt']
                                    response_dict_out['contributionPurposeDescription'] = entity_child_obj['purpose_description']
                                    response_dict_out['contributorEmployer'] = ''
                                    response_dict_out['contributorOccupation'] = ''
                                    response_dict_out['donorFecCommitteeId'] = entity_child_obj['donor_cmte_id']
                                    response_dict_out['donorFecCommitteeName'] = entity_child_obj['donor_cmte_name']
                                    response_dict_out['memoCode'] = entity_child_obj['memo_code']
                                    response_dict_out['memoDescription'] = entity_child_obj['memo_text']
                                    # continue # Needs a fail condition implemented
                                else:
                                    list_child_entity = list_child_entity[0]
                                    response_dict_out['transactionTypeCode'] = entity_child_obj['transaction_type']
                                    response_dict_out['transactionId'] = entity_child_obj['transaction_id']
                                    response_dict_out['backReferenceTransactionIdNumber'] = entity_child_obj['back_ref_transaction_id']
                                    response_dict_out['backReferenceScheduleName'] = entity_child_obj['back_ref_sched_name']
                                    response_dict_out['entityType'] = list_child_entity['entity_type']
                                    response_dict_out['lineNumber'] = entity_child_obj['line_number']
                                    response_dict_out['contributorOranizationName'] = list_child_entity['entity_name'] 
                                    
                                    response_dict_out['contributorLastName'] = list_child_entity['last_name']
                                    response_dict_out['contributorFirstName'] = list_child_entity['first_name']
                                    response_dict_out['contributorMiddleName'] = list_child_entity['middle_name']
                                    response_dict_out['contributorPrefix'] = list_child_entity['prefix']
                                    response_dict_out['contributorSuffix'] = list_child_entity['suffix']
                                    response_dict_out['contributorStreet1 '] = list_child_entity['street_1']
                                    response_dict_out['contributorStreet2'] = list_child_entity['street_2']
                                    response_dict_out['contributorCity'] = list_child_entity['city']
                                    response_dict_out['contributorState'] = list_child_entity['state']
                                    response_dict_out['contributorZip'] = list_child_entity['zip_code']
                                    response_dict_out['contributionDate'] =  datetime.strptime(entity_child_obj['contribution_date'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
                                    response_dict_out['contributionAmount'] = round(entity_child_obj['contribution_amount'],2)
                                    response_dict_out['contributionAggregate'] = entity_child_obj['aggregate_amt']
                                    response_dict_out['contributionPurposeDescription'] = entity_child_obj['purpose_description']
                                    response_dict_out['contributorEmployer'] = list_child_entity['employer']
                                    response_dict_out['contributorOccupation'] = list_child_entity['occupation']
                                    response_dict_out['donorFecCommitteeId'] = entity_child_obj['donor_cmte_id']
                                    response_dict_out['donorFecCommitteeName'] = entity_child_obj['donor_cmte_name']
                                    response_dict_out['memoCode'] = entity_child_obj['memo_code']
                                    response_dict_out['memoDescription'] = entity_child_obj['memo_text']
                                response_dict_receipt['child'].append(response_dict_out)

                        response_inkind_receipt_list.append(response_dict_receipt)
                else:
                    response_inkind_receipt_list = []
                #import ipdb;ipdb.set_trace()
                if entity_id_sched_b_list:
                    for entity_obj_b in entity_id_sched_b_list:
                        response_dict_out = {}
                        response_dict_receipt = {}
                        list_entity_b = get_list_entity(entity_obj_b['entity_id'], entity_obj_b['cmte_id'])
                        if not list_entity_b:
                            response_dict_receipt['transactionTypeCode'] = entity_obj_b['transaction_type']
                            response_dict_receipt['transactionId'] = entity_obj_b['transaction_id']
                            response_dict_receipt['backReferenceTransactionIdNumber'] = entity_obj_b['back_ref_transaction_id']
                            response_dict_receipt['backReferenceScheduleName'] = entity_obj_b['back_ref_sched_name']
                            response_dict_receipt['entityType'] = ''
                            response_dict_receipt['lineNumber'] = entity_obj_b['line_number']
                            response_dict_receipt['payeeOranizationName'] = ''

                            response_dict_receipt['payeeLastName'] = ''
                            response_dict_receipt['payeeFirstName'] = ''
                            response_dict_receipt['payeeMiddleName'] = ''
                            response_dict_receipt['payeePrefix'] = ''
                            response_dict_receipt['payeeSuffix'] = ''
                            response_dict_receipt['payeeStreet1'] = ''
                            response_dict_receipt['payeeStreet2'] = ''
                            response_dict_receipt['payeeCity'] = ''
                            response_dict_receipt['payeeState'] = ''
                            response_dict_receipt['payeezip'] = ''
                            response_dict_receipt['expenditureDate'] = datetime.strptime(entity_obj_b['expenditure_date'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
                            response_dict_receipt['expenditureAmount'] = round(entity_obj_b['expenditure_amount'],2)
                            response_dict_receipt['contributionAggregate'] = round(entity_obj_b['aggregate_amt'],2)
                            response_dict_receipt['expenditurePurposeDescription'] = entity_obj_b['expenditure_purpose']
                            response_dict_receipt['categoryCode'] = '15G'
                            response_dict_receipt['electionCode'] =  entity_obj_b['election_code']
                            response_dict_receipt['electionOtherDescription'] =  entity_obj_b['election_other_description']
                            response_dict_receipt['beneficiaryCommitteeFecId'] = entity_obj_b['beneficiary_cmte_id']
                            response_dict_receipt['beneficiaryCommitteeName'] = comm_info_obj.get('committeeName')
                            response_dict_receipt['beneficiaryCandidateFecId'] = entity_obj_b['beneficiary_cand_id']
                            response_dict_receipt['benificiaryCandidateLastName'] = ''
                            response_dict_receipt['benificiaryCandidateFirstName'] = ''
                        

                            response_dict_receipt['benificiaryCandidateMiddleName'] = ''
                            response_dict_receipt['benificiaryCandidatePrefix'] = ''
                            response_dict_receipt['benificiaryCandidateSuffix'] = ''
                            response_dict_receipt['benificiaryCandidateOffice'] = entity_obj_b['beneficiary_cand_office']
                            response_dict_receipt['benificiaryCandidateState'] = entity_obj_b['beneficiary_cand_state']
                            response_dict_receipt['benificiaryCandidateDistrict'] = entity_obj_b['beneficiary_cand_district']
                            response_dict_receipt['memoCode'] = entity_obj_b['memo_code']
                            response_dict_receipt['memoDescription'] = entity_obj_b['memo_text']
                                # continue # Needs a fail condition implemented
                        else:
                            list_entity_b = list_entity_b[0]
                            response_dict_receipt['transactionTypeCode'] = entity_obj_b['transaction_type']
                            response_dict_receipt['transactionId'] = entity_obj_b['transaction_id']
                            response_dict_receipt['backReferenceTransactionIdNumber'] = entity_obj_b['back_ref_transaction_id']
                            response_dict_receipt['backReferenceScheduleName'] = entity_obj_b['back_ref_sched_name']
                            response_dict_receipt['entityType'] = list_entity_b['entity_type']
                            response_dict_receipt['lineNumber'] = entity_obj_b['line_number']
                            response_dict_receipt['payeeOranizationName'] = list_entity_b['entity_name']

                            response_dict_receipt['payeeLastName'] = list_entity_b['last_name']
                            response_dict_receipt['payeeFirstName'] = list_entity_b['first_name']
                            response_dict_receipt['payeeMiddleName'] = list_entity_b['middle_name']
                            response_dict_receipt['payeePrefix'] = list_entity_b['prefix']
                            response_dict_receipt['payeeSuffix'] = list_entity_b['suffix']
                            response_dict_receipt['payeeStreet1'] = list_entity_b['street_1']
                            response_dict_receipt['payeeStreet2'] = list_entity_b['street_2']
                            response_dict_receipt['payeeCity'] = list_entity_b['city']
                            response_dict_receipt['payeeState'] = list_entity_b['state']
                            response_dict_receipt['payeezip'] = list_entity_b['zip_code']
                            response_dict_receipt['expenditureDate'] = datetime.strptime(entity_obj_b['expenditure_date'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
                            response_dict_receipt['expenditureAmount'] = round(entity_obj_b['expenditure_amount'],2)
                            response_dict_receipt['contributionAggregate'] = round(entity_obj_b['aggregate_amt'],2)
                            response_dict_receipt['expenditurePurposeDescription'] = entity_obj_b['expenditure_purpose']
                            response_dict_receipt['electionCode'] =  entity_obj_b['election_code']
                            response_dict_receipt['electionOtherDescription'] =  entity_obj_b['election_other_description']
                            response_dict_receipt['beneficiaryCommitteeFecId'] = entity_obj_b['beneficiary_cmte_id']
                            response_dict_receipt['beneficiaryCommitteeName'] = comm_info_obj.get('committeeName')
                            response_dict_receipt['beneficiaryCandidateFecId'] = entity_obj_b['beneficiary_cand_id']
                            response_dict_receipt['benificiaryCandidateLastName'] = list_entity_b['last_name']
                            response_dict_receipt['benificiaryCandidateFirstName'] = list_entity_b['first_name']
                        

                            response_dict_receipt['benificiaryCandidateMiddleName'] = list_entity_b['middle_name']
                            response_dict_receipt['benificiaryCandidatePrefix'] = list_entity_b['prefix']
                            response_dict_receipt['benificiaryCandidateSuffix'] = list_entity_b['suffix']
                            response_dict_receipt['benificiaryCandidateOffice'] = entity_obj_b['beneficiary_cand_office']
                            response_dict_receipt['benificiaryCandidateState'] = entity_obj_b['beneficiary_cand_state']
                            response_dict_receipt['benificiaryCandidateDistrict'] = entity_obj_b['beneficiary_cand_district']
                            response_dict_receipt['categoryCode'] = '15G'
                            response_dict_receipt['memoCode'] = entity_obj_b['memo_code']
                            response_dict_receipt['memoDescription'] = entity_obj_b['memo_text']
                         
                        reponse_sched_b_data.append(response_dict_receipt)
                else:
                    reponse_sched_b_data = []

            #import ipdb;ipdb.set_trace()
            # get_list_entity(entity_id, comm_info.committeeid)
           
            data_obj = {}
            data_obj['header'] = header
            comm_info_obj['changeOfAddress'] = f3_i['cmte_addr_chg_flag'] if f3_i['cmte_addr_chg_flag'] else ''
            comm_info_obj['electionState'] = f3_i['state_of_election'] if f3_i['state_of_election'] else ''
            comm_info_obj['reportCode'] = f3_i['report_type']
            comm_info_obj['amendmentIndicator'] = f3_i['amend_ind']
            comm_info_obj['amendmentNumber'] = report_info[0]['amend_number']
            if not f3_i['date_of_election']:
                comm_info_obj['electionDate'] = ''
            else:
                comm_info_obj['electionDate'] = datetime.strptime(f3_i['date_of_election'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
            if not f3_i['cvg_start_dt']:
                comm_info_obj['coverageStartDate'] = ''
            else:
                comm_info_obj['coverageStartDate'] = datetime.strptime(f3_i['cvg_start_dt'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
            if not f3_i['cvg_end_dt']:
                comm_info_obj['coverageEndDate'] = ''
            else:
                comm_info_obj['coverageEndDate'] = datetime.strptime(f3_i['cvg_end_dt'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
            if not f3_i['date_signed']:
                comm_info_obj['dateSigned'] = ''
            else:
                comm_info_obj['dateSigned'] = datetime.strptime(f3_i['date_signed'].split('T')[0], '%Y-%m-%d').strftime('%m/%d/%Y')
        
            data_obj['data'] = comm_info_obj
            data_obj['data']['formType'] = "F3X"
            summary_d = {i:(k if k else 0) for i, k in f_3x_list[0].items()}
            f=get_summary_dict(summary_d)
            data_obj['data']['summary'] = json.loads(f)
            #data_obj['data']['summary'] = json.loads(json.dumps(get_summary_dict(f_3x_list[0])))
            data_obj['data']['schedules'] = {'SA': [], 'SB':[]}
            data_obj['data']['schedules']['SA'] = response_inkind_receipt_list
            data_obj['data']['schedules']['SB'] = reponse_sched_b_data
           
           
            
    except Exception as e:
        print (str(e))
        return False
    return data_obj


@api_view(["POST"])
def create_json_builders(request):
    #import ipdb;ipdb.set_trace()
    # Check for Inkind
    try:
        print(" request = ", request)
        report_id = request.data.get('report_id')
        call_from = request.data.get('call_from')
        form_type = request.data.get('form_type')
        committeeid = request.user.username

        print("report_id", report_id)
        print("call_from", call_from)
        print("committeeid", committeeid)

        data_obj = task_sched_a(request)
        # Check for partnership
        # sche_b_data = task_sched_b(request)
        # if data_obj and sche_b_data:

        if data_obj:
            # data_obj['data']['schedules']['SB'] = sche_b_data
            # Check for returned bounced
            
            client = boto3.client('s3')
            transfer = S3Transfer(client)

            tmp_filename = committeeid +'_'+ str(report_id)+'_'+str(up_datetime)+'.json'
            tmp_path='/tmp/'+tmp_filename
        
            json.dump(data_obj, open(tmp_path, 'w'), indent=4)
        
            transfer.upload_file(tmp_path, 'dev-efile-repo', tmp_filename)

            if call_from == "PrintPreviewPDF":
                data_obj = {'form_type':form_type}
                file_obj = {'json_file': ('data.json', open(tmp_path, 'rb'), 'application/json')}

                print("data_obj = ", data_obj)
                print("file_obj = ", file_obj)
                resp = requests.post(settings.NXG_FEC_PRINT_API_URL + settings.NXG_FEC_PRINT_API_VERSION, data=data_obj, files=file_obj)

            elif call_from == "Submit":
                #data_obj = request
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
                file_obj = {'json_file': ('data.json', open(tmp_path, 'rb'), 'application/json')}
                print("data_obj = ", data_obj)
                print("file_obj = ", file_obj)

                resp = requests.post("http://" + settings.DATA_RECEIVE_API_URL + "/v1/upload_filing" , data=data_obj, files=file_obj)


            if not resp.ok:
                return Response(resp.json(), status=status.HTTP_400_BAD_REQUEST)
            else:
                dictprint = resp.json()
                #merged_dict = {**create_json_data, **dictprint}
                return JsonResponse(dictprint, status=status.HTTP_201_CREATED)
        

            #return Response({'status':'Success', 'filepath': tmp_path, 'filename': tmp_filename}, status=status.HTTP_200_OK)
        else:
            return Response('error for json builder', status=status.HTTP_404_BAD_REQUEST)

    except Exception as e:
        return Response("The create_json_builders is throwing an error" + str(e), status=status.HTTP_400_BAD_REQUEST)






