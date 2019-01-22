"""
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
import maya
from .models import Cmte_Report_Types_View
from rest_framework.response import Response
import json
import datetime
import os
import requests
from django.views.decorators.csrf import csrf_exempt
import logging
from django.db import connection
from django.http import JsonResponse

# Create your views here.

@api_view(['GET'])
def get_filed_report_types(request):

    
    #Fields for identifying the committee type and committee design and filter the forms category 
    
    try:
        #import ipdb;ipdb.set_trace()
        comm_id = request.user.username
        
        #forms_obj = [obj.__dict__ for obj in Cmte_Report_Types_View.objects.raw("select report_type,rpt_type_desc,regular_special_report_ind,rpt_type_info, cvg_start_date,
        #cvg_end_date,due_date from public.cmte_report_types_view where cmte_id='" + comm_id + "' order by rpt_type_order")]

        forms_obj = []
        with connection.cursor() as cursor:
            cursor.execute("select form_type, report_type,rpt_type_desc,regular_special_report_ind,rpt_type_info, cvg_start_date,cvg_end_date,due_date from public.cmte_report_types_view where cmte_id='" + comm_id + "' order by rpt_type_order")
            for row in cursor.fetchall():
                #forms_obj.append(data_row)
                data_row = list(row)
                for idx,elem in enumerate(row):
                    if not elem:
                        data_row[idx]=''
                    if type(elem)==datetime.date:
                        data_row[idx] = elem.strftime("%m-%d-%Y")
                forms_obj.append({"report_type":data_row[0],"rpt_type_desc":data_row[1],"regular_special_report_ind":data_row[2],"rpt_type_info":data_row[3],"cvg_start_date":data_row[4],"cvg_end_date":data_row[5],"due_date":data_row[6]})
                
        if len(forms_obj)== 0:
            return Response("No entries were found for this committee", status=status.HTTP_201_OK)                              
        #for form_obj in forms_obj:
        #    if form_obj['due_date']:
        #        form_obj['due_date'] = form_obj['due_date'].strftime("%m-%d-%Y")
            
        #resp_data = [{k:v.strip(" ") for k,v in form_obj.items() if k not in ["_state"] and type(v) == str } for form_obj in forms_obj]
        return Response(forms_obj, status=status.HTTP_200_OK)
    except:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

"""


@api_view(['GET'])
def get_transaction_categories(request):

    try:
        with connection.cursor() as cursor:
            cursor.execute("select transaction_category_json from transaction_category_json_view where form_type='F3X'")
            for row in cursor.fetchall():
                #forms_obj.append(data_row)
                data_row = list(row)
                for idx,elem in enumerate(row):
                    if not elem:
                        data_row[idx]=''
                forms_obj=data_row[0]
                
        if forms_obj is None:
            return Response("No entries were found for this committee", status=status.HTTP_201_OK)                              
        
        return Response(forms_obj, status=status.HTTP_200_OK)
    except:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_special_report_types(request):

    try:
        with connection.cursor() as cursor:

            report_year = datetime.datetime.now().strftime('%Y')
            cmte_id = request.user.username

            query_string = """WITH duedate_by_report as ( 
                                with duedate as (
                                select
                                report_type,
                                election_state,
                                json_agg(
                                    json_build_object('election_date,',election_date,'cvg_start_date', cvg_start_date,'cvg_end_date', cvg_end_date,'due_date',due_date)) as   dates
                                                                from (select distinct report_type,election_state,election_date,cvg_start_date, cvg_end_date,due_date  from due_dates where report_year=""" + report_year + """) t
                                group by 
                                report_type,
                                election_state
                                order by 1,2)

                                select 
                                report_type,
                                json_agg(
                                json_build_object('state',election_state,'dates',dates)) as json_by_state
                                from duedate group by report_type)

                                select
                                '{ "report_type":' ||
                                json_agg(
                                json_build_object(
                                'report_type',duedate_by_report.report_type,
                                'report_type_desciption',rrt.rpt_type_desc,
                                'report_type_info',rrt.rpt_type_info,
                                'regular_special_report_ind',rrt.regular_special_report_ind,
                                'election_state',json_by_state) ORDER BY rrt.rpt_type_order)||'}' as report_types
                                from duedate_by_report 

                                join ref_rpt_types rrt on duedate_by_report.report_type=rrt.rpt_type 

                                join cmte_report_types_view cr on cr.report_type=duedate_by_report.report_type

                                where cmte_id='""" + cmte_id + """' and form_type='F3X';"""
            
            cursor.execute(query_string)

            for row in cursor.fetchall():
                #forms_obj.append(data_row)
                data_row = list(row)
                for idx,elem in enumerate(row):
                    if not elem:
                        data_row[idx]=''
                forms_obj=data_row[0]
                d = json.loads(forms_obj)
                
        if forms_obj is None:
            return Response("No entries were found for this committee", status=status.HTTP_201_OK)                              
        
        return JsonResponse(d, status=status.HTTP_200_OK, safe=False)
    except:
       return Response({}, status=status.HTTP_404_NOT_FOUND)

