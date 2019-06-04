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
from botocore.exceptions import ClientError
import boto
from boto.s3.key import Key
from django.conf import settings
import re
import csv
from django.core.paginator import Paginator
from fecfiler.core.views import get_list_entity

logger = logging.getLogger(__name__)
# aws s3 bucket connection
conn = boto.connect_s3()

class NoOPError(Exception):
    def __init__(self, *args, **kwargs):
        default_message = 'Raising Custom Exception NoOPError: There are no results found for the specified parameters!'
        if not (args or kwargs): args = (default_message,)
        super().__init__(*args, **kwargs)


"""
******************************************************************************************************************************
Generate Expenditures data Json file API - CORE APP - SPRINT 12 - FNE 769  - BY YESWANTH KUMAR TELLA
******************************************************************************************************************************
"""

def get_entity_expenditure_id(report_id, cmte_id):
    try:
        # GET all rows from schedB table
        forms_obj = []
        query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account, create_date
                       FROM public.sched_b WHERE report_id = %s AND cmte_id = %s""" 
        #AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""

        with connection.cursor() as cursor:
            # import pdb;pdb.set_trace()
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj = data_row[0]
                for d in forms_obj:
                    for i in d:
                        if not d[i]:
                            d[i] = ''
        if forms_obj is []:
            pass
            #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))   
        return forms_obj
    except Exception:
        raise


def get_summary_dict(form3x_header_data):
    form3x_data_string ='{'
    form3x_data_string = form3x_data_string + '"cashOnHandYYYY": 2019,'
    form3x_data_string = form3x_data_string + '"colA": {'
    form3x_data_string = form3x_data_string + '"6b_cashOnHandBeginning": '+ str(form3x_header_data['coh_bop']) + ','
    form3x_data_string = form3x_data_string + '"6c_totalReceipts":'+ str(form3x_header_data['ttl_receipts_sum_page_per']) + ','
    form3x_data_string = form3x_data_string + '"6d_subtotal":'+ str(form3x_header_data['subttl_sum_page_per']) + ','
    form3x_data_string = form3x_data_string + '"7_totalDisbursements":'+ str(form3x_header_data['ttl_disb_sum_page_per']) + ','
    form3x_data_string = form3x_data_string + '"8_cashOnHandAtClose":'+ str(form3x_header_data['coh_cop']) + ','
    form3x_data_string = form3x_data_string + '"9_debtsTo":'+ str(form3x_header_data['debts_owed_to_cmte']) + ','
    form3x_data_string = form3x_data_string + '"10_debtsBy":'+ str(form3x_header_data['debts_owed_by_cmte']) + ','
    form3x_data_string = form3x_data_string + '"11ai_Itemized":'+ str(form3x_header_data['indv_item_contb_per']) + ','
    form3x_data_string = form3x_data_string + '"11aii_Unitemized":'+ str(form3x_header_data['indv_unitem_contb_per']) + ','
    form3x_data_string = form3x_data_string + '"11aiii_Total":'+ str(form3x_header_data['ttl_indv_contb']) + ','
    form3x_data_string = form3x_data_string + '"11b_politicalPartyCommittees":'+ str(form3x_header_data['pol_pty_cmte_contb_per_i']) + ','
    form3x_data_string = form3x_data_string + '"11c_otherPoliticalCommitteesPACs":'+ str(form3x_header_data['other_pol_cmte_contb_per_i']) + ','
    form3x_data_string = form3x_data_string + '"11d_totalContributions":'+ str(form3x_header_data['ttl_contb_col_ttl_per']) + ','
    form3x_data_string = form3x_data_string + '"12_transfersFromAffiliatedOtherPartyCommittees":'+ str(form3x_header_data['tranf_from_affiliated_pty_per']) + ','
    form3x_data_string = form3x_data_string + '"13_allLoansReceived":'+ str(form3x_header_data['all_loans_received_per']) + ','
    form3x_data_string = form3x_data_string + '"14_loanRepaymentsReceived":'+ str(form3x_header_data['loan_repymts_received_per']) + ','
    form3x_data_string = form3x_data_string + '"15_offsetsToOperatingExpendituresRefunds":'+ str(form3x_header_data['offsets_to_op_exp_per_i']) + ','
    form3x_data_string = form3x_data_string + '"16_refundsOfFederalContributions":'+ str(form3x_header_data['fed_cand_contb_ref_per']) + ','
    form3x_data_string = form3x_data_string + '"17_otherFederalReceiptsDividends":'+ str(form3x_header_data['other_fed_receipts_per']) + ','
    form3x_data_string = form3x_data_string + '"18a_transfersFromNonFederalAccount_h3":'+ str(form3x_header_data['tranf_from_nonfed_acct_per']) + ','
    form3x_data_string = form3x_data_string + '"18b_transfersFromNonFederalLevin_h5":'+ str(form3x_header_data['tranf_from_nonfed_levin_per']) + ','
    form3x_data_string = form3x_data_string + '"18c_totalNonFederalTransfers":'+ str(form3x_header_data['ttl_nonfed_tranf_per']) + ','
    form3x_data_string = form3x_data_string + '"19_totalReceipts":'+ str(form3x_header_data['ttl_receipts_per']) + ','
    form3x_data_string = form3x_data_string + '"20_totalFederalReceipts":'+ str(form3x_header_data['ttl_fed_receipts_per']) + ','
    form3x_data_string = form3x_data_string + '"21ai_federalShare":'+ str(form3x_header_data['shared_fed_op_exp_per']) + ','
    form3x_data_string = form3x_data_string + '"21aii_nonFederalShare":'+ str(form3x_header_data['shared_nonfed_op_exp_per']) + ','
    form3x_data_string = form3x_data_string + '"21b_otherFederalOperatingExpenditures":'+ str(form3x_header_data['other_fed_op_exp_per']) + ','
    form3x_data_string = form3x_data_string + '"21c_totalOperatingExpenditures":'+ str(form3x_header_data['ttl_op_exp_per']) + ','
    form3x_data_string = form3x_data_string + '"22_transfersToAffiliatedOtherPartyCommittees":'+ str(form3x_header_data['tranf_to_affliliated_cmte_per']) + ','
    form3x_data_string = form3x_data_string + '"23_contributionsToFederalCandidatesCommittees":'+ str(form3x_header_data['fed_cand_cmte_contb_per']) + ','
    form3x_data_string = form3x_data_string + '"24_independentExpenditures":'+ str(form3x_header_data['indt_exp_per']) + ','
    form3x_data_string = form3x_data_string + '"25_coordinatedExpenditureMadeByPartyCommittees":'+ str(form3x_header_data['coord_exp_by_pty_cmte_per']) + ','
    form3x_data_string = form3x_data_string + '"26_loanRepayments":'+ str(form3x_header_data['loan_repymts_made_per']) + ','
    form3x_data_string = form3x_data_string + '"27_loansMade":'+ str(form3x_header_data['loans_made_per']) + ','
    form3x_data_string = form3x_data_string + '"28a_individualsPersons":'+ str(form3x_header_data['indv_contb_ref_per']) + ','
    form3x_data_string = form3x_data_string + '"28b_politicalPartyCommittees":'+ str(form3x_header_data['pol_pty_cmte_contb_per_ii']) + ','
    form3x_data_string = form3x_data_string + '"28c_otherPoliticalCommittees":'+ str(form3x_header_data['other_pol_cmte_contb_per_ii']) + ','
    form3x_data_string = form3x_data_string + '"28d_totalContributionsRefunds":'+ str(form3x_header_data['ttl_contb_ref_per_i']) + ','
    form3x_data_string = form3x_data_string + '"29_otherDisbursements":'+ str(form3x_header_data['other_disb_per']) + ','
    form3x_data_string = form3x_data_string + '"30ai_sharedFederalActivity_h6_fedShare":'+ str(form3x_header_data['shared_fed_actvy_fed_shr_per']) + ','
    form3x_data_string = form3x_data_string + '"30aii_sharedFederalActivity_h6_nonFed":'+ str(form3x_header_data['shared_fed_actvy_nonfed_per']) + ','
    form3x_data_string = form3x_data_string + '"30b_nonAllocable_100_federalElectionActivity":'+ str(form3x_header_data['non_alloc_fed_elect_actvy_per']) + ','
    form3x_data_string = form3x_data_string + '"30c_totalFederalElectionActivity":'+ str(form3x_header_data['ttl_fed_elect_actvy_per']) + ','
    form3x_data_string = form3x_data_string + '"31_totalDisbursements":'+ str(form3x_header_data['ttl_disb_per']) + ','
    form3x_data_string = form3x_data_string + '"32_totalFederalDisbursements":'+ str(form3x_header_data['ttl_fed_disb_per']) + ','
    form3x_data_string = form3x_data_string + '"33_totalContributions":'+ str(form3x_header_data['ttl_contb_per']) + ','
    form3x_data_string = form3x_data_string + '"34_totalContributionRefunds":'+ str(form3x_header_data['ttl_contb_ref_per_ii']) + ','
    form3x_data_string = form3x_data_string + '"35_netContributions":'+ str(form3x_header_data['net_contb_per']) + ','
    form3x_data_string = form3x_data_string + '"36_totalFederalOperatingExpenditures":'+ str(form3x_header_data['ttl_fed_op_exp_per']) + ','
    form3x_data_string = form3x_data_string + '"37_offsetsToOperatingExpenditures":'+ str(form3x_header_data['offsets_to_op_exp_per_ii']) + ','
    form3x_data_string = form3x_data_string + '"38_netOperatingExpenditures":'+ str(form3x_header_data['net_op_exp_per'])
    form3x_data_string = form3x_data_string + '},'
    form3x_data_string = form3x_data_string + '"colB": {'
    form3x_data_string = form3x_data_string + '"6a_cashOnHandJan_1":'+ str(form3x_header_data['coh_begin_calendar_yr'])+','
    form3x_data_string = form3x_data_string + '"6c_totalReceipts":'+ str(form3x_header_data['ttl_receipts_sum_page_ytd']) + ','
    form3x_data_string = form3x_data_string + '"6d_subtotal":'+ str(form3x_header_data['subttl_sum_ytd']) + ','
    form3x_data_string = form3x_data_string + '"7_totalDisbursements":'+ str(form3x_header_data['ttl_disb_sum_page_ytd']) + ','
    form3x_data_string = form3x_data_string + '"8_cashOnHandAtClose":'+ str(form3x_header_data['coh_coy']) + ','
    form3x_data_string = form3x_data_string + '"11ai_itemized":'+ str(form3x_header_data['indv_item_contb_ytd']) + ','
    form3x_data_string = form3x_data_string + '"11aii_unitemized":'+ str(form3x_header_data['indv_unitem_contb_ytd']) + ','
    form3x_data_string = form3x_data_string + '"11aiii_total":'+ str(form3x_header_data['ttl_indv_contb_ytd']) + ','
    form3x_data_string = form3x_data_string + '"11b_politicalPartyCommittees":'+ str(form3x_header_data['pol_pty_cmte_contb_ytd_i']) + ','
    form3x_data_string = form3x_data_string + '"11c_otherPoliticalCommitteesPACs":'+ str(form3x_header_data['other_pol_cmte_contb_ytd_i']) + ','
    form3x_data_string = form3x_data_string + '"11d_totalContributions":'+ str(form3x_header_data['ttl_contb_col_ttl_ytd']) + ','
    form3x_data_string = form3x_data_string + '"12_transfersFromAffiliatedOtherPartyCommittees":'+ str(form3x_header_data['tranf_from_affiliated_pty_ytd']) + ','
    form3x_data_string = form3x_data_string + '"13_allLoansReceived":'+ str(form3x_header_data['all_loans_received_ytd']) + ','
    form3x_data_string = form3x_data_string + '"14_loanRepaymentsReceived":'+ str(form3x_header_data['loan_repymts_received_ytd']) + ','
    form3x_data_string = form3x_data_string + '"15_offsetsToOperatingExpendituresRefunds":'+ str(form3x_header_data['offsets_to_op_exp_ytd_i']) + ','
    form3x_data_string = form3x_data_string + '"16_refundsOfFederalContributions":'+ str(form3x_header_data['fed_cand_cmte_contb_ytd']) + ','
    form3x_data_string = form3x_data_string + '"17_otherFederalReceiptsDividends":'+ str(form3x_header_data['other_fed_receipts_ytd']) + ','
    form3x_data_string = form3x_data_string + '"18a_transfersFromNonFederalAccount_h3":'+ str(form3x_header_data['tranf_from_nonfed_acct_ytd']) + ','
    form3x_data_string = form3x_data_string + '"18b_transfersFromNonFederalLevin_h5":'+ str(form3x_header_data['tranf_from_nonfed_levin_ytd']) + ','
    form3x_data_string = form3x_data_string + '"18c_totalNonFederalTransfers":'+ str(form3x_header_data['ttl_nonfed_tranf_ytd']) + ','
    form3x_data_string = form3x_data_string + '"19_totalReceipts":'+ str(form3x_header_data['ttl_receipts_ytd']) + ','
    form3x_data_string = form3x_data_string + '"20_totalFederalReceipts":'+ str(form3x_header_data['ttl_fed_receipts_ytd']) + ','
    form3x_data_string = form3x_data_string + '"21ai_federalShare":'+ str(form3x_header_data['shared_fed_op_exp_ytd']) + ','
    form3x_data_string = form3x_data_string + '"21aii_nonFederalShare":'+ str(form3x_header_data['shared_nonfed_op_exp_ytd']) + ','
    form3x_data_string = form3x_data_string + '"21b_otherFederalOperatingExpenditures":'+ str(form3x_header_data['other_fed_op_exp_ytd']) + ','
    form3x_data_string = form3x_data_string + '"21c_totalOperatingExpenditures":'+ str(form3x_header_data['ttl_op_exp_ytd']) + ','
    form3x_data_string = form3x_data_string + '"22_transfersToAffiliatedOtherPartyCommittees":'+ str(form3x_header_data['tranf_to_affilitated_cmte_ytd']) + ','
    form3x_data_string = form3x_data_string + '"23_contributionsToFederalCandidatesCommittees":'+ str(form3x_header_data['fed_cand_cmte_contb_ref_ytd']) + ','
    form3x_data_string = form3x_data_string + '"24_independentExpenditures":'+ str(form3x_header_data['indt_exp_ytd']) + ','
    form3x_data_string = form3x_data_string + '"25_coordinatedExpendituresMadeByPartyCommittees":'+ str(form3x_header_data['coord_exp_by_pty_cmte_ytd']) + ','
    form3x_data_string = form3x_data_string + '"26_loanRepayments":'+ str(form3x_header_data['loan_repymts_made_ytd']) + ','
    form3x_data_string = form3x_data_string + '"27_loansMade":'+ str(form3x_header_data['loans_made_ytd']) + ','
    form3x_data_string = form3x_data_string + '"28a_individualPersons":'+ str(form3x_header_data['indv_contb_ref_ytd']) + ','
    form3x_data_string = form3x_data_string + '"28b_politicalPartyCommittees":'+ str(form3x_header_data['pol_pty_cmte_contb_ytd_ii']) + ','
    form3x_data_string = form3x_data_string + '"28c_otherPoliticalCommittees":'+ str(form3x_header_data['other_pol_cmte_contb_ytd_ii']) + ','
    form3x_data_string = form3x_data_string + '"28d_totalContributionRefunds":'+ str(form3x_header_data['ttl_contb_ref_ytd_i']) + ','
    form3x_data_string = form3x_data_string + '"29_otherDisbursements":'+ str(form3x_header_data['other_disb_ytd']) + ','
    form3x_data_string = form3x_data_string + '"30ai_sharedFederalActivity_h6_federalShare":'+ str(form3x_header_data['shared_fed_actvy_fed_shr_ytd']) + ','
    form3x_data_string = form3x_data_string + '"30aii_sharedFederalActivity_h6_nonFederal":'+ str(form3x_header_data['shared_fed_actvy_nonfed_ytd']) + ','
    form3x_data_string = form3x_data_string + '"30b_nonAllocable_100_federalElectionActivity":'+ str(form3x_header_data['non_alloc_fed_elect_actvy_ytd']) + ','
    form3x_data_string = form3x_data_string + '"30c_totalFederalElectionActivity":'+ str(form3x_header_data['ttl_fed_elect_actvy_ytd']) + ','
    form3x_data_string = form3x_data_string + '"31_totalDisbursements":'+ str(form3x_header_data['ttl_disb_ytd']) + ','
    form3x_data_string = form3x_data_string + '"32_totalFederalDisbursements":'+ str(form3x_header_data['ttl_fed_disb_ytd']) + ','
    form3x_data_string = form3x_data_string + '"33_totalContributions":'+ str(form3x_header_data['ttl_contb_ytd']) + ','
    form3x_data_string = form3x_data_string + '"34_totalContributionRefunds":'+ str(form3x_header_data['ttl_contb_ref_ytd_ii']) + ','
    form3x_data_string = form3x_data_string + '"35_netContributions":'+ str(form3x_header_data['net_contb_ytd']) + ','
    form3x_data_string = form3x_data_string + '"36_totalFederalOperatingExpenditures":'+ str(form3x_header_data['ttl_fed_op_exp_ytd']) + ','
    form3x_data_string = form3x_data_string + '"37_offsetsToOperatingExpenditures":'+ str(form3x_header_data['offsets_to_op_exp_ytd_ii']) + ','
    form3x_data_string = form3x_data_string + '"38_netOperatingExpenditures":'+ str(form3x_header_data['net_op_exp_ytd'])
    form3x_data_string = form3x_data_string + '}'
    form3x_data_string = form3x_data_string + '}'
    return form3x_data_string

def get_committee_mater_values(cmte_id):
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
            committee_info_dict['filercommitteeIdNumber'] = forms_obj['cmte_id']
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



@api_view(["POST"])
def create_f3x_expenditure_json_file(request):
    #creating a JSON file so that it is handy for all the public API's   
    try:
        # import ipdb;ipdb.set_trace()
        report_id = request.POST.get('report_id')
        comm_info = True
        if comm_info:
            committeeid = request.user.username
            comm_info_obj = get_committee_mater_values(committeeid)
            header = {
                "version":"8.3",
                "softwareName":"ABC Inc",
                "softwareVersion":"1.02 Beta",
                "additionalInfomation":"Any other useful information"
            }
            f_3x_list = get_f3x_report_data(committeeid, report_id)
            report_info = get_list_report(report_id, committeeid)
            response_expenditure_receipt_list = []
            # form3x_header_data= get_f3x_report_data(committeeid, report_id)
            for f3_i in f_3x_list:
                #response_dict_out = {}
                #response_dict_receipt = {}
                print (f3_i['report_id'])
                entity_id_list = get_entity_expenditure_id(f3_i['report_id'], f3_i['cmte_id'])
                if not entity_id_list:
                    continue
                print ("we got the data")
                # comm_id = Committee.objects.get(committeeid=request.user.username)
                for entity_obj in entity_id_list:
                    response_dict_out = {}                             
                    response_dict_receipt = {}
                    list_entity = get_list_entity(entity_obj['entity_id'], entity_obj['cmte_id'])
                    if not list_entity:
                        continue
                    else:
                        list_entity = list_entity[0]
                    response_dict_receipt['transactionTypeCode'] = entity_obj['transaction_type']
                    response_dict_receipt['transactionId'] = entity_obj['transaction_id']
                    response_dict_receipt['backReferenceTransactionIdNumber'] = entity_obj['back_ref_transaction_id']
                    response_dict_receipt['backReferenceScheduleName'] = entity_obj['back_ref_sched_name']
                    response_dict_receipt['entityType'] = list_entity['entity_type']

                    response_dict_receipt['payeeOrganizationName'] = list_entity['entity_name']
                    response_dict_receipt['payeeLastName'] = list_entity['last_name']
                    response_dict_receipt['payeeFirstName'] = list_entity['first_name']
                    response_dict_receipt['payeeMiddleName'] = list_entity['middle_name']
                    response_dict_receipt['payeePrefix'] = list_entity['preffix']
                    response_dict_receipt['payeeSuffix'] = list_entity['suffix']
                    response_dict_receipt['payeeStreet1 '] = list_entity['street_1']
                    response_dict_receipt['payeeStreet2'] = list_entity['street_2']
                    response_dict_receipt['payeeCity'] = list_entity['city']
                    response_dict_receipt['payeeState'] = list_entity['state']
                    response_dict_receipt['payeeZip'] = list_entity['zip_code']
                    response_dict_receipt['expenditureDate'] = entity_obj['expenditure_date'].replace('-','')
                    response_dict_receipt['expenditureAmount'] = "%.2f" % round(entity_obj['expenditure_amount'],2)
                    response_dict_receipt['expenditurePurposeDescription'] = entity_obj['expenditure_purpose']
                    response_dict_receipt['categoryCode'] = '15G'
                    response_dict_receipt['memoCode'] = entity_obj['memo_code']
                    response_dict_receipt['memoDescription'] = entity_obj['memo_text']

                    # response_expendtiture_out_list.append(response_dict_out)
                    response_expenditure_receipt_list.append(response_dict_receipt)

            # import ipdb;ipdb.set_trace()$
            # get_list_entity(entity_id, comm_info.committeeid)

            data_obj = {}
            data_obj['header'] = header
            comm_info_obj['changeOfAddress'] = f3_i['cmte_addr_chg_flag'] if f3_i['cmte_addr_chg_flag'] else ''
            comm_info_obj['amendmentIndicator'] = f3_i['amend_ind']
            comm_info_obj['reportCode'] = f3_i['report_type']
            comm_info_obj['electionState'] = f3_i['state_of_election'] if f3_i['state_of_election'] else ''
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
            comm_info_obj['amendmentNumber'] = report_info[0]['amend_number']
            data_obj['data'] = comm_info_obj
            data_obj['data']['formType'] = "F3X"
            data_obj['data']['summary'] = json.loads(get_summary_dict(f_3x_list[0]))
            data_obj['data']['Schedule'] = {'SB':[]}
            data_obj['data']['Schedule']['SB'] = response_expenditure_receipt_list
            bucket = conn.get_bucket("dev-efile-repo")
            k = Key(bucket)
            print(k)
            k.content_type = "application/json"
            k.set_contents_from_string(json.dumps(data_obj, indent=4))            
            url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")
            tmp_filename = '/tmp/' + committeeid + '_'+str(report_id)+'.json'
            vdata = {}
            # vdata['form_type'] = "F3X"
            # vdata['committeeid'] = comm_info.committeeid
            json.dump(data_obj, open(tmp_filename, 'w'))
            vfiles = {}
            vfiles["json_file"] = open(tmp_filename, 'rb')
            res = requests.post("https://" + settings.DATA_RECEIVE_API_URL + "/v1/send_data" , data=data_obj, files=vfiles)
            # import ipdb; ipdb.set_trace()
            return Response('', status=status.HTTP_200_OK)
            
        else:
            return Response({"FEC Error 007":"This user does not have a submitted CommInfo object"}, status=status.HTTP_400_BAD_REQUEST)
            
    except CommitteeInfo.DoesNotExist:
        return Response({"FEC Error 009":"An unexpected error occurred while processing your request"}, status=status.HTTP_400_BAD_REQUEST)

"""

******************************************************************************************************************************
END - Generate Partnership  - CORE APP
******************************************************************************************************************************
"""

def get_f3x_SA_data(cmte_id, report_id):
    try:
        query_string = """SELECT * FROM public.sched_a WHERE cmte_id = %s AND report_id = %s"""
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id], [report_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            pass
   
        return forms_obj
    except Exception:
        raise

def get_amendmentNumber(cmte_id, report_id):
    try:
        query_string = """SELECT amend_number FROM public.reports WHERE cmte_id = %s AND report_id = %s"""
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id], [report_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            pass

        return forms_obj
    except Exception:
        raise



# def get_f3x_report_data(cmte_id, report_id):
#     try:
#         query_string = """SELECT * FROM public.form_3x WHERE cmte_id = %s AND report_id = %s"""
#         forms_obj = None
#         with connection.cursor() as cursor:
#             cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id], [report_id])
#             for row in cursor.fetchall():
#                 data_row = list(row)
#                 forms_obj=data_row[0]
#         if forms_obj is None:
#             pass
#             #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))   
#         return forms_obj
#     except Exception:
#         raise

def get_f3x_SA_children_data(cmte_id, report_id, transaction_id):
    try:
        query_string = """SELECT * FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND transaction_id = %s"""
        forms_obj = None
        with connection.cursor() as cursor:
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""", [cmte_id], [report_id], [transaction_id])
            for row in cursor.fetchall():
                data_row = list(row)
                forms_obj=data_row[0]
        if forms_obj is None:
            pass
   
        return forms_obj
    except Exception:
        raise

@api_view(["POST"])
def build_form3x_json_file(request):
    #creating a JSON file so that it is handy for all the public API's   
    try:
        # import ipdb;ipdb.set_trace()
        #comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username, is_submitted=True).last()
        if 'reportid' in request.data and (not request.data['reportid']=='') and int(request.data['reportid'])>=1:

            comm_info = CommitteeInfo.objects.filter(committeeid=request.data['committeeid'])

            if comm_info:
                comm_info = comm_info[0]
                serializer = CommitteeInfoSerializer(comm_info)
                header = {
                    "version":"8.3",
                    "softwareName":"ABC Inc",
                    "softwareVersion":"1.02 Beta",
                    "additionalInfomation":"Any other useful information"
                }

                """
                form3x_header_string ='{"header": {
                            "version": "8.3",
                            "softwareName": "nxg_fec",
                            "softwareVersion": "1.01 Beta",
                            "additionalInfomation": ""
                        },
                        "data": {'
                """
                form3x_header_string ='{"header": { "version": "8.3","softwareName": "nxg_fec", "softwareVersion": "1.01 Beta", "additionalInfomation": ""   }, "data": {'
                amendment_number_data=get_amendmentNumber(committeeid, request.data['reportid'])  
                if amendment_number_data:
                    amendment_number = amendment_number_data[0]['amend_number']    

                form3x_header_data= get_f3x_report_data(committeeid, request.data['reportid'])
                if form3x_header_data:
                    form3x_header_data=form3x_header_data[0]
                    form3x_header_string = form3x_header_string +'"committeeId": "'+form3x_header_data['cmte_id']+'",'
                    #form3x_header_string = form3x_header_string +'"password": "'+form3x_header_data['cmte_id']+'",'
                    form3x_header_string = form3x_header_string +'"password":"test" ,'
                    form3x_header_string = form3x_header_string +'"committeeName": "'+form3x_header_data['cmte_nm']+'",'
                    form3x_header_string = form3x_header_string +'"changeOfAddress": "'+form3x_header_data['cmte_addr_chg_flag']+'",'
                    form3x_header_string = form3x_header_string +'"street1": "'+form3x_header_data['cmte_street_1']+'",'
                    form3x_header_string = form3x_header_string +'"street2": "'+form3x_header_data['cmte_street_2']+'",'
                    form3x_header_string = form3x_header_string +'"city": "'+form3x_header_data['cmte_city']+'",'
                    form3x_header_string = form3x_header_string +'"state": "'+form3x_header_data['cmte_state']+'",'
                    form3x_header_string = form3x_header_string +'"zipCode": "'+form3x_header_data['cmte_zip']+'",'
                    form3x_header_string = form3x_header_string +'"formType": "'+form3x_header_data['form_type']+'",'
                    form3x_header_string = form3x_header_string +'"amendmentIndicator": "'+form3x_header_data['amend_ind']+'",'
                    form3x_header_string = form3x_header_string +'"amendmentNumber":' +amendment_number+','
                    form3x_header_string = form3x_header_string +'"reportCode": "'+form3x_header_data['report_type']+'",'
                    form3x_header_string = form3x_header_string +'"electionDate": "'+date_format(form3x_header_data['date_of_election'])+'",'
                    form3x_header_string = form3x_header_string +'"electionState": "'+form3x_header_data['state_of_election']+'",'
                    form3x_header_string = form3x_header_string +'"coverageStartDate": "'+date_format(form3x_header_data['cvg_start_dt'])+'",'
                    form3x_header_string = form3x_header_string +'"coverageEndDate": "'+date_format(form3x_header_data['cvg_end_dt'])+'",'
                    form3x_header_string = form3x_header_string +'"treasurerLastName": "'+form3x_header_data['treasurer_last_name']+'",'
                    form3x_header_string = form3x_header_string +'"treasurerFirstName": "'+form3x_header_data['treasurer_first_name']+'",'
                    form3x_header_string = form3x_header_string +'"treasurerMiddleName": "'+form3x_header_data['treasurer_middle_name']+'",'
                    form3x_header_string = form3x_header_string +'"treasurerPrefix": "'+form3x_header_data['treasurer_prefix']+'",'
                    form3x_header_string = form3x_header_string +'"treasurerSuffix": "'+form3x_header_data['treasurer_suffix']+'",'
                    form3x_header_string = form3x_header_string +'"dateSigned": "'+date_format(form3x_header_data['date_signed'])+'",'

                
                    
                    #form3x_sa_list = forn3x_header_data(request.user.username)
                    #form3x_json_header_list=""
                    form3x_data_string ='"summary": {'
                    form3x_data_string = form3x_data_string + '"cashOnHandYYYY": 2019,'
                    form3x_data_string = form3x_data_string + '"colA": {'
                    form3x_data_string = form3x_data_string + '"6b_cashOnHandBeginning": '+ form3x_header_data['coh_bop'] + ','
                    form3x_data_string = form3x_data_string + '"6c_totalReceipts":'+ form3x_header_data['ttl_receipts_sum_page_per'] + ','
                    form3x_data_string = form3x_data_string + '"6d_subtotal":'+ form3x_header_data['subttl_sum_page_per'] + ','
                    form3x_data_string = form3x_data_string + '"7_totalDisbursements":'+ form3x_header_data['ttl_disb_sum_page_per'] + ','
                    form3x_data_string = form3x_data_string + '"8_cashOnHandAtClose":'+ form3x_header_data['coh_cop'] + ','
                    form3x_data_string = form3x_data_string + '"9_debtsTo":'+ form3x_header_data['debts_owed_to_cmte'] + ','
                    form3x_data_string = form3x_data_string + '"10_debtsBy"'+ form3x_header_data['debts_owed_by_cmte'] + ','
                    form3x_data_string = form3x_data_string + '"11ai_Itemized":'+ form3x_header_data['indv_item_contb_per'] + ','
                    form3x_data_string = form3x_data_string + '"11aii_Unitemized":'+ form3x_header_data['indv_unitem_contb_per'] + ','
                    form3x_data_string = form3x_data_string + '"11aiii_Total":'+ form3x_header_data['ttl_indv_contb'] + ','
                    form3x_data_string = form3x_data_string + '"11b_politicalPartyCommittees":'+ form3x_header_data['pol_pty_cmte_contb_per_i'] + ','
                    form3x_data_string = form3x_data_string + '"11c_otherPoliticalCommitteesPACs":'+ form3x_header_data['other_pol_cmte_contb_per_i'] + ','
                    form3x_data_string = form3x_data_string + '"11d_totalContributions":'+ form3x_header_data['ttl_contb_col_ttl_per'] + ','
                    form3x_data_string = form3x_data_string + '"12_transfersFromAffiliatedOtherPartyCommittees":'+ form3x_header_data['tranf_from_affiliated_pty_per'] + ','
                    form3x_data_string = form3x_data_string + '"13_allLoansReceived":'+ form3x_header_data['all_loans_received_per'] + ','
                    form3x_data_string = form3x_data_string + '"14_loanRepaymentsReceived":'+ form3x_header_data['loan_repymts_received_per'] + ','
                    form3x_data_string = form3x_data_string + '"15_offsetsToOperatingExpendituresRefunds":'+ form3x_header_data['offsets_to_op_exp_per_i'] + ','
                    form3x_data_string = form3x_data_string + '"16_refundsOfFederalContributions":'+ form3x_header_data['fed_cand_contb_ref_per'] + ','
                    form3x_data_string = form3x_data_string + '"17_otherFederalReceiptsDividends":'+ form3x_header_data['other_fed_receipts_per'] + ','
                    form3x_data_string = form3x_data_string + '"18a_transfersFromNonFederalAccount_h3":'+ form3x_header_data['tranf_from_nonfed_acct_per'] + ','
                    form3x_data_string = form3x_data_string + '"18b_transfersFromNonFederalLevin_h5":'+ form3x_header_data['tranf_from_nonfed_levin_per'] + ','
                    form3x_data_string = form3x_data_string + '"18c_totalNonFederalTransfers":'+ form3x_header_data['ttl_nonfed_tranf_per'] + ','
                    form3x_data_string = form3x_data_string + '"19_totalReceipts":'+ form3x_header_data['ttl_receipts_per'] + ','
                    form3x_data_string = form3x_data_string + '"20_totalFederalReceipts":'+ form3x_header_data['ttl_fed_receipts_per'] + ','
                    form3x_data_string = form3x_data_string + '"21ai_federalShare":'+ form3x_header_data['shared_fed_op_exp_per'] + ','
                    form3x_data_string = form3x_data_string + '"21aii_nonFederalShare":'+ form3x_header_data['shared_nonfed_op_exp_per'] + ','
                    form3x_data_string = form3x_data_string + '"21b_otherFederalOperatingExpenditures":'+ form3x_header_data['other_fed_op_exp_per'] + ','
                    form3x_data_string = form3x_data_string + '"21c_totalOperatingExpenditures":'+ form3x_header_data['ttl_op_exp_per'] + ','
                    form3x_data_string = form3x_data_string + '"22_transfersToAffiliatedOtherPartyCommittees":'+ form3x_header_data['tranf_to_affliliated_cmte_per'] + ','
                    form3x_data_string = form3x_data_string + '"23_contributionsToFederalCandidatesCommittees":'+ form3x_header_data['fed_cand_cmte_contb_per'] + ','
                    form3x_data_string = form3x_data_string + '"24_independentExpenditures":'+ form3x_header_data['indt_exp_per'] + ','
                    form3x_data_string = form3x_data_string + '"25_coordinatedExpenditureMadeByPartyCommittees":'+ form3x_header_data['coord_exp_by_pty_cmte_per'] + ','
                    form3x_data_string = form3x_data_string + '"26_loanRepayments":'+ form3x_header_data['loan_repymts_made_per'] + ','
                    form3x_data_string = form3x_data_string + '"27_loansMade":'+ form3x_header_data['loans_made_per'] + ','
                    form3x_data_string = form3x_data_string + '"28a_individualsPersons":'+ form3x_header_data['indv_contb_ref_per'] + ','
                    form3x_data_string = form3x_data_string + '"28b_politicalPartyCommittees":'+ form3x_header_data['pol_pty_cmte_contb_per_ii'] + ','
                    form3x_data_string = form3x_data_string + '"28c_otherPoliticalCommittees":'+ form3x_header_data['other_pol_cmte_contb_per_ii'] + ','
                    form3x_data_string = form3x_data_string + '"28d_totalContributionsRefunds":'+ form3x_header_data['ttl_contb_ref_per_i'] + ','
                    form3x_data_string = form3x_data_string + '"29_otherDisbursements":'+ form3x_header_data['other_disb_per'] + ','
                    form3x_data_string = form3x_data_string + '"30ai_sharedFederalActivity_h6_fedShare":'+ form3x_header_data['shared_fed_actvy_fed_shr_per'] + ','
                    form3x_data_string = form3x_data_string + '"30aii_sharedFederalActivity_h6_nonFed":'+ form3x_header_data['shared_fed_actvy_nonfed_per'] + ','
                    form3x_data_string = form3x_data_string + '"30b_nonAllocable_100_federalElectionActivity":'+ form3x_header_data['non_alloc_fed_elect_actvy_per'] + ','
                    form3x_data_string = form3x_data_string + '"30c_totalFederalElectionActivity":'+ form3x_header_data['ttl_fed_elect_actvy_per'] + ','
                    form3x_data_string = form3x_data_string + '"31_totalDisbursements":'+ form3x_header_data['ttl_disb_per'] + ','
                    form3x_data_string = form3x_data_string + '"32_totalFederalDisbursements":'+ form3x_header_data['ttl_fed_disb_per'] + ','
                    form3x_data_string = form3x_data_string + '"33_totalContributions":'+ form3x_header_data['ttl_contb_per'] + ','
                    form3x_data_string = form3x_data_string + '"34_totalContributionRefunds":'+ form3x_header_data['ttl_contb_ref_per_ii'] + ','
                    form3x_data_string = form3x_data_string + '"35_netContributions":'+ form3x_header_data['net_contb_per'] + ','
                    form3x_data_string = form3x_data_string + '"36_totalFederalOperatingExpenditures":'+ form3x_header_data['ttl_fed_op_exp_per'] + ','
                    form3x_data_string = form3x_data_string + '"37_offsetsToOperatingExpenditures":'+ form3x_header_data['offsets_to_op_exp_per_ii'] + ','
                    form3x_data_string = form3x_data_string + '"38_netOperatingExpenditures":'+ form3x_header_data['net_op_exp_per']
                    form3x_data_string = form3x_data_string + '},'
                    form3x_data_string = form3x_data_string + '"colB": {'
                    form3x_data_string = form3x_data_string + '"6a_cashOnHandJan_1":'+ form3x_header_data['coh_begin_calendar_yr']+','
                    form3x_data_string = form3x_data_string + '"6c_totalReceipts":'+ form3x_header_data['ttl_receipts_sum_page_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"6d_subtotal":'+ form3x_header_data['subttl_sum_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"7_totalDisbursements":'+ form3x_header_data['ttl_disb_sum_page_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"8_cashOnHandAtClose":'+ form3x_header_data['coh_coy'] + ','
                    form3x_data_string = form3x_data_string + '"11ai_itemized":'+ form3x_header_data['indv_item_contb_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"11aii_unitemized":'+ form3x_header_data['indv_unitem_contb_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"11aiii_total":'+ form3x_header_data[''] + ','
                    form3x_data_string = form3x_data_string + '"11b_politicalPartyCommittees":'+ form3x_header_data['pol_pty_cmte_contb_ytd_i'] + ','
                    form3x_data_string = form3x_data_string + '"11c_otherPoliticalCommitteesPACs":'+ form3x_header_data['other_pol_cmte_contb_ytd_i'] + ','
                    form3x_data_string = form3x_data_string + '"11d_totalContributions":'+ form3x_header_data['ttl_contb_col_ttl_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"12_transfersFromAffiliatedOtherPartyCommittees":'+ form3x_header_data['tranf_from_affiliated_pty_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"13_allLoansReceived":'+ form3x_header_data['all_loans_received_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"14_loanRepaymentsReceived":'+ form3x_header_data['loan_repymts_received_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"15_offsetsToOperatingExpendituresRefunds":'+ form3x_header_data['offsets_to_op_exp_ytd_i'] + ','
                    form3x_data_string = form3x_data_string + '"16_refundsOfFederalContributions":'+ form3x_header_data['fed_cand_cmte_contb_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"17_otherFederalReceiptsDividends":'+ form3x_header_data['other_fed_receipts_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"18a_transfersFromNonFederalAccount_h3":'+ form3x_header_data['tranf_from_nonfed_acct_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"18b_transfersFromNonFederalLevin_h5":'+ form3x_header_data['tranf_from_nonfed_levin_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"18c_totalNonFederalTransfers":'+ form3x_header_data['ttl_nonfed_tranf_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"19_totalReceipts":'+ form3x_header_data['ttl_receipts_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"20_totalFederalReceipts":'+ form3x_header_data['ttl_fed_receipts_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"21ai_federalShare":'+ form3x_header_data['shared_fed_op_exp_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"21aii_nonFederalShare":'+ form3x_header_data['shared_nonfed_op_exp_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"21b_otherFederalOperatingExpenditures":'+ form3x_header_data['other_fed_op_exp_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"21c_totalOperatingExpenditures":'+ form3x_header_data['ttl_op_exp_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"22_transfersToAffiliatedOtherPartyCommittees":'+ form3x_header_data['tranf_to_affilitated_cmte_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"23_contributionsToFederalCandidatesCommittees":'+ form3x_header_data['fed_cand_cmte_contb_ref_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"24_independentExpenditures":'+ form3x_header_data['indt_exp_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"25_coordinatedExpendituresMadeByPartyCommittees":'+ form3x_header_data['coord_exp_by_pty_cmte_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"26_loanRepayments":'+ form3x_header_data['loan_repymts_made_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"27_loansMade":'+ form3x_header_data['loans_made_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"28a_individualPersons":'+ form3x_header_data['indv_contb_ref_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"28b_politicalPartyCommittees":'+ form3x_header_data['pol_pty_cmte_contb_ytd_ii'] + ','
                    form3x_data_string = form3x_data_string + '"28c_otherPoliticalCommittees":'+ form3x_header_data['other_pol_cmte_contb_ytd_ii'] + ','
                    form3x_data_string = form3x_data_string + '"28d_totalContributionRefunds":'+ form3x_header_data['ttl_contb_ref_ytd_i'] + ','
                    form3x_data_string = form3x_data_string + '"29_otherDisbursements":'+ form3x_header_data['other_disb_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"30ai_sharedFederalActivity_h6_federalShare":'+ form3x_header_data['shared_fed_actvy_fed_shr_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"30aii_sharedFederalActivity_h6_nonFederal":'+ form3x_header_data['shared_fed_actvy_nonfed_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"30b_nonAllocable_100_federalElectionActivity":'+ form3x_header_data['non_alloc_fed_elect_actvy_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"30c_totalFederalElectionActivity":'+ form3x_header_data['ttl_fed_elect_actvy_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"31_totalDisbursements":'+ form3x_header_data['ttl_disb_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"32_totalFederalDisbursements":'+ form3x_header_data['ttl_fed_disb_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"33_totalContributions":'+ form3x_header_data['ttl_contb_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"34_totalContributionRefunds":'+ form3x_header_data['ttl_contb_ref_ytd_ii'] + ','
                    form3x_data_string = form3x_data_string + '"35_netContributions":'+ form3x_header_data['net_contb_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"36_totalFederalOperatingExpenditures":'+ form3x_header_data['ttl_fed_op_exp_ytd'] + ','
                    form3x_data_string = form3x_data_string + '"37_offsetsToOperatingExpenditures":'+ form3x_header_data['offsets_to_op_exp_ytd_ii'] + ','
                    form3x_data_string = form3x_data_string + '"38_netOperatingExpenditures": :'+ form3x_header_data['net_op_exp_ytd']
                    form3x_data_string = form3x_data_string + '}'
                    form3x_data_string = form3x_data_string + '},'
                    form3x_data_string = form3x_data_string + '"schedules": {'
                    form3x_data_string = form3x_data_string + '"SA": [{'
                    
                    form3x_sa_list = get_f3x_SA_data(committeeid, request.data['reportid'])
                    frx_receipt_data_list = []
                    response_inkind_out_list = []
                    for forn3x_sa_data in form3x_sa_list:
                        response_dict_out = {}
                        frx_receipt_data = {}
                        print (forn3x_sa_data['report_id'])
                        entity_id_list = get_entity_sched_a_data(forn3x_sa_data['report_id'], forn3x_sa_data['cmte_id'])
                        if not entity_id_list:
                            continue
                        print ("we got the data")
                        # comm_id = Committee.objects.get(committeeid=request.user.username)
                        for entity_obj in entity_id_list:
                            list_entity = get_list_entity(entity_obj['entity_id'], entity_obj['cmte_id'])
                            if not list_entity:
                                continue
                            else:
                                list_entity = list_entity[0]
                                json_sa_string= '"transactionTypeCode":'+entity_obj['transaction_type']+','
                                json_sa_string= json_sa_string + '"transactionId":'+ entity_obj['transaction_id']+','
                                json_sa_string= json_sa_string + '"entityType":'+entity_obj['entity_type']+','
                                json_sa_string= json_sa_string + '"ontributorLastName":'+list_entity['last_name']+','
                                json_sa_string= json_sa_string + '"contributorFirstName":'+list_entity['first_name']+','
                                json_sa_string= json_sa_string + '"contributorMiddleName":'+list_entity['preffix']+','
                                json_sa_string= json_sa_string + '"contributorPrefix":'+list_entity['transaction_type']+','
                                json_sa_string= json_sa_string + '"contributorSuffix":'+list_entity['suffix']+','
                                json_sa_string= json_sa_string + '"contributorStreet1":'+list_entity['street_1']+','
                                json_sa_string= json_sa_string + '"contributorStreet2":'+list_entity['street_2']+','
                                json_sa_string= json_sa_string + '"contributorCity":'+list_entity['city']+','
                                json_sa_string= json_sa_string + '"contributorState":'+list_entity['state']+','
                                json_sa_string= json_sa_string + '"contributorZip":'+list_entity['zip_code']+','
                                json_sa_string= json_sa_string + '"contributionDate":'+date_format(entity_obj['contribution_date'])+','
                                json_sa_string= json_sa_string + '"contributionAmount":'+entity_obj['contribution_amount']+','
                                json_sa_string= json_sa_string + '"contributionAggregate":'+entity_obj['contribution_amount']+','
                                json_sa_string= json_sa_string + '"contributionPurposeDescription":'+entity_obj['purpose_description']+','
                                json_sa_string= json_sa_string + '"contributorEmployer":'+list_entity['employer']+','
                                json_sa_string= json_sa_string + '"contributorOccupation":'+list_entity['occupation']+','
                                json_sa_string= json_sa_string + '"memoCode":'+entity_obj['memo_code']+','
                                json_sa_string= json_sa_string + '"memoDescription":'+entity_obj['memo_text']+','
                                if entityforn3x_sa_data['back_ref_transaction_id'] != "" :
                                    json_sa_string= json_sa_string + '"child": {'
                                    form3x_sa_chld_list = get_f3x_SA_children_data(forn3x_sa_data['report_id'], forn3x_sa_data['cmte_id'], forn3x_sa_data['back_ref_transaction_id'] )
                                    frx_receipt_data_list = []
                                    response_inkind_out_list = []
                                    for form3x_sa_chld_data in form3x_sa_chld_list:
                                        response_dict_out = {}
                                        frx_receipt_data = {}
                                        print (form3x_sa_chld_data['report_id'])
                                        entity_id_chld_list = get_entity_sched_a_data(form3x_sa_chld_data['report_id'], form3x_sa_chld_data['cmte_id'])
                                        if not entity_id_chld_list:
                                            continue
                                        print ("we got the data")
                                        # comm_id = Committee.objects.get(committeeid=request.user.username)
                                        for entity_chld_obj in entity_id_chld_list:
                                            list_entity = get_list_entity(entity_obj['entity_id'], entity_obj['cmte_id'])
                                            if not list_entity:
                                                continue
                                            else:
                                                list_entity = list_entity[0]
                                                json_sa_string= '"transactionTypeCode":'+entity_chld_obj['transaction_type']+','
                                                json_sa_string= json_sa_string + '"transactionId":'+ entity_chld_obj['transaction_id']+','
                                                json_sa_string= json_sa_string + '"entityType":'+entity_chld_obj['entity_type']+','
                                                json_sa_string= json_sa_string + '"ontributorLastName":'+list_entity['last_name']+','
                                                json_sa_string= json_sa_string + '"contributorFirstName":'+list_entity['first_name']+','
                                                json_sa_string= json_sa_string + '"contributorMiddleName":'+list_entity['preffix']+','
                                                json_sa_string= json_sa_string + '"contributorPrefix":'+list_entity['transaction_type']+','
                                                json_sa_string= json_sa_string + '"contributorSuffix":'+list_entity['suffix']+','
                                                json_sa_string= json_sa_string + '"contributorStreet1":'+list_entity['street_1']+','
                                                json_sa_string= json_sa_string + '"contributorStreet2":'+list_entity['street_2']+','
                                                json_sa_string= json_sa_string + '"contributorCity":'+list_entity['city']+','
                                                json_sa_string= json_sa_string + '"contributorState":'+list_entity['state']+','
                                                json_sa_string= json_sa_string + '"contributorZip":'+list_entity['zip_code']+','
                                                json_sa_string= json_sa_string + '"contributionDate":'+date_format(entity_obj['contribution_date'])+','
                                                json_sa_string= json_sa_string + '"contributionAmount":'+entity_obj['contribution_amount']+','
                                                json_sa_string= json_sa_string + '"contributionAggregate":'+entity_chld_obj['contribution_amount']+','
                                                json_sa_string= json_sa_string + '"contributionPurposeDescription":'+entity_chld_obj['purpose_description']+','
                                                json_sa_string= json_sa_string + '"contributorEmployer":'+list_entity['employer']+','
                                                json_sa_string= json_sa_string + '"contributorOccupation":'+list_entity['occupation']+','
                                                json_sa_string= json_sa_string + '"memoCode":'+entity_chld_obj['memo_code']+','
                                                json_sa_string= json_sa_string + '"memoDescription":'+entity_chld_obj['memo_text']+','
                                                json_sa_string= json_sa_string + '}'
                    json_sa_string= json_sa_string + '},'
                    Json_string = form3x_header_string + form3x_data_string + json_sa_string + "}]}}"    
                    json_actual_string=ast.literal_eval(json_sa_string)

                    # import pdb;pdb.set_trace()
                    # get_list_entity(entity_id, comm_info.committeeid)
                
                    bucket = conn.get_bucket("dev-efile-repo")
                    k = Key(bucket)
                    print(k)
                    k.content_type = "application/json"
                    data_obj = {}
                    data_obj['header'] = header
                    data_obj['data'] = frx_receipt_data_list
                    k.set_contents_from_string(json.dumps(data_obj, indent=4))            
                    url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")
                    tmp_filename = '/tmp/' + comm_info.committeeid + '_f3x.json'
                    vdata = {}
                    vdata['form_type'] = "F3X"
                    vdata['committeeid'] = comm_info.committeeid
                    #json.dump(data_obj, open(tmp_filename, 'w'))
                    json.dump(json_actual_string, open(tmp_filename, 'w'))
                    vfiles = {}
                    vfiles["json_file"] = open(tmp_filename, 'rb')
                    res = requests.post("http://" + settings.DATA_RECEIVE_API_URL + "/v1/send_data" , data=vdata, files=vfiles)
                    # import ipdb; ipdb.set_trace()
                    return Response(res.text, status=status.HTTP_200_OK)
                    
                else:
                    return Response({"FEC Error 007":"This user does not have a submitted CommInfo object"}, status=status.HTTP_400_BAD_REQUEST)
    except CommitteeInfo.DoesNotExist:
       return Response({"FEC Error 009":"An unexpected error occurred while processing your request"}, status=status.HTTP_400_BAD_REQUEST)

"""
******************************************************************************************************************************
END  - CORE APP
******************************************************************************************************************************
"""

"""
******************************************************************************************************************************
Generate In kind Receipt and out Kind transaction Json file API - CORE APP - SPRINT 12 - FNE 928 - BY Yeswanth Tella
******************************************************************************************************************************

"""
def get_entity_sched_a_data(report_id, cmte_id, transaction_id=None):
    try:
        # GET all rows from schedA table
        forms_obj = []
        if not transaction_id:
            query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date
                        FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""
        else:
            query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date
                        FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""
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
                            if not d[i]:
                                d[i] = ''
                # forms_obj.append(data_row)
        if forms_obj is None:
            pass
            #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))   
        return forms_obj
    except Exception:
        raise

def get_entity_sched_b_data(report_id, cmte_id, transaction_id=None):
    try:
        # GET all rows from schedB table
        forms_obj = []
        if not transaction_id:
            query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, expenditure_date, expenditure_amount, expenditure_purpose, memo_code, memo_text, election_code, election_other_description, create_date, category_code
                        FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""
        else:
            query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, expenditure_date, expenditure_amount, expenditure_purpose, memo_code, memo_text, election_code, election_other_description, create_date, category_code
                        FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""
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
                            if not d[i]:
                                d[i] = ''
                # forms_obj.append(data_row)
        if forms_obj is None:
            pass
            #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))   
        return forms_obj
    except Exception:
        raise



@api_view(["POST"])
def create_f3x_json_file(request):
    #creating a JSON file so that it is handy for all the public API's   
    try:
        report_id = request.POST.get('report_id')
        #import ipdb;ipdb.set_trace()
        #comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username, is_submitted=True).last()
        #comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username)
        comm_info = True
        if comm_info:
            committeeid = request.user.username
            # serializer = CommitteeInfoSerializer(comm_info)
            comm_info_obj = get_committee_mater_values(committeeid)
            header = {
                "version":"8.3",
                "softwareName":"ABC Inc",
                "softwareVersion":"1.02 Beta",
                "additionalInfomation":"Any other useful information"
            }
            f_3x_list = get_f3x_report_data(committeeid, report_id)
            report_info = get_list_report(report_id, committeeid)
            response_inkind_receipt_list = []
            response_inkind_out_list = []
            response_dict_receipt = {}
            for f3_i in f_3x_list:
                print (f3_i['report_id'])
                entity_id_list = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'])
                if not entity_id_list:
                    continue
                print ("we got the data")
                #import ipdb;ipdb.set_trace()
                # comm_id = Committee.objects.get(committeeid=request.user.username)
                for entity_obj in entity_id_list:
                    response_dict_out = {}
                    response_dict_receipt = {}
                    list_entity = get_list_entity(entity_obj['entity_id'], entity_obj['cmte_id'])
                    if not list_entity:
                        continue
                    else:
                        list_entity = list_entity[0]
                    response_dict_receipt['transactionTypeCode'] = entity_obj['transaction_type']
                    response_dict_receipt['transactionId'] = entity_obj['transaction_id']
                    response_dict_receipt['backReferenceTransactionIdNumber'] = entity_obj['back_ref_transaction_id']
                    response_dict_receipt['backReferenceScheduleName'] = entity_obj['back_ref_sched_name']
                    response_dict_receipt['entityType'] = list_entity['entity_type']

                    response_dict_receipt['contributorLastName'] = list_entity['last_name']
                    response_dict_receipt['contributorFirstName'] = list_entity['first_name']
                    response_dict_receipt['contributorMiddleName'] = list_entity['middle_name']
                    response_dict_receipt['contributorPrefix'] = list_entity['preffix']
                    response_dict_receipt['contributorSuffix'] = list_entity['suffix']
                    response_dict_receipt['contributorStreet1 '] = list_entity['street_1']
                    response_dict_receipt['contributorStreet2'] = list_entity['street_2']
                    response_dict_receipt['contributorCity'] = list_entity['city']
                    response_dict_receipt['contributorState'] = list_entity['state']
                    response_dict_receipt['contributorZip'] = list_entity['zip_code']
                    response_dict_receipt['contributionDate'] = entity_obj['contribution_date'].replace('-','')
                    response_dict_receipt['contributionAmount'] = round(entity_obj['contribution_amount'],2)
                    response_dict_receipt['contributionAggregate'] = round(entity_obj['contribution_amount'],2)
                    response_dict_receipt['contributionPurposeDescription'] = entity_obj['purpose_description']
                    response_dict_receipt['contributorEmployer'] = list_entity['employer']
                    response_dict_receipt['contributorOccupation'] = list_entity['occupation']
                    response_dict_receipt['memoCode'] = entity_obj['memo_code']
                    response_dict_receipt['memoDescription'] = entity_obj['memo_text']


                    
                    entity_id_child_list = get_entity_sched_b_data(f3_i['report_id'], f3_i['cmte_id'], entity_obj['transaction_id'])

                    if not entity_id_child_list:
                        response_inkind_receipt_list.append(response_dict_receipt)
                        continue
                    for entity_child_obj in entity_id_child_list:
                        response_dict_out = {}
                        list_child_entity = get_list_entity(entity_child_obj['entity_id'], entity_child_obj['cmte_id'])
                        if not list_child_entity:
                            continue
                        else:
                            list_child_entity = list_child_entity[0]
                        response_dict_receipt['child'] = []
                        response_dict_out['transactionTypeCode'] = entity_child_obj['transaction_type']
                        response_dict_out['transactionId'] = entity_child_obj['transaction_id']
                        response_dict_out['backReferenceTransactionIdNumber'] = entity_child_obj['back_ref_transaction_id']
                        response_dict_out['backReferenceScheduleName'] = entity_child_obj['back_ref_sched_name']
                        response_dict_out['entityType'] = list_child_entity['entity_type']

                        response_dict_out['payeeLastName'] = list_child_entity['last_name']
                        response_dict_out['payeeFirstName'] = list_child_entity['first_name']
                        response_dict_out['payeeMiddleName'] = list_child_entity['middle_name']
                        response_dict_out['payeePrefix'] = list_child_entity['preffix']
                        response_dict_out['payeeSuffix'] = list_child_entity['suffix']
                        response_dict_out['payeeStreet1'] = list_child_entity['street_1']
                        response_dict_out['payeeStreet2'] = list_child_entity['street_2']
                        response_dict_out['payeeCity'] = list_child_entity['city']
                        response_dict_out['payeeState'] = list_child_entity['state']
                        response_dict_out['payeezip'] = list_child_entity['zip_code']
                        response_dict_out['expenditureDate'] = entity_child_obj['expenditure_date'].replace('-','')
                        response_dict_out['expenditureAmount'] = round(entity_child_obj['expenditure_amount'],2)
                        response_dict_out['expenditurePurposeDescription'] = entity_child_obj['expenditure_purpose']
                        response_dict_out['categoryCode'] = '15G'
                        response_dict_out['memoCode'] = entity_child_obj['memo_code']
                        response_dict_out['memoDescription'] = entity_child_obj['memo_text']
                        response_dict_receipt['child'].append(response_dict_out)


                    response_inkind_receipt_list.append(response_dict_receipt)

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
            data_obj['data']['summary'] = json.loads(get_summary_dict(f_3x_list[0]))
            data_obj['data']['Schedule'] = {'SA': [],}
            data_obj['data']['Schedule']['SA'] = response_inkind_receipt_list
            # data_obj['data']['Schedule']['SB'] = response_inkind_out_list
            #import ipdb;ipdb.set_trace()
            bucket = conn.get_bucket("dev-efile-repo")
            k = Key(bucket)
            print(k)
            k.content_type = "application/json"
            k.set_contents_from_string(json.dumps(data_obj, indent=4))            
            url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")
            tmp_filename = '/tmp/' + committeeid + str(report_id)+'_.json'
            vdata = {}
            #data_obj['data']['form_type'] = "F3X"
            print('tmp_filename')
            json.dump(data_obj, open(tmp_filename, 'w'))  
            vfiles = {}
            vfiles["json_file"] = open(tmp_filename, 'rb')
            #print('tmp_filename')
            #import ipdb; ipdb.set_trace()
            print("vfiles",vfiles)
            print ("tmp_filename= ", tmp_filename)
            res = requests.post("http://" + settings.DATA_RECEIVE_API_URL + "/v1/send_data" , data=vdata, files=vfiles)
            return Response(res.text, status=status.HTTP_200_OK)
            
        else:
            return Response({"FEC Error 007":"This user does not have a submitted CommInfo object"}, status=status.HTTP_400_BAD_REQUEST)
            
    except CommitteeInfo.DoesNotExist:
        return Response({"FEC Error 009":"An unexpected error occurred while processing your request"}, status=status.HTTP_400_BAD_REQUEST)


"""
******************************************************************************************************************************
END  - Inkind receipt and inkind out - CORE APP
******************************************************************************************************************************
"""

"""
******************************************************************************************************************************
Generate Partnership Receipet and Partnership Memo Json file API - CORE APP - SPRINT 12 - FNE -765 - BY YESWANTH TELLA
******************************************************************************************************************************
"""

@api_view(["POST"])
def create_f3x_partner_json_file(request):
    #creating a JSON file so that it is handy for all the public API's   
    try:
        report_id = request.POST.get('report_id')
        comm_info = True
        if comm_info:
            committeeid = request.user.username
            comm_info_obj = get_committee_mater_values(committeeid)
            header = {    
                "version":"8.3",
                "softwareName":"ABC Inc",
                "softwareVersion":"1.02 Beta",
                "additionalInfomation":"Any other useful information"
            }
            f_3x_list = get_f3x_report_data(committeeid, report_id)
            report_info = get_list_report(report_id, committeeid)
            response_inkind_receipt_list = []
            response_inkind_out_list = []
            response_dict_receipt = {}
            for f3_i in f_3x_list:
                print (f3_i['report_id'])
                entity_id_list = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'])
                if not entity_id_list:
                    continue
                print ("we got the data")
                # comm_id = Committee.objects.get(committeeid=request.user.username)
                for entity_obj in entity_id_list:
                    response_dict_out = {}
                    response_dict_receipt = {}
                    list_entity = get_list_entity(entity_obj['entity_id'], entity_obj['cmte_id'])
                    if not list_entity:
                        continue
                    else:
                         list_entity = list_entity[0]
                    response_dict_receipt['transactionTypeCode'] = entity_obj['transaction_type']
                    response_dict_receipt['transactionId'] = entity_obj['transaction_id']
                    response_dict_receipt['backReferenceTransactionIdNumber'] = entity_obj['back_ref_transaction_id']
                    response_dict_receipt['backReferenceScheduleName'] = entity_obj['back_ref_sched_name']
                    response_dict_receipt['entityType'] = list_entity['entity_type']

                    response_dict_receipt['contributorOrganizationName']=list_entity['entity_name']
                    response_dict_receipt['contributorStreet1'] = list_entity['street_1']
                    response_dict_receipt['contributorStreet2'] = list_entity['street_2']
                    response_dict_receipt['contributorCity'] = list_entity['city']
                    response_dict_receipt['contributorState'] = list_entity['state']
                    response_dict_receipt['contributorZip'] = list_entity['zip_code']
                    response_dict_receipt['contributionDate'] = entity_obj['contribution_date'].replace('-','')
                    response_dict_receipt['contributionAmount'] = "%.2f" % round(entity_obj['contribution_amount'],2)
                    response_dict_receipt['contributionAggregate'] = "%.2f" % round(entity_obj['contribution_amount'],2)
                    response_dict_receipt['contributionPurposeDescription'] = entity_obj['purpose_description']
                    response_dict_receipt['memoCode'] = entity_obj['memo_code']
                    response_dict_receipt['memoDescription'] = entity_obj['memo_text']
                    

                    #response_dict_receipt['child'] = []

                    entity_id_child_list = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'], entity_obj['transaction_id'])

                    if not entity_id_child_list:
                        response_inkind_receipt_list.append(response_dict_receipt)
                        continue
                    for entity_child_obj in entity_id_child_list:
                        response_dict_out = {}
                        list_child_entity = get_list_entity(entity_child_obj['entity_id'], entity_child_obj['cmte_id'])
                        if not list_child_entity:
                            continue
                        else:
                            list_child_entity = list_child_entity[0]
                        response_dict_receipt['child'] = []
                        response_dict_out['transactionTypeCode'] = entity_child_obj['transaction_type']
                        response_dict_out['transactionId'] = entity_child_obj['transaction_id']
                        response_dict_out['backReferenceTransactionIdNumber'] = entity_child_obj['back_ref_transaction_id']
                        response_dict_out['backReferenceScheduleName'] = entity_child_obj['back_ref_sched_name']
                        response_dict_out['entityType'] = list_child_entity['entity_type']
                       

                        response_dict_out['contributorLastName'] = list_child_entity['last_name']
                        response_dict_out['contributorFirstName'] = list_child_entity['first_name']
                        response_dict_out['contributorMiddleName'] = list_child_entity['middle_name']
                        response_dict_out['contributorPrefix'] = list_child_entity['preffix']
                        response_dict_out['contributorSuffix'] = list_child_entity['suffix']
                        response_dict_out['contributorStreet1 '] = list_child_entity['street_1']
                        response_dict_out['contributorStreet2'] = list_child_entity['street_2']
                        response_dict_out['contributorCity'] = list_child_entity['city']
                        response_dict_out['contributorState'] = list_child_entity['state']
                        response_dict_out['contributorZip'] = list_child_entity['zip_code']
                        response_dict_out['contributionDate'] = entity_child_obj['contribution_date'].replace('-','')
                        response_dict_out['contributionAmount'] = "%.2f" % round(entity_child_obj['contribution_amount'],2)
                        response_dict_out['contributionAggregate'] = "%.2f" % round(entity_child_obj['contribution_amount'],2)
                        response_dict_out['contributionPurposeDescription'] = entity_child_obj['purpose_description']
                        response_dict_out['contributorEmployer'] = list_child_entity['employer']
                        response_dict_out['contributorOccupation'] = list_child_entity['occupation']
                        response_dict_out['memoCode'] = entity_child_obj['memo_code']
                        response_dict_out['memoDescription'] = entity_child_obj['memo_text']
                        response_dict_receipt['child'].append(response_dict_out)
                    
                    response_inkind_receipt_list.append(response_dict_receipt)

            # import ipdb;ipdb.set_trace()
            # get_list_entity(entity_id, comm_info.committeeid)

            data_obj = {}
            data_obj['header'] = header
            comm_info_obj['changeOfAddress'] = f3_i['cmte_addr_chg_flag'] if f3_i['cmte_addr_chg_flag'] else ''
            comm_info_obj['amendmentIndicator'] = f3_i['amend_ind']
            comm_info_obj['reportCode'] = f3_i['report_type']
            comm_info_obj['electionState'] = f3_i['state_of_election'] if f3_i['state_of_election'] else ''
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
            comm_info_obj['amendmentNumber'] = report_info[0]['amend_number']
            data_obj['data'] = comm_info_obj
            data_obj['data']['formType'] = "F3X"
            data_obj['data']['summary'] = json.loads(get_summary_dict(f_3x_list[0]))
            data_obj['data']['Schedule'] = {'SA': []}
            data_obj['data']['Schedule']['SA'] = response_inkind_receipt_list 
            # data_obj['data']['Schedule']['SA'] = response_inkind_out_list
            bucket = conn.get_bucket("dev-efile-repo")
            k = Key(bucket)
            print(k)
            k.content_type = "application/json"
            k.set_contents_from_string(json.dumps(data_obj, indent=4))            
            url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")
            tmp_filename = '/tmp/' + committeeid + '_f3x_PARTNER.json'
            vdata = {}
            # vdata['form_type'] = "F3X"
            # vdata['committeeid'] = comm_info.committeeid
            json.dump(data_obj, open(tmp_filename, 'w'))
            vfiles = {}
            vfiles["json_file"] = open(tmp_filename, 'rb')
            print(vfiles)
            res = requests.post("https://" + settings.DATA_RECEIVE_API_URL + "/v1/send_data" , data=data_obj, files=vfiles)
            # import ipdb; ipdb.set_trace()
            return Response(res.text, status=status.HTTP_200_OK)
            
        else:
            return Response({"FEC Error 007":"This user does not have a submitted CommInfo object"}, status=status.HTTP_400_BAD_REQUEST)
            
    except CommitteeInfo.DoesNotExist:
        return Response({"FEC Error 009":"An unexpected error occurred while processing your request"}, status=status.HTTP_400_BAD_REQUEST)


"""
******************************************************************************************************************************
END  - Partnership Memo Json - CORE APP
******************************************************************************************************************************
"""

"""

**********************************************************************************************************************************************
Generate Returned or Bonused Receipt  Json file API - CORE APP - SPRINT 12 - FNE -920 - BY YESWANTH TELLA
***********************************************************************************************************************************************
"""

# def get_entity_sched_a_data(report_id, cmte_id):
#     try:
#         # GET all rows from schedA table
#         forms_obj = []
#         query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date
#                          FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""
#         #AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""
#         with connection.cursor() as cursor:
#             cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [report_id, cmte_id])
#             for row in cursor.fetchall():
#                 #forms_obj.append(data_row)
#                 data_row = list(row)
#                 #schedA_list = data_row[0]
#                 forms_obj = data_row[0]
#                 for d in forms_obj:
#                     for i in d:
#                         if not d[i]:
#                             d[i] = ''
#         if forms_obj is None:
#             pass
#             #raise NoOPError('The committeeid ID: {} does not exist or is deleted'.format(cmte_id))   
#         return forms_obj
#     except Exception:
#         raise


@api_view(["POST"])
def create_f3x_returned_bounced_json_file(request):
    #creating a JSON file so that it is handy for all the public API's   
    try:
        report_id = request.POST.get('report_id')
        comm_info = True
        if comm_info:
            committeeid = request.user.username
            comm_info_obj = get_committee_mater_values(committeeid)
            header = {    
                "version":"8.3",
                "softwareName":"ABC Inc",
                "softwareVersion":"1.02 Beta",
                "additionalInfomation":"Any other useful information"
            }
            f_3x_list = get_f3x_report_data(committeeid, report_id)
            report_info = get_list_report(report_id, committeeid)
            #response_inkind_receipt_list = []
            response_inkind_out_list = []
            for f3_i in f_3x_list:
                print (f3_i['report_id'])

                entity_id_list = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'])
                if not entity_id_list:
                    continue
                print ("we got the data")
                # comm_id = Committee.objects.get(committeeid=request.user.username)
                for entity_obj in entity_id_list:
                    response_dict_out = {}
                    response_dict_receipt = {}
                    list_entity = get_list_entity(entity_obj['entity_id'], entity_obj['cmte_id'])
                    if not list_entity:
                        continue
                    else:
                         list_entity = list_entity[0]
                    response_dict_out['transactionTypeCode'] = entity_obj['transaction_type']
                    response_dict_out['transactionId'] = entity_obj['transaction_id']
                    response_dict_out['backReferenceTransactionIdNumber'] = entity_obj['back_ref_transaction_id']
                    response_dict_out['backReferenceScheduleName'] = entity_obj['back_ref_sched_name']
                    response_dict_out['entityType'] = list_entity['entity_type']
                    

                    response_dict_out['contributorLastName'] = list_entity['last_name']
                    response_dict_out['contributorFirstName'] = list_entity['first_name']
                    response_dict_out['contributorMiddleName'] = list_entity['middle_name']
                    response_dict_out['contributorPrefix'] = list_entity['preffix']
                    response_dict_out['contributorSuffix'] = list_entity['suffix']
                    response_dict_out['contributorStreet1 '] = list_entity['street_1']
                    response_dict_out['contributorStreet2'] = list_entity['street_2']
                    response_dict_out['contributorCity'] = list_entity['city']
                    response_dict_out['contributorState'] = list_entity['state']
                    response_dict_out['contributorZip'] = list_entity['zip_code']
                    response_dict_out['contributionDate'] = entity_obj['contribution_date'].replace('-','')
                    response_dict_out['contributionAmount'] = "%.2f" % round(entity_obj['contribution_amount'],2)
                    response_dict_out['contributionAggregate'] = "%.2f" % round(entity_obj['contribution_amount'],2)
                    response_dict_out['contributionPurposeDescription'] = entity_obj['purpose_description']
                    response_dict_out['contributorEmployer'] = list_entity['employer']
                    response_dict_out['contributorOccupation'] = list_entity['occupation']
                    response_dict_out['memoCode'] = entity_obj['memo_code']
                    response_dict_out['memoDescription'] = entity_obj['memo_text']

                    response_inkind_out_list.append(response_dict_out)
                    #response_inkind_receipt_list.append(response_dict_receipt)

            # import ipdb;ipdb.set_trace()
            # get_list_entity(entity_id, comm_info.committeeid)

            data_obj = {}
            data_obj['header'] = header
            comm_info_obj['changeOfAddress'] = f3_i['cmte_addr_chg_flag'] if f3_i['cmte_addr_chg_flag'] else ''
            comm_info_obj['amendmentIndicator'] = f3_i['amend_ind']
            comm_info_obj['reportCode'] = f3_i['report_type']
            comm_info_obj['electionState'] = f3_i['state_of_election'] if f3_i['state_of_election'] else ''
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
            comm_info_obj['amendmentNumber'] = report_info[0]['amend_number']
            data_obj['data'] = comm_info_obj
            data_obj['data']['formType'] = "F3X"
            data_obj['data']['summary'] = json.loads(get_summary_dict(f_3x_list[0]))
            data_obj['data']['Schedule'] = {'SA': []}
            data_obj['data']['Schedule']['SA'] = response_inkind_out_list
            # data_obj['data']['Schedule']['SA'] = response_inkind_out_list
            bucket = conn.get_bucket("dev-efile-repo")
            k = Key(bucket)
            print(k)
            k.content_type = "application/json"
            k.set_contents_from_string(json.dumps(data_obj, indent=4))            
            url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")
            tmp_filename = '/tmp/' + committeeid + '_f3x_RETURNED.json'
            vdata = {}
            # vdata['form_type'] = "F3X"
            # vdata['committeeid'] = comm_info.committeeid
            json.dump(data_obj, open(tmp_filename, 'w'))
            vfiles = {}
            vfiles["json_file"] = open(tmp_filename, 'rb')
            print(vfiles)
            res = requests.post("https://" + settings.DATA_RECEIVE_API_URL + "/v1/send_data" , data=vdata, files=vfiles)
            # import ipdb; ipdb.set_trace()
            return Response(res.text, status=status.HTTP_200_OK)
            
        else:
            return Response({"FEC Error 007":"This user does not have a submitted CommInfo object"}, status=status.HTTP_400_BAD_REQUEST)
            
    except CommitteeInfo.DoesNotExist:
        return Response({"FEC Error 009":"An unexpected error occurred while processing your request"}, status=status.HTTP_400_BAD_REQUEST)



"""
******************************************************************************************************************************
END  - Returned or Bonused Receipt  Json file API - CORE APP
******************************************************************************************************************************
"""

"""

**********************************************************************************************************************************************
FNE-909 REATTRIBUTION AND REATTRIBUTION MEMO SPRINT 12 YESWANTH TELLA
***********************************************************************************************************************************************

"""

@api_view(["POST"])
def create_f3x_reattribution_json_file(request):
    #creating a JSON file so that it is handy for all the public API's   
    try:
        report_id = request.POST.get('report_id')
        comm_info = True
        if comm_info:
            committeeid = request.user.username
            comm_info_obj = get_committee_mater_values(committeeid)
            header = {    
                "version":"8.3",
                "softwareName":"ABC Inc",
                "softwareVersion":"1.02 Beta",
                "additionalInfomation":"Any other useful information"
            }
            f_3x_list = get_f3x_report_data(committeeid, report_id)
            report_info = get_list_report(report_id, committeeid)
            response_inkind_receipt_list = []
            response_inkind_out_list = []
            response_dict_receipt = {}
            for f3_i in f_3x_list:
                print (f3_i['report_id'])
                entity_id_list = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'])
                if not entity_id_list:
                    continue
                print ("we got the data")
                # comm_id = Committee.objects.get(committeeid=request.user.username)
                for entity_obj in entity_id_list:
                    response_dict_out = {}
                    response_dict_receipt = {}
                    list_entity = get_list_entity(entity_obj['entity_id'], entity_obj['cmte_id'])
                    if not list_entity:
                        continue
                    else:
                         list_entity = list_entity[0]
                    response_dict_receipt['transactionTypeCode'] = entity_obj['transaction_type']
                    response_dict_receipt['transactionId'] = entity_obj['transaction_id']
                    response_dict_receipt['backReferenceTransactionIdNumber'] = entity_obj['back_ref_transaction_id']
                    response_dict_receipt['backReferenceScheduleName'] = entity_obj['back_ref_sched_name']
                    response_dict_receipt['entityType'] = list_entity['entity_type']

                    response_dict_receipt['contributorLastName'] = list_entity['last_name']
                    response_dict_receipt['contributorFirstName'] = list_entity['first_name']
                    response_dict_receipt['contributorMiddleName'] = list_entity['middle_name']
                    response_dict_receipt['contributorPrefix'] = list_entity['preffix']
                    response_dict_receipt['contributorSuffix'] = list_entity['suffix']
                    response_dict_receipt['contributorStreet1'] = list_entity['street_1']
                    response_dict_receipt['contributorStreet2'] = list_entity['street_2']
                    response_dict_receipt['contributorCity'] = list_entity['city']
                    response_dict_receipt['contributorState'] = list_entity['state']
                    response_dict_receipt['contributorZip'] = list_entity['zip_code']
                    response_dict_receipt['contributionDate'] = entity_obj['contribution_date'].replace('-','')
                    response_dict_receipt['contributionAmount'] = "%.2f" % round(entity_obj['contribution_amount'],2)
                    response_dict_receipt['contributionAggregate'] = "%.2f" % round(entity_obj['contribution_amount'],2)
                    response_dict_receipt['contributionPurposeDescription'] = entity_obj['purpose_description']
                    response_dict_receipt['contributorEmployer'] = list_entity['employer']
                    response_dict_receipt['contributorOccupation'] = list_entity['occupation']
                    response_dict_receipt['memoCode'] = entity_obj['memo_code']
                    response_dict_receipt['memoDescription'] = entity_obj['memo_text']


                    #response_dict_receipt['child'] = []
                    entity_id_child_list = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'], entity_obj['transaction_id'])

                    if not entity_id_child_list:
                        response_inkind_receipt_list.append(response_dict_receipt)
                        continue
                    for entity_child_obj in entity_id_child_list:
                        response_dict_out = {}

                        list_child_entity = get_list_entity(entity_child_obj['entity_id'], entity_child_obj['cmte_id'])
                        if not list_child_entity:
                            continue
                        else:
                            list_child_entity = list_child_entity[0]
                        response_dict_receipt['child'] = []
                        response_dict_out['transactionTypeCode'] = entity_child_obj['transaction_type']
                        response_dict_out['transactionId'] = entity_child_obj['transaction_id']
                        response_dict_out['backReferenceTransactionIdNumber'] = entity_child_obj['back_ref_transaction_id']
                        response_dict_out['backReferenceScheduleName'] = entity_child_obj['back_ref_sched_name']
                        response_dict_out['entityType'] = list_child_entity['entity_type']
                       

                        response_dict_out['contributorLastName'] = list_child_entity['last_name']
                        response_dict_out['contributorFirstName'] = list_child_entity['first_name']
                        response_dict_out['contributorMiddleName'] = list_child_entity['middle_name']
                        response_dict_out['contributorPrefix'] = list_child_entity['preffix']
                        response_dict_out['contributorSuffix'] = list_child_entity['suffix']
                        response_dict_out['contributorStreet1 '] = list_child_entity['street_1']
                        response_dict_out['contributorStreet2'] = list_child_entity['street_2']
                        response_dict_out['contributorCity'] = list_child_entity['city']
                        response_dict_out['contributorState'] = list_child_entity['state']
                        response_dict_out['contributorZip'] = list_child_entity['zip_code']
                        response_dict_out['contributionDate'] = entity_child_obj['contribution_date'].replace('-','')
                        response_dict_out['contributionAmount'] = "%.2f" % round(entity_child_obj['contribution_amount'],2)
                        response_dict_out['contributionAggregate'] = "%.2f" % round(entity_child_obj['contribution_amount'],2)
                        response_dict_out['contributionPurposeDescription'] = entity_child_obj['purpose_description']
                        response_dict_out['contributorEmployer'] = list_child_entity['employer']
                        response_dict_out['contributorOccupation'] = list_child_entity['occupation']
                        response_dict_out['memoCode'] = entity_child_obj['memo_code']
                        response_dict_out['memoDescription'] =entity_child_obj['memo_text']
                        response_dict_receipt['child'].append(response_dict_out)
                    
                    response_inkind_receipt_list.append(response_dict_receipt)

            # import ipdb;ipdb.set_trace()
            # get_list_entity(entity_id, comm_info.committeeid)

            data_obj = {}
            data_obj['header'] = header
            comm_info_obj['changeOfAddress'] = f3_i['cmte_addr_chg_flag'] if f3_i['cmte_addr_chg_flag'] else ''
            comm_info_obj['amendmentIndicator'] = f3_i['amend_ind']
            comm_info_obj['reportCode'] = f3_i['report_type']
            comm_info_obj['amendmentNumber'] = report_info[0]['amend_number']
            comm_info_obj['electionState'] = f3_i['state_of_election'] if f3_i['state_of_election'] else ''
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
            data_obj['data']['summary'] = json.loads(get_summary_dict(f_3x_list[0]))
            data_obj['data']['Schedule'] = {'SA': []}
            data_obj['data']['Schedule']['SA'] = response_inkind_receipt_list
            # data_obj['data']['Schedule']['SA'] = response_inkind_out_list
            bucket = conn.get_bucket("dev-efile-repo")
            k = Key(bucket)
            print(k)
            k.content_type = "application/json"
            k.set_contents_from_string(json.dumps(data_obj, indent=4))            
            url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")
            tmp_filename = '/tmp/' + committeeid + '_f3x_REATTRIBUTION.json'
            vdata = {}
            # vdata['form_type'] = "F3X"
            # vdata['committeeid'] = comm_info.committeeid
            json.dump(data_obj, open(tmp_filename, 'w'))
            vfiles = {}
            vfiles["json_file"] = open(tmp_filename, 'rb')
            print(vfiles)
            res = requests.post("https://" + settings.DATA_RECEIVE_API_URL + "/v1/send_data" , data=vdata, files=vfiles)
            # import ipdb; ipdb.set_trace()
            return Response(res.text, status=status.HTTP_200_OK)
            
        else:
            return Response({"FEC Error 007":"This user does not have a submitted CommInfo object"}, status=status.HTTP_400_BAD_REQUEST)
            
    except CommitteeInfo.DoesNotExist:
        return Response({"FEC Error 009":"An unexpected error occurred while processing your request"}, status=status.HTTP_400_BAD_REQUEST)


"""

********************************************************************************************************************************
END  - REATTRIBUTION AND REATTRIBUTION MEMO Json - CORE APP
********************************************************************************************************************************
"""

"""
**************************************************************************************************************************************
Generate In kind Bitcoin Receipt and Inkind Bitcoin  transaction Json file API - CORE APP - SPRINT 12 - FNE 791 - BY Yeswanth Tella
**************************************************************************************************************************************

"""
@api_view(["POST"])
def create_inkind_bitcoin_f3x_json_file(request):
    #creating a JSON file so that it is handy for all the public API's   
    try:
        report_id = request.POST.get('report_id')
        #import ipdb;ipdb.set_trace()
        #comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username, is_submitted=True).last()
        #comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username)
        comm_info = True
        if comm_info:
            committeeid = request.user.username
            # serializer = CommitteeInfoSerializer(comm_info)
            comm_info_obj = get_committee_mater_values(committeeid)
            header = {
                "version":"8.3",
                "softwareName":"ABC Inc",
                "softwareVersion":"1.02 Beta",
                "additionalInfomation":"Any other useful information"
            }
            f_3x_list = get_f3x_report_data(committeeid, report_id)
            report_info = get_list_report(report_id, committeeid)
            response_inkind_receipt_list = []
            response_inkind_out_list = []
            response_dict_receipt = {}
            for f3_i in f_3x_list:
                print (f3_i['report_id'])
                entity_id_list = get_entity_sched_a_data(f3_i['report_id'], f3_i['cmte_id'])
                if not entity_id_list:
                    continue
                print ("we got the data")
                #import ipdb;ipdb.set_trace()
                # comm_id = Committee.objects.get(committeeid=request.user.username)
                for entity_obj in entity_id_list:
                    response_dict_out = {}
                    response_dict_receipt = {}
                    list_entity = get_list_entity(entity_obj['entity_id'], entity_obj['cmte_id'])
                    if not list_entity:
                        continue
                    else:
                        list_entity = list_entity[0]
                    response_dict_receipt['transactionTypeCode'] = entity_obj['transaction_type']
                    response_dict_receipt['transactionId'] = entity_obj['transaction_id']
                    response_dict_receipt['backReferenceTransactionIdNumber'] = entity_obj['back_ref_transaction_id']
                    response_dict_receipt['backReferenceScheduleName'] = entity_obj['back_ref_sched_name']
                    response_dict_receipt['entityType'] = list_entity['entity_type']

                    response_dict_receipt['contributorLastName'] = list_entity['last_name']
                    response_dict_receipt['contributorFirstName'] = list_entity['first_name']
                    response_dict_receipt['contributorMiddleName'] = list_entity['middle_name']
                    response_dict_receipt['contributorPrefix'] = list_entity['preffix']
                    response_dict_receipt['contributorSuffix'] = list_entity['suffix']
                    response_dict_receipt['contributorStreet1 '] = list_entity['street_1']
                    response_dict_receipt['contributorStreet2'] = list_entity['street_2']
                    response_dict_receipt['contributorCity'] = list_entity['city']
                    response_dict_receipt['contributorState'] = list_entity['state']
                    response_dict_receipt['contributorZip'] = list_entity['zip_code']
                    response_dict_receipt['contributionDate'] = entity_obj['contribution_date'].replace('-','')
                    response_dict_receipt['contributionAmount'] = round(entity_obj['contribution_amount'],2)
                    response_dict_receipt['contributionAggregate'] = round(entity_obj['contribution_amount'],2)
                    response_dict_receipt['contributionPurposeDescription'] = entity_obj['purpose_description']
                    response_dict_receipt['contributorEmployer'] = list_entity['employer']
                    response_dict_receipt['contributorOccupation'] = list_entity['occupation']
                    response_dict_receipt['memoCode'] = entity_obj['memo_code']
                    response_dict_receipt['memoDescription'] = entity_obj['memo_text']


                    
                    entity_id_child_list = get_entity_sched_b_data(f3_i['report_id'], f3_i['cmte_id'], entity_obj['transaction_id'])

                    if not entity_id_child_list:
                        response_inkind_receipt_list.append(response_dict_receipt)
                        continue
                    for entity_child_obj in entity_id_child_list:
                        response_dict_out = {}
                        list_child_entity = get_list_entity(entity_child_obj['entity_id'], entity_child_obj['cmte_id'])
                        if not list_child_entity:
                            continue
                        else:
                            list_child_entity = list_child_entity[0]
                        response_dict_receipt['child'] = []
                        response_dict_out['transactionTypeCode'] = entity_child_obj['transaction_type']
                        response_dict_out['transactionId'] = entity_child_obj['transaction_id']
                        response_dict_out['backReferenceTransactionIdNumber'] = entity_child_obj['back_ref_transaction_id']
                        response_dict_out['backReferenceScheduleName'] = entity_child_obj['back_ref_sched_name']
                        response_dict_out['entityType'] = list_child_entity['entity_type']

                        response_dict_out['payeeLastName'] = list_child_entity['last_name']
                        response_dict_out['payeeFirstName'] = list_child_entity['first_name']
                        response_dict_out['payeeMiddleName'] = list_child_entity['middle_name']
                        response_dict_out['payeePrefix'] = list_child_entity['preffix']
                        response_dict_out['payeeSuffix'] = list_child_entity['suffix']
                        response_dict_out['payeeStreet1'] = list_child_entity['street_1']
                        response_dict_out['payeeStreet2'] = list_child_entity['street_2']
                        response_dict_out['payeeCity'] = list_child_entity['city']
                        response_dict_out['payeeState'] = list_child_entity['state']
                        response_dict_out['payeezip'] = list_child_entity['zip_code']
                        response_dict_out['expenditureDate'] = entity_child_obj['expenditure_date'].replace('-','')
                        response_dict_out['expenditureAmount'] = round(entity_child_obj['expenditure_amount'],2)
                        response_dict_out['expenditurePurposeDescription'] = entity_child_obj['expenditure_purpose']
                        response_dict_out['categoryCode'] = '15G'
                        response_dict_out['memoCode'] = entity_child_obj['memo_code']
                        response_dict_out['memoDescription'] = entity_child_obj['memo_text']
                        response_dict_receipt['child'].append(response_dict_out)


                    response_inkind_receipt_list.append(response_dict_receipt)

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
            data_obj['data']['summary'] = json.loads(get_summary_dict(f_3x_list[0]))
            data_obj['data']['Schedule'] = {'SA': [],}
            data_obj['data']['Schedule']['SA'] = response_inkind_receipt_list
            # data_obj['data']['Schedule']['SB'] = response_inkind_out_list
            #import ipdb;ipdb.set_trace()
            bucket = conn.get_bucket("dev-efile-repo")
            k = Key(bucket)
            print(k)
            k.content_type = "application/json"
            k.set_contents_from_string(json.dumps(data_obj, indent=4))            
            url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")
            tmp_filename = '/tmp/' + committeeid + str(report_id)+'_.json'
            vdata = {}
            #data_obj['data']['form_type'] = "F3X"
            print('tmp_filename')
            json.dump(data_obj, open(tmp_filename, 'w'))  
            vfiles = {}
            vfiles["json_file"] = open(tmp_filename, 'rb')
            #print('tmp_filename')
            #import ipdb; ipdb.set_trace()
            print("vfiles",vfiles)
            print ("tmp_filename= ", tmp_filename)
            res = requests.post("http://" + settings.DATA_RECEIVE_API_URL + "/v1/send_data" , data=vdata, files=vfiles)
            return Response(res.text, status=status.HTTP_200_OK)
            
        else:
            return Response({"FEC Error 007":"This user does not have a submitted CommInfo object"}, status=status.HTTP_400_BAD_REQUEST)
            
    except CommitteeInfo.DoesNotExist:
        return Response({"FEC Error 009":"An unexpected error occurred while processing your request"}, status=status.HTTP_400_BAD_REQUEST)

"""

******************************************************************************************************************************************
"""
@api_view(['GET'])
def get_report_info(request):
    """
    Get report details
    """
    cmte_id = request.user.username
    report_id = request.query_params.get('reportid')
    print("cmte_id", cmte_id)
    print("report_id", report_id)
    try:
        if ('reportid' in request.query_params and (not request.query_params.get('reportid') =='')):
            print("you are here1")
            if int(request.query_params.get('reportid'))>=1:
                print("you are here2")
                with connection.cursor() as cursor:
                    # GET all rows from Reports table
                    
                    query_string = """SELECT cmte_id as cmteId, report_id as reportId, form_type as formType, '' as electionCode, report_type as reportType,  rt.rpt_type_desc as reportTypeDescription, rt.regular_special_report_ind as regularSpecialReportInd, '' as stateOfElection, '' as electionDate, cvg_start_date as cvgStartDate, cvg_end_date as cvgEndDate, due_date as dueDate, amend_ind as amend_Indicator, 0 as coh_bop, (SELECT CASE WHEN due_date IS NOT NULL THEN to_char(due_date, 'YYYY-MM-DD')::date - to_char(now(), 'YYYY-MM-DD')::date ELSE 0 END ) AS daysUntilDue, email_1 as email1, email_2 as email2, additional_email_1 as additionalEmail1, additional_email_2 as additionalEmail2
                                      FROM public.reports rp, public.ref_rpt_types rt WHERE rp.report_type=rt.rpt_type AND delete_ind is distinct from 'Y' AND cmte_id = %s  AND report_id = %s""" 

                    print("query_string", query_string)

                    cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id, report_id])
                
                    for row in cursor.fetchall():
                        data_row = list(row)
                        forms_obj=data_row[0]
                        
            if forms_obj is None:
                raise NoOPError('The Committee: {} does not have any reports listed'.format(cmte_id))

            return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception:
        raise
