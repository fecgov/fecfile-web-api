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

from fecfiler.core.report_helper import new_report_date

# Create your views here.
logger = logging.getLogger(__name__)

LIST_F1M_COLUMNS = ['report_id', 'est_status', 'cmte_id', 'aff_cmte_id', 'aff_date', 'can1_id', 'can1_con', 'can2_id', 'can2_con', 'can3_id', 
					'can3_con', 'can4_id', 'can4_con', 'can5_id', 'can5_con', 'date_51', 'orig_date', 'metreq_date', 'sign_id', 'sign_date']

DICT_F1M_COLUMNS_MAP_INPUT = {
	'committee_id' : 'aff_cmte_id',
	'affiliation_date' : 'aff_date',
	'sign' : 'sign_id',
	'submission_date' : 'sign_date'
}

"""
****************************** Helper Functions ****************************************
"""

def noneCheckMissingParameters(parameter_name_list, checking_dict=None, value_dict=None, function_name="blank"):
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
				','.join(none_list) + ' are defined as None/blank.'
		if missing_list or none_list:
			raise Exception(error_string)
	except Exception as e:
		raise Exception(
			'The noneCheckMissingParameters function is throwing an error: ' + str(e))

def f1m_sql_dict(request):
	try:
		output_dict = {'cmte_id': request.user.username}
		db_key_list = check_columns_f1M(request.query_params.get('step'))
		for key, value in request.data.items():
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
			key_list = ['report_id', 'est_status', 'cmte_id', 'aff_cmte_id', 'aff_date']
		elif step == 'saveCandidate':
			key_list = ['']
		elif step == 'saveDates':
			key_list = ['']
		elif step == 'saveSignatureAndEmail':
			key_list = ['']
		elif step == 'submit':
			key_list = ['']
		else:
			raise Exception('The step value provided {} is invalid'.format(step))
		return key_list
	except Exception as e:
		raise Exception(
			'The check_columns_f1M function is throwing an error: ' + str(e))

def post_sql(request_dict, table, error_function):
	try:
		request_dict['create_date'] = datetime.datetime.now()
		request_dict['last_update_date'] = datetime.datetime.now()
		noneCheckMissingParameters(['report_id', 'cmte_id'], checking_dict=request_dict,
								   value_dict=request_dict, function_name=table+'-POST')
		value_list = []
		key_string = ""
		param_string = ""
		print(request_dict)
		for key, value in request_dict.items():
			key_string += key+", "
			param_string += "%s, "
			value_list.append(value)
		with connection.cursor() as cursor:
			sql = """INSERT INTO public.{}({}) VALUES ({})""".format(table, key_string[:-2], param_string[:-2])
			print(sql)
			cursor.execute(sql,value_list)
			logger.debug(table + " POST")
			logger.debug(cursor.query)
			if cursor.rowcount == 0:
				raise Exception('Failed to insert data into {} table.'.format(table))
	except Exception as e:
		raise Exception(
			'The post_sql function for table : {} is throwing an error in the function {}: '.format(table, error_function) + str(e))

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
				raise Exception('Failed to update data into {} table.'.format(table))
	except Exception as e:
		raise Exception(
			'The put_sql function for table : {} is throwing an error in the function {}: '.format(table, error_function, ) + str(e))

"""
***************************** WRAPPER FUNCTIONS **************************************
"""

def report_last_update_date(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        logger.debug("update report last_update_date after {}".format(func.__name__))
        report_id = res.get("report_id")
        renew_report_update_date(report_id)
        logger.debug("report date updated")
        return res
    return wrapper

"""
****************************** Reports Table ******************************************
"""

def renew_report_update_date(report_id):
    """
    a helper function to update last update date on report when a transaction is added to deleted
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

def next_report_id():
	try:
		with connection.cursor() as cursor:
			cursor.execute("""SELECT nextval('report_id_seq')""")
			report_ids = cursor.fetchone()
			report_id = report_ids[0]
		return report_id
	except Exception as e:
		raise Exception(
			'The get_next_report_id function is throwing an error: ' + str(e))

def check_report_id_status(cmte_id, report_id):
	try:
		with connection.cursor() as cursor:
			cursor.execute("""SELECT report_id FROM public.reports WHERE cmte_id=%s AND report_id=%s
				AND delete_ind IS DISTINCT FROM 'Y'""",[cmte_id, report_id])
			if cursor.rowcount == 0:
				raise Exception("""The report Id: {0} for committee Id: {1} doesnot 
					exist or is deleted.""".format(report_id, cmte_id))
		return report_id
	except Exception as e:
		raise 

def reports_post(request):
	try:
		report_dict = {
			'report_id': str(next_report_id()),
			'cmte_id': request.user.username,
			'form_type': 'F1M',
			'amend_ind': 'N',
			'status': 'Saved'
		}
		post_sql(report_dict, "reports", "reports_post")
		report_id = report_dict.get('report_id')
		return report_id
	except Exception as e:
		raise Exception(
			'The reports_post function is throwing an error: ' + str(e))

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
				output_list.append[candidate_dict]
			del request_dict[column_name]
			del request_dict[column_name[:-2]+'con']
		request_dict['candidates'] = output_list
		return request_dict
	except Exception as e:
		raise Exception(
			'The get_candidate_details function is throwing an error: ' + str(e))

def get_sql_candidate(candidate_id):
	try:
		sql = """SELECT cand_id AS "candidate_id", cand_last_name, cand_first_name, cand_middle_name, 
		cand_prefix, cand_suffix, cand_office, cand_office_state, cand_office_district 
		FROM public.candidate_master WHERE cand_id=%s"""
		with connection.cursor() as cursor:
			cursor.execute("""SELECT json_agg(t) FROM ({}) AS t""",format(sql),[candidate_id])
			logger.debug("CANDIDATE TABLE")
			logger.debug(cursor.query)
			output_dict = cursor.fetchone()[0]
			if output_dict:
				return output_dict[0]
			else:
				raise Exception('The candidateId: {} does not exist in candidate table.'.format(candidate_id))
	except Exception as e:
		raise Exception(
			'The get_sql_candidate function is throwing an error: ' + str(e))

"""
************************************ Form 1M Functions ******************************************
"""
def check_clear_establishment_status(cmte_id, report_id, delete_est_status):
	try:
		if f1M_est_status(cmte_id, report_id) == delete_est_status:
			if delete_est_status == 'Q':
				clear_list = ['can1_id', 'can1_con', 'can2_id', 'can2_con', 'can3_id', 
					'can3_con', 'can4_id', 'can4_con', 'can5_id', 'can5_con', 'date_51', 
					'orig_date', 'metreq_date',]
			elif delete_est_status == 'A':
				clear_list = ['aff_cmte_id']
			else:
				clear_list = []
			f1M_clear(cmte_id, report_id, clear_list)
	except Exception as e:
		raise Exception(
			'The check_establishment_status function is throwing an error: ' + str(e))

def f1M_est_status(cmte_id, report_id):
	try:
		with connection.cursor() as cursor:
			_sql = """SELECT est_status FROM public.form_1m WHERE 
			cmte_id = %s AND report_id = %s AND delete_ind IS DISTINCT FROM 'Y'"""
			cursor.execute(_sql,[cmte_id, report_id])
			est_status = cursor.fetchone()
			if est_status:
				return est_status[0]
			else:
				raise Exception("""The report Id: {0} for committee Id: {1} does 
					not exist or is either deleted in form-1M table.""".format(report_id, cmte_id))
	except Exception as e:
		raise Exception(
			'The f1M_est_status function is throwing an error: ' + str(e))

def f1M_clear(cmte_id, report_id, request_list):
	try:
		if request_list:
			sql_dict = {}
			for item in request_list:
				sql_dict[item] = None
			put_sql(sql_dict, "form_1m", "f1M_clear")
	except Exception as e:
		raise Exception(
			'The f1M_clear function is throwing an error: ' + str(e))


def get_sql_f1m(request_dict):
	try:
		param_string = ""
		noneCheckMissingParameters(['report_id', 'cmte_id'], checking_dict=request_dict,
								   value_dict=request_dict, function_name='get_sql_f1m')
		value_list =[]
		for key, value in request_dict.items():
			if key in ['report_id', 'cmte_id']:
				param_string += "m." + key + "=%s AND "
				value_list.append(value)
		with connection.cursor() as cursor:
			"""
			id, report_id, est_status, cmte_id, aff_cmte_id, aff_date, can1_id, can1_con, 
	       can2_id, can2_con, can3_id, can3_con, can4_id, can4_con, can5_id, 
	       can5_con, date_51, orig_date, metreq_date, sign_id, sign_date, 
	       delete_ind, create_date, last_update_date
			"""
			sql = """SELECT rp.form_type, rp.amend_ind, rp.status, m.report_id AS "reportId", 
				m.cmte_id, m.est_status AS "establishmentType", m.aff_cmte_id AS "committee_id",
				(SELECT cmte.cmte_name FROM committee_master cmte WHERE cmte.cmte_id = m.aff_cmte_id)
				AS "committee_name", m.aff_date AS "affiliation_date", m.can1_id, m.can1_con, 
	        	m.can2_id, m.can2_con, m.can3_id, m.can3_con, m.can4_id, m.can4_con, m.can5_id, 
	        	m.can5_con, m.date_51 AS "fifty_first_contributor_date", m.orig_date AS "registration_date",
	        	m.metreq_date AS "requirements_met_date", m.sign_id, e.last_name AS "sign_last_name", 
	        	e.first_name AS "sign_first_name", e.middle_name AS "sign_middle_name", e.preffix AS "sign_prefix",
	        	e.suffix AS "sign_suffix", m.sign_date AS "submission_date", rp.email_1, rp.email_2,
	        	rp.additional_email_1, rp.additional_email_2
				FROM public.form_1m m 
				JOIN public.reports rp ON m.report_id=rp.report_id AND m.cmte_id=rp.cmte_id
				AND rp.delete_ind IS DISTINCT FROM 'Y' 
				LEFT JOIN public.entity e ON e.entity_id = m.sign_id
				WHERE {} m.delete_ind IS DISTINCT FROM 'Y' """.format(param_string)
			cursor.execute("""SELECT json_agg(t) FROM ({}) AS t""".format(sql),value_list)
			logger.debug("get_sql_f1m")
			logger.debug(cursor.query)
			output_dict = cursor.fetchone()[0]
			if output_dict:
				output_dict = output_dict[0]
				output_dict = get_candidate_details(output_dict)
				return output_dict
			else:				
				raise Exception("""This report Id: {} for committee Id: {} 
					does not exist in forms_1m table""".format(request_dict['report_id'], 
						request_dict['cmte_id']))
	except Exception as e:
		raise Exception(
			'The get_sql_f1m function is throwing an error: '+ str(e))

"""
************************************ API Call ******************************************
"""

@api_view(['POST', 'GET', 'DELETE', 'PUT'])
# @report_last_update_date
def form1M(request):
	cmte_id = request.user.username
	report_flag = False
	"""
	************************************ POST Call - form 1M ******************************************
	"""
	if request.method == "POST":
		# try:
			noneCheckMissingParameters(['step'], checking_dict=request.query_params,
									   value_dict=request.query_params, function_name='form1M-POST')
			step = request.query_params['step']

			# by affiliation step2 POST
			if step == 'saveAffiliation':
				noneCheckMissingParameters(['committee_id', 'affiliation_date'], checking_dict=request.data,
										   value_dict=request.data, function_name='form1M-POST: step-2 Affiliation')
				request_dict = f1m_sql_dict(request)
				request_dict['est_status'] = 'A'
				if 'reportId' in request.data and request.data.get('reportId') not in [None, '', 'null']:
					request_dict['report_id'] = check_report_id_status(cmte_id, request.data.get('reportId'))
					check_clear_establishment_status(cmte_id, request_dict['report_id'], 'Q')
					put_sql(request_dict, "form_1m", "form1m-PUT")
				else:
					request_dict['report_id'] = reports_post(request)
					report_flag = True
					post_sql(request_dict, "form_1m", "form1m-POST")
				output_dict = get_sql_f1m(request_dict)

			# by qualification step2 POST
			if step == 'saveCandidate':
				print()
				# by qualification step3 POST
			if step == 'saveDates':
				print()
				# both step4 POST
			if step == 'saveSignatureAndEmail':
				print()
				# both step4 POST
			if step == 'submit':
				print()
			return JsonResponse(output_dict, status=status.HTTP_200_OK, safe=False)
		# except Exception as e:
		# 	logger.debug(e)
		# 	return Response("The form1M API - POST is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

	"""
	************************************ PUT Call - form 1M ******************************************
	"""
	if request.method == "PUT":
		try:
			noneCheckMissingParameters(['step'], checking_dict=request.query_params,
									   value_dict=request.query_params, function_name='form1M-POST')

		except Exception as e:
			logger.debug(e)
			return Response("The form1M API - PUT is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

	"""
	************************************ GET Call - form 1M ******************************************
	"""
	if request.method == "GET":
		try:
			print('test')

		except Exception as e:
			logger.debug(e)
			return Response("The form1M API - GET is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

	"""
	************************************ DELETE Call - form 1M ******************************************
	"""
	if request.method == "DELETE":
		try:
			print('test')
		except Exception as e:
			logger.debug(e)
			return Response("The form1M API - DELETE is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)









	password = request.data.get('password')
	# user = authenticate(username=username, password=password)
	user = authenticate(request=request)
	if user is not None:
		return Response('authenticated', status=status.HTTP_200_OK)
	else:
		return Response('NOT authenticated', status=status.HTTP_200_OK)
