from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
import datetime
import os
import requests
import logging
from django.db import connection
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import JsonResponse
from functools import wraps

# Create your views here.
from fecfiler.authentication.authorization import is_read_only_or_filer_reports
from fecfiler.core.views import get_comittee_id, get_next_report_id

logger = logging.getLogger(__name__)

LIST_F1M_COLUMNS = ['report_id', 'est_status', 'cmte_id', 'aff_cmte_id', 'aff_date', 
					'can1_id', 'can1_con', 'can2_id', 'can2_con', 'can3_id', 
					'can3_con', 'can4_id', 'can4_con', 'can5_id', 'can5_con', 
					'date_51', 'orig_date', 'metreq_date', 'sign_id', 'sign_date']

DICT_F1M_COLUMNS_MAP_INPUT = {
	'committee_id' : 'aff_cmte_id',
	'sign' : 'sign_id',
	'submission_date' : 'sign_date',
	'reportId' : 'report_id',
	'establishmentType' : 'est_status',
	'affiliation_date' : 'aff_date',
	'fifty_first_contributor_date' : 'date_51',
	'registration_date' : 'orig_date',
	'requirements_met_date' : 'metreq_date',
	'sign' : 'sign_id',
	'submission_date' : 'sign_date',
	'can1_id' : 'can1_id', 
	'can1_con' : 'can1_con', 
	'can2_id' : 'can2_id', 
	'can2_con' : 'can2_con', 
	'can3_id' : 'can3_id', 
	'can3_con' : 'can3_con', 
	'can4_id' : 'can4_id', 
	'can4_con' : 'can4_con', 
	'can5_id' : 'can5_id', 
	'can5_con' : 'can5_con',
}

"""
****************************** Helper Functions ****************************************
"""

def noneCheckMissingParameters(parameter_name_list, checking_dict=None,
	value_dict=None, function_name="blank"):
	try:
		missing_list = []
		none_list = []
		error_string = ""
		for item in parameter_name_list:
			if checking_dict is not None and item not in checking_dict:
				missing_list.append(item)
			if value_dict is not None and value_dict.get(item) in [None, '', " ", 'null']:
				if item not in missing_list:
					none_list.append(item)
		if missing_list:
			error_string = 'The following parameters: ' + \
				','.join(missing_list) + ' are missing in function: ' + \
				function_name + '.'
		if none_list:
			error_string += ' The ' + function_name + ' function has parameters: ' + \
				','.join(none_list) + ' defined as None/blank.'
		if missing_list or none_list:
			raise Exception(error_string)
	except Exception as e:
		raise Exception(
			'The noneCheckMissingParameters function is throwing an error: ' + str(e))

def f1m_sql_dict(cmte_id, step, request_dict):
	try:
		output_dict = {'cmte_id': cmte_id}
		db_key_list = check_columns_f1M(step)
		for key, value in request_dict.items():
			if key in DICT_F1M_COLUMNS_MAP_INPUT:
				if DICT_F1M_COLUMNS_MAP_INPUT[key] in db_key_list:
					output_dict[DICT_F1M_COLUMNS_MAP_INPUT[key]] = value
		logger.debug(output_dict)
		return output_dict
	except Exception as e:
		raise Exception(
			'The f1m_sql_dict function is throwing an error: ' + str(e))

def check_columns_f1M(step):
	try:
		if step == 'saveAffiliation':
			key_list = ['report_id', 'aff_cmte_id', 'aff_date']
		elif step == 'saveCandidate' or step == 'saveQualification':
			key_list = ['report_id']
		elif step == 'saveDates':
			key_list = ['report_id', 'date_51', 'orig_date', 'metreq_date']
		elif step == 'saveSignatureAndEmail':
			key_list = ['report_id']
		elif step == 'submit':
			key_list = ['report_id', 'sign_id', 'sign_date']
		elif step == 'None':
			key_list = ['report_id']
		elif step == 'All':
			key_list = ['report_id', 'est_status', 'aff_cmte_id', 'aff_date',
				'date_51', 'orig_date', 'metreq_date', 'sign_id', 'sign_date', 'can1_id', 
				'can1_con', 'can2_id', 'can2_con', 'can3_id', 'can3_con', 'can4_id', 
				'can4_con', 'can5_id', 'can5_con']
		else:
			raise Exception('The step value provided {} is invalid'.format(step))
		return key_list
	except Exception as e:
		raise Exception(
			'The check_columns_f1M function is throwing an error: ' + str(e))

def password_authenticate(username, password):
	user = authenticate(username=username, password=password)
	if user is None:
		raise Exception('Password is Invalid. Kindly check if capsLock is ON')

def post_sql(request_dict, table, error_function):
	try:
		request_dict['create_date'] = datetime.datetime.now()
		request_dict['last_update_date'] = datetime.datetime.now()
		noneCheckMissingParameters(['report_id', 'cmte_id'], checking_dict=request_dict,
								   value_dict=request_dict, function_name=table+'-POST')
		value_list = []
		key_string = ""
		param_string = ""
		for key, value in request_dict.items():
			key_string += key+", "
			param_string += "%s, "
			value_list.append(value)
		with connection.cursor() as cursor:
			sql = """INSERT INTO public.{}({}) VALUES ({})""".format(table, 
					key_string[:-2], param_string[:-2])
			cursor.execute(sql,value_list)
			logger.debug(table + " POST")
			logger.debug(cursor.query)
			if cursor.rowcount == 0:
				raise Exception('Failed to insert data into {} table.'.format(table))
	except Exception as e:
		raise Exception(
			"""The post_sql function for table : {} is throwing an error in 
				the function {}: """.format(table, error_function) + str(e))

def put_sql(request_dict, table, error_function="blank"):
	try:
		request_dict['last_update_date'] = datetime.datetime.now()
		param_string = ""
		noneCheckMissingParameters(['report_id', 'cmte_id'], checking_dict=request_dict,
								   value_dict=request_dict, function_name=table+'-PUT')
		value_list = []
		for key, value in request_dict.items():
			if key not in ['report_id', 'cmte_id']:
				param_string += key + "=%s, "
				value_list.append(value)
		with connection.cursor() as cursor:
			sql = """UPDATE public.{} SET {} WHERE cmte_id = %s AND report_id = %s 
				AND delete_ind IS DISTINCT FROM 'Y'""".format(table, param_string[:-2])
			value_list.extend([request_dict['cmte_id'], request_dict['report_id']])
			cursor.execute(sql,value_list)
			logger.debug(table + " PUT")
			logger.debug(cursor.query)
			if cursor.rowcount == 0:
				raise Exception("""Failed to update data in {} table. report Id: {}, 
					committee Id: {}""".format(table,request_dict['report_id'],
					request_dict['cmte_id']))
	except Exception as e:
		raise Exception(
			"""The put_sql function for table : {} is throwing an error in the 
				function {}: """.format(table, error_function) + str(e))

def delete_sql(request_dict, table, error_function="blank"):
	try:
		with connection.cursor() as cursor:
			if request_dict['delete_ind']:
				print_text = "delete"
			else:
				print_text = "restore"
			sql = """UPDATE public.{} SET delete_ind = %s, last_update_date=%s
				WHERE cmte_id=%s AND report_id=%s""".format(table)
			cursor.execute(sql,[request_dict['delete_ind'], datetime.datetime.now(),
				request_dict['cmte_id'], request_dict['report_id']])
			logger.debug(table + " DELETE")
			logger.debug(cursor.query)
			if cursor.rowcount == 0:
				raise Exception("""Failed to {} data in {} table. report Id: {}, 
					committee Id: {}""".format(print_text,table,request_dict['report_id'],
					request_dict['cmte_id']))
	except Exception as e:
		raise Exception(
			"""The delete_sql function for table : {} is throwing an error 
			in the function {}: """.format(table, error_function) + str(e))

def remove_sql(request_dict, table, error_function="blank"):
	try:
		with connection.cursor() as cursor:
			sql = """DELETE FROM public.{}
				WHERE cmte_id=%s AND report_id=%s""".format(table)
			cursor.execute(sql,[request_dict['cmte_id'], request_dict['report_id']])
			logger.debug(table + " REMOVE")
			logger.debug(cursor.query)
			if cursor.rowcount == 0:
				raise Exception("""Failed to remove report from {} table. report Id: {}, 
					committee Id: {}""".format(table,request_dict['report_id'],
					request_dict['cmte_id']))
	except Exception as e:
		raise Exception(
			"""The remove_sql function for table : {} is throwing an error in the 
			function {}: """.format(table, error_function) + str(e))

def check_candidate_number(candidate_number):
	try:
		if 1 <= int(candidate_number) <= 5:
			return candidate_number
		else:
			raise Exception("""The candidate number can only be in between and including 
				1 and 5. Input received: {}""".format(candidate_number))

	except Exception as e:
		raise Exception(
			"""The check_candidate_number function is 
			throwing an error : """.format(candidate_number) + str(e))
"""
***************************** WRAPPER FUNCTIONS **************************************
"""

def report_last_update_date(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        logger.debug("update report last_update_date after {}".format(func.__name__))
        logger.debug(res)
        report_id = res[1].get("reportId")
        update_report_update_date(report_id)
        logger.debug("report date updated")
        return res
    return wrapper

"""
**************************** Committee Master Table **********************************
"""

def committee_master_get(request_dict):
	try:
		with connection.cursor() as cursor:
			sql = """SELECT cmte_email_1 AS "email_1", cmte_email_2 AS "email_2" 
				FROM public.committee_master WHERE cmte_id=%s"""
			cursor.execute("""SELECT json_agg(t) FROM ({}) AS t""".format(sql),
				[request_dict['cmte_id']])
			logger.debug("COMMITTE MASTER TABLE")
			logger.debug(cursor.query)
			output_dict = cursor.fetchone()[0]
			if output_dict:
				return output_dict[0]
			else:
				raise Exception("""The committee Id: {} does not exist in 
					committee_master table.""".format(request_dict['cmte_id']))
	except Exception as e:
		raise Exception("""The committee_master_get function is 
			throwing an error: """ + str(e))

def get_cmte_type(cmte_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT cmte_type_category FROM public.committee_master 
            	WHERE cmte_id=%s""", [cmte_id])
            cmte_type_tuple = cursor.fetchone()
            if cmte_type_tuple:
                return cmte_type_tuple[0]
            else:
                raise Exception("""The cmte_id: {} does not exist in committee master 
                	table.""".format(cmte_id))
    except Exception as err:
        raise Exception(f"The cmte_type function is throwing an error: {err}")

"""
****************************** Reports Table ******************************************
"""

def update_report_update_date(report_id):
    """
    a helper function to update last update date on report 
    when a transaction is added to deleted
    """
    try:
        logger.debug(
            "renew report last_update_date with report_id:{}".format(report_id)
        )
        _sql = """
        UPDATE public.reports
        SET last_update_date = %s
        WHERE report_id = %s 
        """
        with connection.cursor() as cursor:
            cursor.execute(_sql, [datetime.datetime.now(), report_id])
            if cursor.rowcount == 0:
                raise Exception("Error: updating report update date failed.")
    except:
        raise

def check_report_id_status(cmte_id, report_id, delete_flag=True, submit_flag=True):
	try:
		if report_id not in [None, '', " ", 'null']:

			if delete_flag:
				param_string = "AND delete_ind IS DISTINCT FROM 'Y'"
			else:
				param_string = ""

			with connection.cursor() as cursor:
				cursor.execute("""SELECT status FROM public.reports 
					WHERE cmte_id=%s AND report_id=%s {}""".format(param_string),
					[cmte_id, report_id])
				if cursor.rowcount == 0:
					raise Exception("""The report Id: {0} for committee Id: {1} 
						doesnot exist or is deleted.""".format(report_id, cmte_id))
				else:
					report_status = cursor.fetchone()[0]
					logger.debug("REPORT status: " + report_status)
					if report_status not in ['Saved', '', None, " "] and submit_flag:
						raise Exception("""The report Id: {0} for committee Id: {1}
							is already submitted.""".format(report_id, cmte_id))
		else:
			raise Exception("""Report Id cannot be none or blank. 
				Kindly check. Input received: """ + report_id)
	except Exception as e:
		raise 

def report_post(request):
	try:
		report_dict = {
			'report_id': str(get_next_report_id()),
			'cmte_id': get_comittee_id(request.user.username),
			'form_type': 'F1M',
			'amend_ind': 'N',
			'status': 'Saved'
		}
		cmte_dict = committee_master_get(report_dict)
		request_dict = {**report_dict, **cmte_dict}
		post_sql(request_dict, "reports", "reports-POST")
		report_id = report_dict.get('report_id')
		return True,report_id
	except Exception as e:
		raise Exception(
			'The report_post function is throwing an error: ' + str(e))

def report_put(request_dict):
	try:
		put_sql(request_dict, "reports", "reports-PUT")
		return True
	except Exception as e:
		raise Exception(
			'The report_put function is throwing an error: '+ str(e))

def report_delete(report_dict):
	try:
		delete_sql(report_dict, "reports", "reports_delete")
	except Exception as e:
		raise Exception(
			'The report_delete function is throwing an error: ' + str(e))

def report_remove(report_dict):
	try:
		remove_sql(report_dict, "reports", "reports_remove")
	except Exception as e:
		raise Exception(
			'The report_remove function is throwing an error: ' + str(e))

def report_get(request_dict):
	try:
		with connection.cursor() as cursor:
			sql = """SELECT report_id, form_type, cmte_id, status, email_1, 
				email_2, additional_email_1, additional_email_2
				FROM public.reports WHERE cmte_id=%s AND report_id=%s"""
			cursor.execute("""SELECT json_agg(t) FROM ({}) AS t""".format(sql),
				[request_dict['cmte_id'],request_dict['report_id']])
			logger.debug("REPORTS TABLE")
			logger.debug(cursor.query)
			output_dict = cursor.fetchone()[0]
			if output_dict:
				return output_dict[0]
			else:
				raise Exception("""The report Id: {} does not exist in reports 
					table for committeeId: {}""".format(request_dict['report_id'],
					request_dict['cmte_id']))
	except Exception as e:
		raise Exception('The report_get function is throwing an error: ' + str(e))

"""
***************************** CANDIDATE DETAILS API *************************************
"""

def get_candidate_details(request_dict):
	try:
		output_list = []
		for i in range(1,6):
			column_name = 'can'+str(i)+'_id'
			candidate_id = request_dict.get(column_name)
			if candidate_id:
				candidate_dict = get_sql_candidate(candidate_id)
				candidate_dict['contribution_date'] = request_dict.get(column_name[:-2]+'con')
				candidate_dict['candidate_number'] = i
				output_list.append(candidate_dict)
			del request_dict[column_name]
			del request_dict[column_name[:-2]+'con']
		request_dict['candidates'] = output_list
		return request_dict
	except Exception as e:
		raise Exception(
			'The get_candidate_details function is throwing an error: ' + str(e))

def get_sql_candidate(candidate_id):
	try:
		sql = """SELECT cand_id AS "candidate_id", cand_last_name, cand_first_name, 
		cand_middle_name, cand_prefix, cand_suffix, cand_office, cand_office_state, 
		cand_office_district FROM public.candidate_master WHERE cand_id=%s"""
		with connection.cursor() as cursor:
			cursor.execute("""SELECT json_agg(t) FROM ({}) AS t""".format(sql),[candidate_id])
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
			'The get_sql_candidate function is throwing an error: ' + str(e))

"""
************************************ Helper Functions ******************************************
"""

def step4_reports_put(request):
	try:
		report_dict = {}
		if 'additionalEmail1' in request.data and request.data['additionalEmail1'] not in [None, '', " ", 'null']:
			report_dict['additional_email_1'] = request.data['additionalEmail1']
		else:
			report_dict['additional_email_1'] = None
		if 'additionalEmail2' in request.data and request.data['additionalEmail2'] not in [None, '', " ", 'null']:
			report_dict['additional_email_2'] = request.data['additionalEmail2']
		else:
			report_dict['additional_email_2'] = None
		if report_dict:
			report_dict['cmte_id'] = get_comittee_id(request.user.username)
			report_dict['report_id'] = request.data['reportId']
			previous_report_dict = report_get(report_dict)
			report_flag = report_put(report_dict)
			return report_flag, previous_report_dict
		else:
			return False, {}
	except Exception as e:
		raise Exception(
			'The step4_reports_put function is throwing an error: ' + str(e))

def submit_f1m_report(request):
	try:
		report_dict= {'status' : "Submitted"}
		report_dict['filed_date'] = datetime.datetime.now()
		report_dict['cmte_id'] = get_comittee_id(request.user.username)
		report_dict['report_id'] = request.data['reportId']
		return report_put(report_dict)
	except Exception as e:
		raise Exception(
			'The submit_report function is throwing an error: ' + str(e))
"""
************************************ Form 1M Functions ******************************************
"""

def check_clear_establishment_status(cmte_id, report_id, delete_est_status):
	try:
		if delete_est_status == 'Q':
			clear_list = ['can1_id', 'can1_con', 'can2_id', 'can2_con', 'can3_id', 
				'can3_con', 'can4_id', 'can4_con', 'can5_id', 'can5_con', 'date_51', 
				'orig_date', 'metreq_date',]
		elif delete_est_status == 'A':
			clear_list = ['aff_cmte_id', 'aff_date']
		else:
			clear_list = []
		logger.debug('CLEAR LIST')
		logger.debug(clear_list)
		f1M_clear(cmte_id, report_id, clear_list)
	except Exception as e:
		raise Exception(
			'The check_establishment_status function is throwing an error: ' + str(e))

def f1M_clear(cmte_id, report_id, request_list):
	try:
		if request_list:
			sql_dict = {'cmte_id' : cmte_id,
						'report_id' : report_id}
			for item in request_list:
				sql_dict[item] = None
			logger.debug("f1M_clear")
			logger.debug(sql_dict)
			put_sql(sql_dict, "form_1m", "f1M_clear")
	except Exception as e:
		raise Exception(
			'The f1M_clear function is throwing an error: ' + str(e))


def get_sql_f1m(request_dict, complete=False):
	try:
		param_string = ""
		value_list =[]
		for key, value in request_dict.items():
			if key in ['report_id', 'cmte_id']:
				param_string += "m." + key + "=%s AND "
				value_list.append(value)
		with connection.cursor() as cursor:
			sql = """SELECT rp.form_type, rp.amend_ind, rp.status, m.report_id AS "reportId", 
				m.cmte_id, m.est_status AS "establishmentType", m.aff_cmte_id AS "committee_id",
				(SELECT cmte.cmte_name FROM committee_master cmte WHERE cmte.cmte_id = m.aff_cmte_id)
				AS "committee_name", m.aff_date AS "affiliation_date", m.can1_id, m.can1_con, 
				m.can2_id, m.can2_con, m.can3_id, m.can3_con, m.can4_id, m.can4_con, m.can5_id, 
				m.can5_con, m.date_51 AS "fifty_first_contributor_date", m.orig_date AS "registration_date",
				m.metreq_date AS "requirements_met_date", m.sign_id, cm.treasurer_last_name AS "sign_last_name", 
				cm.treasurer_first_name AS "sign_first_name", cm.treasurer_middle_name AS "sign_middle_name", 
				cm.treasurer_prefix AS "sign_prefix", cm.treasurer_suffix AS "sign_suffix", 
				m.sign_date AS "submission_date", rp.email_1, rp.email_2, rp.additional_email_1, 
				rp.additional_email_2, cm.treasurer_last_name, cm.treasurer_first_name, 
				cm.treasurer_middle_name, cm.treasurer_prefix, cm.treasurer_suffix
				FROM public.form_1m m 
				JOIN public.reports rp ON m.cmte_id=rp.cmte_id AND m.report_id=rp.report_id
				LEFT JOIN public.entity e ON e.entity_id = m.sign_id
				LEFT JOIN public.committee_master cm ON cm.cmte_id = m.cmte_id
				WHERE {} """.format(param_string[:-4])
			cursor.execute("""SELECT json_agg(t) FROM ({}) AS t""".format(sql),value_list)
			logger.debug("get_sql_f1m")
			logger.debug(cursor.query)
			output_dict = cursor.fetchone()[0]
			if output_dict:
				output_dict = output_dict[0]
				if complete:
					output_dict = get_candidate_details(output_dict)
				return output_dict
			else:				
				raise Exception("""This report Id: {} for committee Id: {} 
					does not exist in forms_1m table""".format(request_dict['report_id'], 
						request_dict['cmte_id']))
	except Exception as e:
		raise Exception(
			'The get_sql_f1m function is throwing an error: '+ str(e))

def validate_before_submit(request_dict):
	try:
		if request_dict['establishmentType'] == "A":
			noneCheckMissingParameters(['reportId', 'cmte_id', 'committee_id', 
				'affiliation_date', 'sign_id', 'submission_date'], 
				checking_dict=request_dict, value_dict=request_dict, 
				function_name='validate_before_submit')
		elif request_dict['establishmentType'] == "Q":
			cmte_type = get_cmte_type(request_dict['cmte_id'])
			if  cmte_type == "PAC":
				noneCheckMissingParameters(['reportId', 'cmte_id', 
					'fifty_first_contributor_date', 'registration_date', 
					'requirements_met_date', 'sign_id', 'submission_date'
					'can1_id', 'can1_con', 'can2_id', 'can2_con', 'can3_id', 
					'can3_con', 'can4_id', 'can4_con', 'can5_id'], 
					checking_dict=request_dict, value_dict=request_dict, 
					function_name='validate_before_submit')
			else:
				noneCheckMissingParameters(['reportId', 'cmte_id', 
					'fifty_first_contributor_date', 'registration_date', 
					'requirements_met_date', 'sign_id', 'submission_date'], 
					checking_dict=request_dict, value_dict=request_dict, 
					function_name='validate_before_submit')
		else:
			raise Exception("""The establishment status is not correctly defined. 
				options allowed are 'A' and 'Q'. Data stored: {}""".format(
					request_dict['establishmentType']))
	except Exception as e:
		raise 

"""
************************************ Form 1M CRUD Functions ******************************************
"""

@report_last_update_date
def f1m_post(request_dict):
	try:
		post_sql(request_dict, "form_1m", "form1m-POST")
		return True,get_sql_f1m(request_dict)
	except Exception as e:
		raise Exception(
			'The f1m_post function is throwing an error: '+ str(e))

@report_last_update_date
def f1m_put(request_dict):
	try:
		put_sql(request_dict, "form_1m", "form1m-PUT")
		return True,get_sql_f1m(request_dict)
	except Exception as e:
		raise Exception(
			'The f1m_put function is throwing an error: '+ str(e))

def f1m_delete(request_dict):
	try:
		delete_sql(request_dict, "form_1m", "form1m-DELETE")
	except Exception as e:
		raise Exception(
			'The f1m_delete function is throwing an error: '+ str(e))

def f1m_remove(request_dict):
	try:
		remove_sql(request_dict, "form_1m", "form1m-REMOVE")
	except Exception as e:
		raise Exception(
			'The f1m_remove function is throwing an error: '+ str(e))

"""
******************************************************************************************************
                        FORM 1M API Call - SPRINT 30 - BY PRAVEEN JINKA
******************************************************************************************************
"""

@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def form1M(request):
	cmte_id = get_comittee_id(request.user.username)
	report_flag = False
	f1m_flag = False
	previous_report_dict = None
	previous_f1m_dict = None
	"""
	************************************ POST Call - form 1M ******************************************
	"""
	if request.method == "POST":
		try:
			noneCheckMissingParameters(['step'], checking_dict=request.query_params,
						   value_dict=request.query_params, function_name='form1M-POST')
			step = request.query_params['step']

			# by affiliation step2 POST
			if step == 'saveAffiliation':
				try:
					is_read_only_or_filer_reports(request)
					noneCheckMissingParameters(['committee_id', 'affiliation_date'], checking_dict=request.data,
							   value_dict=request.data, function_name='form1M-POST: step-2 Affiliation')
					request_dict = f1m_sql_dict(cmte_id, step, request.data)
					request_dict['est_status'] = 'A'
					if 'report_id' in request_dict:
						check_report_id_status(cmte_id, request_dict['report_id'])
						previous_f1m_dict = get_sql_f1m(request_dict)
						check_clear_establishment_status(cmte_id, request_dict['report_id'], 'Q')
						f1m_flag, output_dict = f1m_put(request_dict)
					else:
						report_flag, request_dict['report_id'] = report_post(request)
						f1m_flag, output_dict = f1m_post(request_dict)

				except Exception as e:
					json_result = {'message': str(e)}
					return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)

			# by qualification step2 POST - skipping candidates
			elif step == 'saveQualification':
				request_dict = f1m_sql_dict(cmte_id, step, request.data)
				request_dict['est_status'] = 'Q'
				if 'report_id' in request_dict:
					check_report_id_status(cmte_id, request_dict['report_id'])
					previous_f1m_dict = get_sql_f1m(request_dict)
					check_clear_establishment_status(cmte_id, request_dict['report_id'], 'A')
					f1m_flag, output_dict = f1m_put(request_dict)
				else:
					report_flag, request_dict['report_id'] = report_post(request)
					f1m_flag, output_dict = f1m_post(request_dict)

			# by qualification step2 POST
			elif step == 'saveCandidate':
				noneCheckMissingParameters(['candidate_id', 'contribution_date',
					'candidate_number'],
					checking_dict=request.data, value_dict=request.data,
					function_name='form1M-POST: step-2 Qualification')
				candidate_number = check_candidate_number(request.data['candidate_number'])
				request_dict = f1m_sql_dict(cmte_id, step, request.data)
				column_name = 'can'+candidate_number+'_id'
				request_dict[column_name] = request.data['candidate_id']
				request_dict[column_name[:-2]+'con'] = request.data['contribution_date']
				if candidate_number == '1':
					request_dict['est_status'] = 'Q'
				if 'report_id' in request_dict:
					check_report_id_status(cmte_id, request_dict['report_id'])
					previous_f1m_dict = get_sql_f1m(request_dict)
					if candidate_number == '1':
						check_clear_establishment_status(cmte_id, request_dict['report_id'], 'A')
					f1m_flag, output_dict = f1m_put(request_dict)
				elif candidate_number == '1':
					report_flag, request_dict['report_id'] = report_post(request)
					f1m_flag, output_dict = f1m_post(request_dict)
				else:
					raise Exception('reportId parameter is mandatory for this step.')

			# by qualification step3 POST
			elif step == 'saveDates':
				noneCheckMissingParameters(['reportId', 'registration_date',
					'fifty_first_contributor_date',
					'requirements_met_date'], checking_dict=request.data, value_dict=request.data,
					function_name='form1M-POST: step-3 Qualification')
				request_dict = f1m_sql_dict(cmte_id, step, request.data)
				check_report_id_status(cmte_id, request_dict['report_id'])
				previous_f1m_dict = get_sql_f1m(request_dict)
				check_clear_establishment_status(cmte_id, request_dict['report_id'], 'A')
				f1m_flag, output_dict = f1m_put(request_dict)

			# both step4 POST
			elif step == 'saveSignatureAndEmail':
				noneCheckMissingParameters(['reportId'],
					checking_dict=request.data, value_dict=request.data,
					function_name='form1M-POST: step-4 SAVE')
				request_dict = f1m_sql_dict(cmte_id, step, request.data)
				check_report_id_status(cmte_id, request_dict['report_id'])
				previous_f1m_dict = get_sql_f1m(request_dict)
				f1m_flag, output_dict = f1m_put(request_dict)
				report_flag, previous_report_dict = step4_reports_put(request)

			# both step4 POST
			elif step == 'submit':
				noneCheckMissingParameters(['sign', 'submission_date', 'reportId'], 
					checking_dict=request.data, value_dict=request.data, 
					function_name='form1M-POST: step-4 SUBMIT')
				# password = request.data['filingPassword']
				# password_authenticate(cmte_id, password)
				request_dict = f1m_sql_dict(cmte_id, step, request.data)
				check_report_id_status(cmte_id, request_dict['report_id'])
				previous_f1m_dict = get_sql_f1m(request_dict)
				f1m_flag, output_dict = f1m_put(request_dict)
				report_flag, previous_report_dict = step4_reports_put(request)
				validate_before_submit(output_dict)
				submit_flag = submit_f1m_report(request)
			else:
				raise Exception("""Kindly provide a valid value for 'step' parameter.
				Input received: {}""".format(step))

			output_dict = get_sql_f1m(request_dict, True)
			return JsonResponse(output_dict, status=status.HTTP_200_OK, safe=False)
		except Exception as e:
			logger.debug('ENTERED EXCEPTION CATCH - POST')
			if report_flag and previous_report_dict:
				report_put(previous_report_dict)
			if report_flag and not previous_report_dict:
				report_remove(request_dict)
			if f1m_flag and previous_f1m_dict:
				f1m_put(f1m_sql_dict(cmte_id, "All", previous_f1m_dict))
			if f1m_flag and not previous_f1m_dict:
				f1m_remove(request_dict)
			logger.debug(e)
			return Response("The form1M API - POST is throwing an error: " + str(e),
				status=status.HTTP_400_BAD_REQUEST)

	"""
	************************************ PUT Call - form 1M ******************************************
	"""
	if request.method == "PUT":

		try:
			is_read_only_or_filer_reports(request)
			try:
				noneCheckMissingParameters(['step'], checking_dict=request.query_params,
				   value_dict=request.query_params, function_name='form1M-PUT')
				step = request.query_params['step']

				# by affiliation step2 PUT
				if step == 'saveAffiliation':
					noneCheckMissingParameters(['reportId','committee_id', 'affiliation_date'],
						checking_dict=request.data, value_dict=request.data,
						function_name='form1M-PUT: step-2 Affiliation')
					request_dict = f1m_sql_dict(cmte_id, step, request.data)
					check_report_id_status(cmte_id, request_dict['report_id'])
					request_dict['est_status'] = 'A'
					previous_f1m_dict = get_sql_f1m(request_dict)
					check_clear_establishment_status(cmte_id, request_dict['report_id'], 'Q')
					f1m_flag, output_dict = f1m_put(request_dict)

				# by qualification step2 PUT
				elif step == 'saveCandidate':
					noneCheckMissingParameters(['reportId','candidate_id', 'contribution_date',
						'candidate_number'],
						checking_dict=request.data, value_dict=request.data,
						function_name='form1M-PUT: step-2 Qualification')
					request_dict = f1m_sql_dict(cmte_id, step, request.data)
					check_report_id_status(cmte_id, request_dict['report_id'])
					candidate_number = check_candidate_number(request.data['candidate_number'])
					column_name = 'can'+candidate_number+'_id'
					request_dict[column_name] = request.data['candidate_id']
					request_dict[column_name[:-2]+'con'] = request.data['contribution_date']
					previous_f1m_dict = get_sql_f1m(request_dict)
					if candidate_number == '1':
						check_clear_establishment_status(cmte_id, request_dict['report_id'], 'A')
						request_dict['est_status'] = 'Q'
					f1m_flag, output_dict = f1m_put(request_dict)

				# by qualification step3 PUT
				elif step == 'saveDates':
					noneCheckMissingParameters(['reportId', 'registration_date',
						'fifty_first_contributor_date', 'requirements_met_date'],
						checking_dict=request.data, value_dict=request.data,
						function_name='form1M-PUT: step-3 Qualification')
					request_dict = f1m_sql_dict(cmte_id, step, request.data)
					check_report_id_status(cmte_id, request_dict['report_id'])
					previous_f1m_dict = get_sql_f1m(request_dict)
					check_clear_establishment_status(cmte_id, request_dict['report_id'], 'A')
					f1m_flag, output_dict = f1m_put(request_dict)

				# both step4 PUT
				elif step == 'saveSignatureAndEmail':
					noneCheckMissingParameters(['reportId'],
						checking_dict=request.data, value_dict=request.data,
						function_name='form1M-PUT: step-4 SAVE')
					request_dict = f1m_sql_dict(cmte_id, step, request.data)
					check_report_id_status(cmte_id, request_dict['report_id'])
					previous_f1m_dict = get_sql_f1m(request_dict)
					f1m_flag, output_dict = f1m_put(request_dict)
					report_flag, previous_report_dict = step4_reports_put(request)
				else:
					raise Exception("""Kindly provide a valid value for 'step' parameter.
					Input received: {}""".format(step))

				output_dict = get_sql_f1m(request_dict, True)
				return JsonResponse(output_dict, status=status.HTTP_200_OK, safe=False)
			except Exception as e:
				logger.debug('ENTERED EXCEPTION CATCH - PUT')
				if report_flag and previous_report_dict:
					report_put(previous_report_dict)
				if report_flag and not previous_report_dict:
					report_remove(request_dict)
				if f1m_flag and previous_f1m_dict:
					f1m_put(f1m_sql_dict(cmte_id, "All", previous_f1m_dict))
				if f1m_flag and not previous_f1m_dict:
					f1m_remove(request_dict)
				logger.debug(e)
				return Response("The form1M API - PUT is throwing an error: " + str(e),
					status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			json_result = {'message': str(e)}
			return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)

	"""
	************************************ GET Call - form 1M ******************************************
	"""
	if request.method == "GET":
		try:
			step = "None"
			noneCheckMissingParameters(['reportId'], checking_dict=request.query_params,
				   value_dict=request.query_params, function_name='form1M-GET')
			request_dict = f1m_sql_dict(cmte_id, step, request.query_params)
			check_report_id_status(cmte_id, request.query_params['reportId'], delete_flag=False, submit_flag=False)
			output_dict = get_sql_f1m(request_dict, True)
			return JsonResponse(output_dict, status=status.HTTP_200_OK, safe=False)
		except Exception as e:
			logger.debug(e)
			return Response("The form1M API - GET is throwing an error: " + str(e), 
				status=status.HTTP_400_BAD_REQUEST)

	"""
	************************************ DELETE Call - form 1M ******************************************
	"""
	if request.method == "DELETE":
		try:
			step = "None"
			noneCheckMissingParameters(['reportId', 'delete_ind'], 
				checking_dict=request.data,value_dict=request.data, 
				function_name='form1M-DELETE')
			request_dict = f1m_sql_dict(cmte_id, step, request.data)
			check_report_id_status(cmte_id, request_dict['report_id'], False)
			if request.data['delete_ind'] == 'Y':
				request_dict['delete_ind'] = 'Y'
			else:
				request_dict['delete_ind'] = None
			f1m_delete(request_dict)
			report_delete(request_dict)
			return JsonResponse(request_dict, status=status.HTTP_200_OK, safe=False)
		except Exception as e:
			logger.debug(e)
			return Response("The form1M API - DELETE is throwing an error: " + str(e), 
				status=status.HTTP_400_BAD_REQUEST)

"""
************************************** END OF FORM 1M API Call *********************************************
"""
def noneCheckTrueorFalse(parameter, check_dict):
	try:
		if parameter in check_dict and check_dict[parameter] not in [None, '', " ", 'null']:
			return True
		else:
			return False
	except Exception as e:
		logger.debug(e)
		return Response("The noneCheckTrueorFalse is throwing an error: " + str(e), 
			status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_details(request):
	try:
		cmte_id =  get_comittee_id(request.user.username)
		noneCheckMissingParameters(['type'], 
				checking_dict=request.query_params,value_dict=request.query_params, 
				function_name='get_details')
		type = request.query_params['type'].lower()
		if type == 'committee':
			if noneCheckTrueorFalse('committee_id', request.query_params):
				param_string = """cmte_id ILIKE '{}%'""".format(
					request.query_params['committee_id'].lower())
			elif noneCheckTrueorFalse('committee_name', request.query_params):
				param_string = """cmte_name ILIKE '{}%'""".format(
					request.query_params['committee_name'].lower())
			else:
				raise Exception("""For committee type, only committee_id, 
					committee_name are valid parameters""")
			sql = """SELECT cmte_id AS "committee_id", cmte_name AS "committee_name" 
				FROM public.committee_master WHERE {} 
				ORDER BY cmte_name ASC""".format(param_string)
		elif type == 'candidate':
			if noneCheckTrueorFalse('candidate_id', request.query_params):
				param_string = """cand_id ILIKE '{}%'""".format(
					request.query_params['candidate_id'].lower())
			elif noneCheckTrueorFalse('cand_last_name', request.query_params):
				param_string = """cand_last_name ILIKE '{}%'""".format(
					request.query_params['cand_last_name'].lower())
			elif noneCheckTrueorFalse('cand_first_name', request.query_params):
				param_string = """cand_first_name ILIKE '{}%'""".format(
					request.query_params['cand_first_name'].lower())
			else:
				raise Exception("""For candidate type, only candidate_id, cand_last_name, 
					cand_first_name are valid parameters""")
			sql = """SELECT cand_id AS "candidate_id", cand_last_name, cand_first_name, 
				cand_middle_name, cand_prefix, cand_suffix, cand_office, cand_office_state, 
				cand_office_district FROM public.candidate_master WHERE {} 
				ORDER BY cand_last_name ASC, cand_first_name ASC""".format(param_string)
		elif type == 'treasurer':
			if noneCheckTrueorFalse('treasurer', request.query_params):
				param_string = """(treasurer_last_name ILIKE '{0}%' OR
				treasurer_first_name ILIKE '{0}%') AND cmte_id='{1}'""".format(
					request.query_params['treasurer'].lower(), cmte_id)
			else:
				raise Exception("""For treasurer type, only treasurer is 
					valid parameters""")
			sql = """SELECT treasurer_last_name, treasurer_first_name, treasurer_middle_name, 
				treasurer_prefix, treasurer_suffix FROM public.committee_master 
				WHERE {}""".format(param_string)
		else:
			raise Exception("""type parameter can have only these values : 'committee', 
				'candidate', 'treasurer'""")
		with connection.cursor() as cursor:
			cursor.execute("""SELECT json_agg(t) FROM ({}) AS t""".format(sql))
			logger.debug("get_details")
			logger.debug(cursor.query)
			output_dict = cursor.fetchone()[0]
			if not output_dict:
				output_dict = []
		return JsonResponse(output_dict, status=status.HTTP_200_OK, safe=False)
	except Exception as e:
		logger.debug(e)
		return Response("The get_details API is throwing an error: " + str(e), 
			status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def get_original_registration_date(request):
	try:
		cmte_id = get_comittee_id(request.user.username)
		sql="""SELECT sub_date AS "registration_date" FROM public.form_1 
			WHERE comid = %s ORDER BY repid LIMIT 1"""
		with connection.cursor() as cursor:
			cursor.execute("""SELECT json_agg(t) FROM ({}) AS t""".format(sql), [cmte_id])
			logger.debug("get_original_registration")
			logger.debug(cursor.query)
			output_dict = cursor.fetchone()[0]
			if output_dict:
				output_dict = output_dict[0]
			else:
				raise Exception("""This committee doesnot have entries in form_1 table. 
					Kindly check with DB admin. committeeId: {}""".format(cmte_id))
		return JsonResponse(output_dict, status=status.HTTP_200_OK, safe=False)
	except Exception as e:
		logger.debug(e)
		return Response("The get_original_registration API is throwing an error: " + str(e), 
			status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def get_committee_met_req_date(request):
	try:
		cmte_id = get_comittee_id(request.user.username)
		print(request.query_params)
		noneCheckMissingParameters(['reportId', 'fifty_first_contributor_date'], 
				checking_dict=request.data,value_dict=request.data, 
				function_name='get_committee_met_req_date')
		sql = """SELECT f1m.can1_con, f1m.can2_con, f1m.can3_con, f1m.can4_con, 
			f1m.can5_con, f1.sub_date FROM public.form_1m f1m
			LEFT JOIN public.form_1 f1 ON f1.comid = f1m.cmte_id 
			WHERE f1m.cmte_id = %s AND f1m.report_id = %s AND f1m.delete_ind IS
			DISTINCT FROM 'Y' ORDER BY f1.repid LIMIT 1"""
		with connection.cursor() as cursor:
			cursor.execute(sql,[cmte_id, request.data['reportId']])
			logger.debug("get_committee_met_req_date")
			logger.debug(cursor.query)
			output_list = cursor.fetchall()
			if output_list:
				output_list = list(filter(None, output_list[0]))
			else:
				raise Exception("""The reportId: {} does not exist in form 1m table 
					for committeeId: {}""".format(request.data['reportId'],cmte_id))
		fifty_date = request.data['fifty_first_contributor_date']
		output_list.append(datetime.datetime.strptime(fifty_date, '%Y-%m-%d').date())
		output = {'requirements_met_date': max(output_list)}
		return JsonResponse(output, status=status.HTTP_200_OK, safe=False)
	except Exception as e:
		logger.debug(e)
		return Response("The get_committee_met_req_date API is throwing an error: " + str(e), 
			status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_candidate_f1m(request):
	try:
		is_read_only_or_filer_reports(request)
		try:
			cmte_id = get_comittee_id(request.user.username)
			noneCheckMissingParameters(['reportId',	'candidate_number'],
				checking_dict=request.query_params, value_dict=request.query_params,
				function_name='delete_candidate_f1m')
			request_dict = {}
			report_id = request.query_params['reportId']
			check_report_id_status(cmte_id, report_id)
			request_dict['cmte_id'] = cmte_id
			request_dict['report_id'] = report_id
			candidate_number = check_candidate_number(request.query_params['candidate_number'])
			request_dict['can'+candidate_number+'_id'] = None
			request_dict['can'+candidate_number+'_con'] = None
			put_sql(request_dict, "form_1m", "delete_candidate_f1m")
			output_dict = get_sql_f1m(request_dict)
			return JsonResponse(output_dict, status=status.HTTP_201_CREATED, safe=False)
		except Exception as e:
			logger.debug(e)
			return Response("The delete_candidate_f1m API is throwing an error: " + str(e),
				status=status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		json_result = {'message': str(e)}
		return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)