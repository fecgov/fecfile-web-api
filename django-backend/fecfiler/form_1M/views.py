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

from fecfiler.core.report_helper import new_report_date

# Create your views here.
logger = logging.getLogger(__name__)

"""
****************************** Helper Functions ****************************************
"""


def noneCheckMissingParameters(parameter_name_list, checking_dict=None, value_dict=None, function_name="blank"):
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


"""
************************************ API Call ******************************************
"""


@api_view(['POST', 'GET', 'DELETE', 'PUT'])
def form1M(request):
    cmte_id = request.user.username
    """
	************************************ POST Call - form 1M ******************************************
	"""
    if request.method == "POST":
        try:
            noneCheckMissingParameters(['step'], checking_dict=request.query_params,
                                       value_dict=request.query_params, function_name='form1M-POST')
            step = request.query_params['step']

            # by affiliation step2 POST
            if step = 'saveAffiliation':

                # by qualification step2 POST
            if step = 'saveCandidate':

                # by qualification step3 POST
            if step = 'saveDates':

                # both step4 POST
            if step = 'saveSignatureAndEmail':

                # both step4 POST
            if step = 'submit':

        except Exception as e:
            logger.debug(e)
            return Response("The form1M API - POST is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

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
