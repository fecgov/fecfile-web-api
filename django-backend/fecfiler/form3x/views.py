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
from datetime import datetime

# Create your views here.

logger = logging.getLogger(__name__)

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
            cursor.execute("select report_type,rpt_type_desc,regular_special_report_ind,rpt_type_info, cvg_start_date,cvg_end_date,due_date from public.cmte_report_types_view where cmte_id='" + comm_id + "' order by rpt_type_order")
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
            return Response("No entries were found for this committee", status=status.HTTP_400_BAD_REQUEST)	                            
        #for form_obj in forms_obj:
        #    if form_obj['due_date']:
        #        form_obj['due_date'] = form_obj['due_date'].strftime("%m-%d-%Y")
            
        #resp_data = [{k:v.strip(" ") for k,v in form_obj.items() if k not in ["_state"] and type(v) == str } for form_obj in forms_obj]
        return Response(forms_obj, status=status.HTTP_200_OK)
    except:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_transaction_categories(request):

    try:
        with connection.cursor() as cursor:
            form_type = request.query_params.get('form_type')
            cursor.execute("select transaction_category_json from transaction_category_json_view where form_type='"+ form_type +"'")
            for row in cursor.fetchall():
                #forms_obj.append(data_row)
                data_row = list(row)
                for idx,elem in enumerate(row):
                    if not elem:
                        data_row[idx]=''
                forms_obj=data_row[0]
                
        if forms_obj is None:
            return Response("No entries were found for this committee", status=status.HTTP_400_BAD_REQUEST)                              
        
        return Response(forms_obj, status=status.HTTP_200_OK)
    except:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_report_types(request):

    try:
        with connection.cursor() as cursor:

            #report_year = datetime.datetime.now().strftime('%Y')
            cmte_id = request.user.username
            form_type = request.query_params.get('form_type')

            query_string = """select report_types_json From public.report_type_and_due_dates_view where cmte_id='""" + cmte_id + """' and form_type='""" + form_type + """';"""
            
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
            return Response("No entries were found for this committee", status=status.HTTP_400_BAD_REQUEST)                              
        
        return JsonResponse(d, status=status.HTTP_200_OK, safe=False)
    except:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_f3x_transaction_fields(request):

    try:
        with connection.cursor() as cursor:

            #report_year = datetime.datetime.now().strftime('%Y')
            cmte_id = request.user.username
            form_type = request.query_params.get('form_type')
            transaction_type = request.query_params.get('transaction_type')

            query_string = """select report_types_json From public.report_type_and_due_dates_view where cmte_id='""" + cmte_id + """' and form_type='""" + form_type + """';"""
            
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
            return Response("No entries were found for this committee", status=status.HTTP_400_BAD_REQUEST)                              
        
        return JsonResponse(d, status=status.HTTP_200_OK, safe=False)
    except:
        return Response({}, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST','GET','DELETE','PUT'])
def reports(request):

    #insert a new record for reports table
    if request.method == 'POST':

        try:
            forms_obj = []
            with connection.cursor() as cursor: 

                #report_year = datetime.datetime.now().strftime('%Y')
                cmte_id = request.user.username
                form_type = request.data.get('form_type')

                if not (form_type in ["F3X",]):
                    return Response("Form Type is not correctly specified. Input received is: {}".format(form_type), status=status.HTTP_404_NOT_FOUND)
                cvg_start_dt = datetime.strptime(request.data.get('cvg_start_dt'), '%Y-%m-%d').date()
                cvg_end_dt = datetime.strptime(request.data.get('cvg_end_dt'), '%Y-%m-%d').date()

                query_string = """SELECT report_id, cvg_start_date, cvg_end_date FROM public.reports WHERE cmte_id='""" + cmte_id + """' and form_type='""" + form_type + """' AND delete_ind is distinct from 'Y'"""
                
                cursor.execute(query_string)
                #print(query_string)

                for row in cursor.fetchall():
                    
                    if (row[1] <= cvg_end_dt and row[2] >= cvg_start_dt):

                        #print("it entered if loop")
                        
                        forms_obj.append({"report_id":row[0],"cvg_start_date":row[1],"cvg_end_date":row[2]})                
            
            #print(len(forms_obj))        
            if len(forms_obj)== 0:
                #print("okay")
                with connection.cursor() as cursor:
     
                    cursor.execute("""SELECT nextval('report_id_seq')""")
                    report_ids = cursor.fetchone()
                    report_id = report_ids[0]

                    #print(report_id)

                if 'amend_ind' in request.data:
                    amend_ind = request.data.get('amend_ind')
                else:
                    amend_ind = "N"

                if 'election_code' in request.data:
                    election_code = request.data.get('election_code')
                else:
                    election_code = None

                data = {
                    'report_id': report_id,
                    'cmte_id': cmte_id,
                    'form_type': form_type,
                    'amend_ind': amend_ind,
                    'report_type': request.data.get('report_type'),
                    'election_code': election_code,
                    'date_of_election': request.data.get('date_of_election'),
                    'state_of_election': request.data.get('state_of_election'),
                    'cvg_start_dt': request.data.get('cvg_start_dt'),
                    'cvg_end_dt': request.data.get('cvg_end_dt'),
                    'coh_bop': int(request.data.get('coh_bop')),
                }

                #print(data)
                with connection.cursor() as cursor:

                    try:

                        # Insert data into Reports table
                        cursor.execute("""INSERT INTO public.reports (report_id, cmte_id, form_type, amend_ind, report_type, cvg_start_date, cvg_end_date)
                                            VALUES (%s,%s,%s,%s,%s,%s,%s)""",(data.get('report_id'), data.get('cmte_id'), data.get('form_type'), data.get('amend_ind'), data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt')))                       
                    
                    except Exception as e:

                        cursor.execute("""SELECT setval('report_id_seq', """ + str(report_id) +""", false)""")

                        logger.debug(e)
                        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

                with connection.cursor() as cursor:

                    try:

                        #Insert data into Form 3X table
                        if data.get('form_type') == "F3X":

                            cursor.execute("""INSERT INTO public.form_3x (report_id, cmte_id, form_type, amend_ind, report_type, election_code, date_of_election, state_of_election, cvg_start_dt, cvg_end_dt, coh_bop)
                                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(data.get('report_id'), data.get('cmte_id'), data.get('form_type'), data.get('amend_ind'), data.get('report_type'), data.get('election_code'), data.get('date_of_election'), data.get('state_of_election'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('coh_bop')))               
                
                        
                    except Exception as e:

                        cursor.execute("""DELETE FROM public.reports WHERE report_id = '""" + str(report_id) + """'""")
                        cursor.execute("""SELECT setval('report_id_seq', """ + str(report_id) +""", false)""")

                        logger.debug(e)
                        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


                return JsonResponse(data, status=status.HTTP_201_CREATED)
            
            else:

                return JsonResponse(forms_obj, status=status.HTTP_400_BAD_REQUEST, safe=False)

        except:
            return Response("crud_reports-POST call is throwing an exception", status=status.HTTP_404_NOT_FOUND)


    #Get records from reports table
    if request.method == 'GET':
        try:
            cmte_id = request.user.username

            forms_obj = None
            with connection.cursor() as cursor:

                query_string = query_string = """SELECT report_id, cmte_id, form_type, report_type, amend_ind, amend_number, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, create_date, last_update_date
                                                    FROM public.reports WHERE cmte_id ='""" + cmte_id + """' AND delete_ind is distinct from 'Y'"""
                failed_response = "No entries were found for this committee"

                if 'report_id' in request.query_params:
                    try:
                        report_id = request.query_params.get('report_id')
                        check_report_id = int(request.query_params.get('report_id'))

                        query_string = """SELECT report_id, cmte_id, form_type, report_type, amend_ind, amend_number, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, create_date, last_update_date 
                                            FROM public.reports WHERE cmte_id='""" + cmte_id + """' AND delete_ind is distinct from 'Y' AND report_id='""" + report_id + """'"""
                        failed_response = "No entries were found for the report id: " + report_id + " for this committee" 

                    except ValueError:
                        query_string = query_string

                cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t;""")

                for row in cursor.fetchall():
                #forms_obj.append(data_row)
                    data_row = list(row)
                    for idx,elem in enumerate(row):
                        if not elem:
                            data_row[idx]=''
                    forms_obj=data_row[0]
                
            if len(forms_obj)== 0:
                return Response(failed_response, status=status.HTTP_400_BAD_REQUEST)

            else:
                return JsonResponse(forms_obj, status=status.HTTP_200_OK, safe=False)
        except:
            return Response("crud_reports-GET call is throwing an exception", status=status.HTTP_404_NOT_FOUND)


    if request.method == 'PUT':

        try:
            forms_obj = []
            with connection.cursor() as cursor: 

                #report_year = datetime.datetime.now().strftime('%Y')
                cmte_id = request.user.username
                form_type = request.data.get('form_type')
                if not (form_type in ["F3X",]):
                    return Response("Form Type is not correctly specified. Input received is: {}".format(form_type), status=status.HTTP_404_NOT_FOUND)
                cvg_start_dt = datetime.strptime(request.data.get('cvg_start_dt'), '%Y-%m-%d').date()
                cvg_end_dt = datetime.strptime(request.data.get('cvg_end_dt'), '%Y-%m-%d').date()
                report_id = request.data.get('report_id')

                try:
                    check_report_id = int(request.data.get('report_id'))
                except ValueError:
                    return Response("Report ID provided is not an Integer", status=status.HTTP_400_BAD_REQUEST)

                query_string = """SELECT report_id, cvg_start_date, cvg_end_date FROM public.reports WHERE cmte_id='""" + cmte_id + """' AND form_type='""" + form_type + """' AND delete_ind is distinct from 'Y'"""
                
                cursor.execute(query_string)
                #print(query_string)

                for row in cursor.fetchall():
                    
                    if ((row[1] <= cvg_end_dt and row[2] >= cvg_start_dt) and int(report_id) != row[0]):

                        forms_obj.append({"report_id":row[0],"cvg_start_date":row[1],"cvg_end_date":row[2]})                
            
            #print(len(forms_obj))        
            if len(forms_obj)== 0:
                
                if 'amend_ind' in request.data:
                    amend_ind = request.data.get('amend_ind')
                else:
                    amend_ind = "N"

                if 'election_code' in request.data:
                    election_code = request.data.get('election_code')
                else:
                    election_code = None

                data = {
                    'report_id': report_id,
                    'cmte_id': cmte_id,
                    'form_type': form_type,
                    'amend_ind': amend_ind,
                    'report_type': request.data.get('report_type'),
                    'election_code': election_code,
                    'date_of_election': request.data.get('date_of_election'),
                    'state_of_election': request.data.get('state_of_election'),
                    'cvg_start_dt': request.data.get('cvg_start_dt'),
                    'cvg_end_dt': request.data.get('cvg_end_dt'),
                    'coh_bop': int(request.data.get('coh_bop')),
                }

                with connection.cursor() as cursor:

                    cursor.execute("""SELECT report_type, cvg_start_date, cvg_end_date FROM public.reports WHERE report_id = '""" + data.get('report_id') + """' AND delete_ind is distinct from 'Y'""")
                    row = cursor.fetchone()
                    if not (row is None):
                        prev_report_type = row[0]
                        prev_cvg_start_dt = row[1]
                        prev_cvg_end_dt = row[2]
                    #print(row)
                with connection.cursor() as cursor:

                    try:

                        cursor.execute("""UPDATE public.reports SET report_type = %s, cvg_start_date = %s, cvg_end_date = %s WHERE report_id = %s AND delete_ind is distinct from 'Y'""",
                                            (data.get('report_type'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('report_id')))

                        if (cursor.rowcount == 0):
                            return Response("This Report ID does not exist in Reports table", status=status.HTTP_400_BAD_REQUEST)

                    except Exception as e:

                        logger.debug(e)
                        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


                if data.get('form_type') == "F3X":
                    
                    with connection.cursor() as cursor:

                        try:

                            cursor.execute("""UPDATE public.form_3x SET report_type = %s, election_code = %s, date_of_election = %s, state_of_election = %s, cvg_start_dt = %s, cvg_end_dt = %s, coh_bop = %s WHERE report_id = %s AND delete_ind is distinct from 'Y'""",
                                                (data.get('report_type'), data.get('election_code'), data.get('date_of_election'), data.get('state_of_election'), data.get('cvg_start_dt'), data.get('cvg_end_dt'), data.get('coh_bop'), data.get('report_id')))
                            
                            if (cursor.rowcount == 0):
                                cursor.execute("""UPDATE public.reports SET report_type = %s, cvg_start_date = %s, cvg_end_date = %s WHERE report_id = %s AND delete_ind is distinct from 'Y'""",
                                                    (prev_report_type, prev_cvg_start_dt, prev_cvg_end_dt, data.get('report_id')))
                                return Response("This Report ID does not exist in Form 3X table", status=status.HTTP_400_BAD_REQUEST)

                        except Exception as e:

                            cursor.execute("""UPDATE public.reports SET report_type = %s, cvg_start_date = %s, cvg_end_date = %s WHERE report_id = %s AND delete_ind is distinct from 'Y'""",
                                                    (prev_report_type, prev_cvg_start_dt, prev_cvg_end_dt, data.get('report_id')))
                            logger.debug(e)
                            return Response(str(e), status=status.HTTP_400_BAD_REQUEST) 
                            
                return JsonResponse(data, status=status.HTTP_201_CREATED)
            
            else:

                return JsonResponse(forms_obj, status=status.HTTP_400_BAD_REQUEST, safe=False)
        except:
            return Response("crud_reports-PUT call is throwing an exception", status=status.HTTP_404_NOT_FOUND) 


    if request.method == 'DELETE':

        try:

            report_id = request.query_params.get('report_id')
            form_type = request.query_params.get('form_type')
            if not (form_type in ["F3X",]):
                    return Response("Form Type is not correctly specified. Input received is: {}".format(form_type), status=status.HTTP_404_NOT_FOUND)

            try:
                check_report_id = int(report_id)
            except ValueError:
                return Response("Report ID provided is not an Integer", status=status.HTTP_400_BAD_REQUEST)

            with connection.cursor() as cursor:

                try:

                    cursor.execute("""UPDATE public.reports SET delete_ind = 'Y' WHERE report_id = '""" + report_id + """' AND delete_ind is distinct from 'Y'""")

                    if (cursor.rowcount == 0):
                        return Response("This Report ID is either already deleted or does not exist in Reports table", status=status.HTTP_400_BAD_REQUEST)

                except Exception as e:

                    logger.debug(e)
                    return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


            if form_type == "F3X":
                
                with connection.cursor() as cursor:

                    try:

                        cursor.execute("""UPDATE public.form_3x SET delete_ind = 'Y' WHERE report_id = '""" + report_id + """'AND delete_ind is distinct from 'Y'""")

                        if (cursor.rowcount == 0):

                            delete_ind = None
                            cursor.execute("""UPDATE public.reports SET delete_ind = %s WHERE report_id = %s""", (delete_ind, report_id))

                            return Response("This Report ID is either already deleted or does not exist in Form 3X table", status=status.HTTP_400_BAD_REQUEST)

                    except Exception as e:

                        delete_ind = None
                        cursor.execute("""UPDATE public.reports SET delete_ind = %s WHERE report_id = %s""", (delete_ind, report_id))
                        logger.debug(e)
                        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

            return Response("The Report with ID: {} has been successfully deleted".format(report_id),status=status.HTTP_201_CREATED)

        except:

            return Response("crud_reports-DELETE call is throwing an exception", status=status.HTTP_404_NOT_FOUND) 