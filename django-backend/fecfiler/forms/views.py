from django.shortcuts import render

from rest_framework.decorators import api_view
import maya
import pytz
#from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .models import CommitteeInfo, Committee, CommitteeMaster, RefFormTypes, My_Forms_View
from .serializers import CommitteeInfoSerializer, CommitteeSerializer, CommitteeInfoListSerializer
import json
import os
import requests
from django.views.decorators.csrf import csrf_exempt
import logging
import datetime
import magic
import pdfrw
from django.http import JsonResponse, HttpResponse, FileResponse
import fecfiler
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.template.loader import render_to_string
from django.template import Context, Template
import PyPDF2
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from PyPDF2.generic import BooleanObject, NameObject, IndirectObject
import urllib
from django.db import connection
import boto
from boto.s3.key import Key
from fecfiler.core.views import NoOPError, get_levin_accounts, get_comittee_id

#import datetime as dt

# API view functionality for GET DELETE and PUT
# Exception handling is taken care to validate the committeinfo
from ..authentication.authorization import is_read_only_or_filer_submit, is_read_only_or_filer_reports, is_not_read_only_or_filer

logger = logging.getLogger(__name__)

# API which prints Form 99 data
@api_view(['POST'])
def print_pdf_info(request):
    """
    Creates a new CommitteeInfo Object, or updates the last created CommitteeInfo object created for that committee.
    """
    # Configuration values
    ANNOT_KEY = '/Annots'
    ANNOT_FIELD_KEY = '/T'
    ANNOT_VAL_KEY = '/V'
    ANNOT_RECT_KEY = '/Rect'
    SUBTYPE_KEY = '/Subtype'
    WIDGET_SUBTYPE_KEY = '/Widget'

    input_pdf_path = 'templates/forms/F99.pdf'
    output_pdf_path = 'templates/forms/media/%s.pdf' %request.data.get('id')

    #code to generate form 99 using form99 template
    template_pdf = pdfrw.PdfReader(input_pdf_path)
    annotations = template_pdf.pages[0][ANNOT_KEY]
    for annotation in annotations:
        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
            if annotation[ANNOT_FIELD_KEY]:
                key = annotation[ANNOT_FIELD_KEY][1:-1]
                if key == "IMGNO":
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(request.data.get('id')))
                    )
                if key == "FILING_TIMESTAMP":
                    date = datetime.datetime.now().strftime('%Y%m%d')
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(date))
                    )
                if key == "PAGESTR":
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format("1 of 1"))
                    )
                if key == "COMMITTEE_NAME":
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(request.data.get('committeename')))
                    )
                if key == "FILER_FEC_ID_NUMBER":
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(request.data.get('committeeid')))
                    )
                if key == "STREET_1":
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(request.data.get('street1')))
                    )
                if key == "STREET_2":
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(request.data.get('street2')))
                    )
                if key == "CITY":
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(request.data.get('city')))
                    )
                if key == "STATE":
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(request.data.get('state')))
                    )
                if key == "ZIP":
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(request.data.get('zipcode')))
                    )
                if key == "FREE_FORMAT_TEXT":
                    annotation.update(
                        pdfrw.PdfDict(V='{}'.format(request.data.get('text')))
                    )
    pdfrw.PdfWriter().write(output_pdf_path, template_pdf)

    response = FileResponse(open(output_pdf_path, 'rb'), content_type='application/pdf')
    response['content-Disposition'] = 'inline; filename = {}_Form99_Preview.pdf'.format(request.data.get('committeeid'))
    """f = open(output_pdf_path, 'rb')
    pdf_contents = f.read()
    f.close()
    response = HttpResponse(pdf_contents, content_type='application/pdf')
    response['content-Disposition'] = 'inline; filename = {}.pdf'.format(request.data.get('id'))"""
    return response

# API to create a .fec which can be used on webprint module to print pdf. The data being used is the data that was last saved in the database for f99.
"""@api_view(['GET'])
def print_f99_info(request):

    
    #Fetches the last unsubmitted comm_info object saved in db and creates a .fec file which is used as input to print form99 in webprint module.
    
    try: 
        # fetch last comm_info object created that is not submitted, else return None
        comm_info = CommitteeInfo.objects.filter(committeeid=get_comittee_id(request.user.username),  is_submitted=False).last() #,)

    except CommitteeInfo.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND) #status=status.HTTP_404_NOT_FOUND)

    file_name = "%s.fec" %comm_info.id
    with open(file_name, "w") as text_file:
        text_file.write("HDRFEC8.3FECfile8.3.0.0(f32)F99")
        text_file.write("%s" %comm_info.committeeid)
        text_file.write("%s" %comm_info.committeename)
        text_file.write("%s" %comm_info.street1)
        text_file.write("%s" %comm_info.street2)
        text_file.write("%s" %comm_info.city)
        text_file.write("%s" %comm_info.state)
        text_file.write("%s" %comm_info.zipcode)
        text_file.write("%s" %comm_info.treasurerlastname)
        text_file.write("%s" %comm_info.treasurerfirstname)
        text_file.write("%s" %comm_info.zipcode)
        date = comm_info.created_at.strftime('%Y%m%d')
        text_file.write("%s" %date)
        text_file.write("%s" %comm_info.reason)
        text_file.write("[BEGINTEXT]")
        text_file.write("%s" %comm_info.zipcode)
        text_file.write("[ENDTEXT]")

    # get details of a single comm_info
    if request.method == 'GET':
        if comm_info:
            serializer = CommitteeInfoSerializer(comm_info)
            return Response(status=status.HTTP_201_CREATED)    
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)    
"""
@api_view(['GET'])
def fetch_f99_info(request):
    """"
    Fetches the last unsubmitted comm_info object saved in db. This obviously is for the object persistence between logins.
    """
    #import ipdb; ipdb.set_trace()
    try:
        # fetch last comm_info object created that is not submitted, else return None
        comm_info = CommitteeInfo.objects.filter(committeeid=get_comittee_id(request.user.username),  is_submitted=False).last() #,)
    except CommitteeInfo.DoesNotExist:
        return Response({}) #status=status.HTTP_404_NOT_FOUND)

    # get details of a single comm_info
    if request.method == 'GET':
        if comm_info:
            serializer = CommitteeInfoSerializer(comm_info)
            return Response(serializer.data)
        else:
            return Response({})

parser_classes = (MultiPartParser, FormParser)

@api_view(['POST'])
def create_f99_info(request):
    """
    Creates a new CommitteeInfo Object, or updates the last created CommitteeInfo object created for that committee.
    """
    # insert a new record for a comm_info
    if request.method == 'POST':
        
        data = {
            'committeeid': request.data.get('committeeid'),
            'committeename': request.data.get('committeename'),
            'street1': request.data.get('street1'),
            'street2': request.data.get('street2'),
            'city': request.data.get('city'),
            'state': request.data.get('state'),
            'text': request.data.get('text'),
            #'reason' :request.data.get('text'),
            'reason' :request.data.get('reason'),
            'zipcode': request.data.get('zipcode'),
            'treasurerlastname': request.data.get('treasurerlastname'),
            'treasurerfirstname': request.data.get('treasurerfirstname'),
            'treasurermiddlename': request.data.get('treasurermiddlename'),
            'treasurerprefix': request.data.get('treasurerprefix'),
            'treasurersuffix': request.data.get('treasurersuffix'),
            'is_submitted': request.data.get('is_submitted'),
            'signee': request.data.get('signee'),
            'email_on_file' : request.data.get('email_on_file'),
            'email_on_file_1': request.data.get('email_on_file_1'),

            'additional_email_1' : request.data.get('additional_email_1'),
            'additional_email_2': request.data.get('additional_email_2'),
            'file': request.data.get('file'),
            'form_type': request.data.get('form_type'),
            'coverage_start_date': request.data.get('coverage_start_date'),
            'coverage_end_date': request.data.get('coverage_end_date'),
        }
        #import ipdb; ipdb.set_trace()

        """

        if 'file' in request.data:
            data['filename'] = request.data.get('file').name

        serializer = CommitteeInfoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        """
        logger.debug("Incoming parameters: create_f99_info" + str(request.data))
        incoming_data = data
        #import ipdb; ipdb.set_trace()
        # overwrite is_submitted just in case user sends it, all submit changes to go via submit_comm_info api as we save to s3 and call fec api.

        #if not(incoming_data['is_submitted'] in['False',False,'false'] and incoming_data['committeeid'] == get_comittee_id(request.user.username)):
            #logger.debug("FEC Error 001:is_submitted and committeeid field changes are restricted for this api call. Please use the submit api to finalize and submit the data")
            #return Response({"FEC Error 001":"is_submitted and committeeid field changes are restricted for this api call. Please use the submit api to finalize and submit the data"}, status=status.HTTP_400_BAD_REQUEST)
        # just making sure that committeeid is not updated by mistake
        
        print("Reason text= ", request.data.get('text'))
        strcheck_Reason=check_F99_Reason_Text(request.data.get('text'))

        print ("strcheck_Reason", strcheck_Reason)
        if strcheck_Reason != "":
           return Response({"FEC Error 999":"The reason text is not in proper format - HTML tag violation...!"}, status=status.HTTP_400_BAD_REQUEST)


        if 'file' in request.data:
            incoming_data['filename'] = request.data.get('file').name

        #try:
            #import ipdb; ipdb.set_trace()
            # fetch last comm_info object created, else return 404
        try:
            if 'id' in request.data and (not request.data['id']==''):
                if int(request.data['id'])>=1:
                    id_comm = CommitteeInfo()
                    id_comm.id = request.data['id']
                    comm_info = CommitteeInfo.objects.filter(id=id_comm.id).last()
                    if comm_info:
                        if comm_info.is_submitted==False:
                            #print(comm_info.created_at)
                            incoming_data['created_at'] = comm_info.created_at
                            id_comm.created_at = comm_info.created_at
                            comm_info.delete()
                            id_comm.updated_at = datetime.datetime.now()
                            if incoming_data['additional_email_2'] in [None, "", " "]:
                                incoming_data['additional_email_2'] = None
                            if incoming_data['additional_email_1'] in [None, "", " "]:
                                incoming_data['additional_email_1'] = None
                            """if not 'file' in request.data:
                                if not comm_info.file is None:
                                    del incoming_data['file']
                                    del incoming_data['filename']
                            """
                            serializer = CommitteeInfoSerializer(id_comm, data=incoming_data)
                        else:
                            logger.debug("FEC Error 002:This form is already submitted")
                            return Response({"FEC Error 002":"This form is already submitted"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        logger.debug("FEC Error 003:This form Id number does not exist")
                        return Response({"FEC Error 003":"This form Id number does not exist"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    incoming_data['created_at'] = datetime.datetime.now()
                    incoming_data['updated_at'] = incoming_data['created_at']
                    serializer = CommitteeInfoSerializer(data=incoming_data)
            else:
                incoming_data['created_at'] = datetime.datetime.now()
                incoming_data['updated_at'] = incoming_data['created_at']
                serializer = CommitteeInfoSerializer(data=incoming_data)
        except CommitteeInfo.DoesNotExist:
            logger.debug("FEC Error 004:There is no unsubmitted data. Please create f99 form object before submitting")
            return Response({"FEC Error 004":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            logger.debug("FEC Error 006:This form Id number is not an integer")
            return Response({"FEC Error 006":"This form Id number is not an integer"}, status=status.HTTP_400_BAD_REQUEST)
        #except:
            #logger.
            #return Response({"error":"An unexpected error occurred" + str(sys.exc_info()[0]) + ". Please contact administrator"}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            if is_not_read_only_or_filer(request):
                if is_not_read_only_or_filer:
                    serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
         
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
"""
@api_view(['POST'])
#class f99_file_upload(APIView):
    #parser_class = (FileUploadParser,)

def f99_file_upload(self, request, format=None):
    import ipdb; ipdb.set_trace()
    if 'file' not in request.data:
        raise ParseError("Empty content")

    f = request.data['file']
    #import ipdb; ipdb.set_trace()
    
    mymodel.my_file_field.save(f.name, f, save=True)
    return Response(status=status.HTTP_201_CREATED)
"""
@api_view(['POST'])
def update_f99_info(request, print_flag=False):
    try:
        is_read_only_or_filer_reports(request)

        if request.method == 'POST':
            try:
                if 'id' in request.data and (not request.data['id']=='') and int(request.data['id'])>=1:
                    comm_info = CommitteeInfo.objects.filter(id=request.data['id']).last()
                    print(request.data.get('email_on_file_1'))
                    print(comm_info.email_on_file_1)

                    if comm_info:
                        if comm_info.is_submitted==False:
                            comm_info.committeeid =  request.data.get('committeeid')
                            comm_info.committeename = request.data.get('committeename')
                            comm_info.street1 = request.data.get('street1')
                            comm_info.street2 = request.data.get('street2')
                            comm_info.city = request.data.get('city')
                            comm_info.state = request.data.get('state')
                            comm_info.text = request.data.get('text')
                            comm_info.reason = request.data.get('reason')
                            comm_info.zipcode = request.data.get('zipcode')
                            comm_info.treasurerlastname = request.data.get('treasurerlastname')
                            comm_info.treasurerfirstname = request.data.get('treasurerfirstname')
                            comm_info.treasurermiddlename = request.data.get('treasurermiddlename')
                            comm_info.treasurerprefix = request.data.get('treasurerprefix')
                            comm_info.treasurersuffix = request.data.get('treasurersuffix')
                            comm_info.is_submitted = request.data.get('is_submitted')
                            try:
                                comm_info.filename = request.data.get('file').name
                                comm_info.file = request.data.get('file')
                            except:
                                pass
                            comm_info.form_type = request.data.get('form_type')
                            comm_info.coverage_start_date = request.data.get('coverage_start_date')
                            comm_info.coverage_end_date = request.data.get('coverage_end_date')
                            comm_info.signee = request.data.get('signee')
                            comm_info.email_on_file = request.data.get('email_on_file')
                            comm_info.email_on_file_1 = request.data.get('email_on_file_1')
                            comm_info.additional_email_1 = request.data.get('additional_email_1')
                            comm_info.additional_email_2 = request.data.get('additional_email_2')
                            comm_info.updated_at = datetime.datetime.now()
                            comm_info.save()
                            result = CommitteeInfo.objects.filter(id=request.data['id']).last()
                            if result:
                                serializer = CommitteeInfoSerializer(result)
                                return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
                            else:
                                return Response({})
                        else:
                            if print_flag:
                                result = CommitteeInfo.objects.filter(id=request.data['id']).last()
                                if result:
                                    serializer = CommitteeInfoSerializer(result)
                                    return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
                                else:
                                    return Response({})
                            else:
                                logger.debug("FEC Error 002:This form is already submitted")
                                return Response({"FEC Error 002":"This form is already submitted"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        logger.debug("FEC Error 003:This form Id number does not exist")
                        return Response({"FEC Error 003":"This form Id number does not exist"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    print('new id is created')
                    #create_f99_info(request)
            except CommitteeInfo.DoesNotExist:
                logger.debug("FEC Error 004:There is no unsubmitted data. Please create f99 form object before submitting")
                return Response({"FEC Error 004":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)

            except ValueError:
                logger.debug("FEC Error 006:This form Id number is not an integer")
                return Response({"FEC Error 006":"This form Id number is not an integer"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)

    """   
    #Updates the last unsubmitted comm_info object only. you can use this to change the 'text' and 'is_submitted' field as well as any other field.
    
    # update details of a single comm_info
    if request.method == 'POST':

        try:
            #import ipdb; ipdb.set_trace()
            # fetch last comm_info object created, else return 404
            try:

                id_comm = CommitteeInfo()
                id_comm.id = request.data['id']
                comm_info = CommitteeInfo.objects.filter(id=id_comm.id, is_submitted=False).last()

                comm_info.delete()
            except CommitteeInfo.DoesNotExist:
                return Response({"error":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)
        except:
            #logger.
            return Response({"error":"An unexpected error occurred" + str(sys.exc_info()[0]) + ". Please contact administrator"}, status=status.HTTP_400_BAD_REQUEST)

        incoming_data = request.data
        #import ipdb; ipdb.set_trace()
        # overwrite is_submitted just in case user sends it, all submit changes to go via submit_comm_info api as we save to s3 and call fec api.

        if not(incoming_data['is_submitted'] in['False',False,'false'] and incoming_data['committeeid'] == get_comittee_id(request.user.username)):
            return Response({"error":"is_submitted and committeeid field changes are restricted for this api call. Please use the submit api to finalize and submit the data"}, status=status.HTTP_400_BAD_REQUEST)
        # just making sure that committeeid is not updated by mistake

        if 'file' in request.data:
            incoming_data['filename'] = request.data.get('file').name

                
        serializer = CommitteeInfoSerializer(id_comm, data=incoming_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
         
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    """
@api_view(['POST'])
def submit_comm_info(request):
    if request.method == 'POST':
        try:
            is_read_only_or_filer_reports(request)
        
            data = {
                'committeeid': request.data.get('committeeid'),
                'committeename': request.data.get('committeename'),
                'street1': request.data.get('street1'),
                'street2': request.data.get('street2'),
                'city': request.data.get('city'),
                'state': request.data.get('state'),
                'text': request.data.get('text'),
                #'reason' :request.data.get('text'),
                'reason' :request.data.get('reason'),
                'zipcode': request.data.get('zipcode'),
                'treasurerlastname': request.data.get('treasurerlastname'),
                'treasurerfirstname': request.data.get('treasurerfirstname'),
                'treasurermiddlename': request.data.get('treasurermiddlename'),
                'treasurerprefix': request.data.get('treasurerprefix'),
                'treasurersuffix': request.data.get('treasurersuffix'),

                'signee': request.data.get('signee'),
                'email_on_file' : request.data.get('email_on_file'),
                'email_on_file_1': request.data.get('email_on_file_1'),

                'additional_email_1' : request.data.get('additional_email_1'),
                'additional_email_2': request.data.get('additional_email_2'),
                'form_type': request.data.get('form_type'),
                'coverage_start_date': request.data.get('coverage_start_date'),
                'coverage_end_date': request.data.get('coverage_end_date'),

            }
            logger.debug("Incoming parameters: submit_comm_info" + str(request.data))
            incoming_data = data

            print("Reason text= ", request.data.get('text'))
            strcheck_Reason=check_F99_Reason_Text(request.data.get('text'))

            print ("strcheck_Reason", strcheck_Reason)
            if strcheck_Reason != "":
               return Response({"FEC Error 999":"The reason text is not in proper format - HTML tag violation...!"}, status=status.HTTP_400_BAD_REQUEST)


            #import ipdb; ipdb.set_trace()
            # overwrite is_submitted just in case user sends it, all submit changes to go via submit_comm_info api as we save to s3 and call fec api.

            #not(request.data['is_submitted'] in['True',True,'true'] and
            #if not incoming_data['committeeid'] == get_comittee_id(request.user.username):
                #return Response({"FEC Error 005":"is_submitted and committeeid field changes are restricted for this api call. Please use the create api to finalize or update the data"}, status=status.HTTP_400_BAD_REQUEST)
            # just making sure that committeeid is not updated by mistake
            try:
                comm_info = CommitteeInfo.objects.filter(id=request.data['id']).last()
                if comm_info:
                    if comm_info.is_submitted==False:
                        incoming_data['updated_at'] = datetime.datetime.now()
                        incoming_data['created_at'] = comm_info.created_at
                        comm_info.is_submitted=True
                        serializer = CommitteeInfoSerializer(comm_info, data=incoming_data)
                    else:
                        return Response({"FEC Error 002":"This form is already submitted"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"FEC Error 003":"This form Id number does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            except CommitteeInfo.DoesNotExist:
                return Response({"FEC Error 004":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                        return Response({"FEC Error 006":"This form Id number is not an integer"}, status=status.HTTP_400_BAD_REQUEST)

            if serializer.is_valid():
                serializer.save()
                email(True, serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            json_result = {'message': str(e)}
            return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)

    """
    Submits the last unsubmitted but saved comm_info object only. Returns the saved object with updated timestamp and comm_info details
    validate_api/s3 not being called currently
    #
    #import ipdb; ipdb.set_trace()
    if request.method == 'POST':
        try:
            comm_info = CommitteeInfo.objects.filter(committeeid=get_comittee_id(request.user.username)).last()
            #print(comm_info.pk)
            if comm_info:
                comm_info.is_submitted = True
                comm_info.updated_at = datetime.datetime.now()                
                serializer = CommitteeInfoSerializer(comm_info)                
                #if serializer.is_valid():
                #if True:
                comm_info.save()
                    
                email(True, serializer.data)
                return Response(serializer.data, status=status.HTTP_200_OK)
                #else:
                #    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)                    
        except:
            return Response({"error":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)

    else:
        return Response({"error":"ERRCODE: FEC02. Error occured while trying to submit form f99."}, status=status.HTTP_400_BAD_REQUEST)
    """
    
# @api_view(['POST'])
# def submit_comm_info(request):
#     """
#     Submits the last unsubmitted but saved comm_info object only. Returns the saved object with updated timestamp and comm_info details.Call the data_receive API and fetch the response
#     """
#     #import ipdb; ipdb.set_trace()
#     #if request.method == 'POST':
#     if request.method == 'POST':
#         try:
#             #import ipdb; ipdb.set_trace()
#             comm_info = CommitteeInfo.objects.filter(committeeid=get_comittee_id(request.user.username)).last()
#             if comm_info:

#                 comm_info.is_submitted=True
#                 comm_info.updated_at=datetime.datetime.now()
#                 comm_info.save()
#                 new_data = comm_info.__dict__
#                 serializer = CommitteeInfoSerializer(comm_info) #, data=new_data)
#                 if True: #serializer.is_valid():
#                     #serializer.save()

#                     # make temp file, stream it , and close
#                     try:
#                         tmp_filename = '/tmp/' + new_data['committeeid'] + "_" + 'f99' + new_data['updated_at'].strftime("%Y_%m_%d_%H_%M") + ".json"
#                         json.dump(serializer.data, open(tmp_filename, 'w'))

#                         f99_obj_to_s3 = {
#                             'committeeid': new_data['committeeid'],
#                             #'upload':open(tmp_filename, 'r')
#                         }
#                         resp = requests.post(fecfiler.settings.DATA_RECEIVE_API_URL + fecfiler.settings.DATA_RECEIVE_API_VERSION + "f99_data_receive", data=f99_obj_to_s3, files={'upload':open(tmp_filename,'r')})

#                         if not resp.ok:
#                             return Response(resp.json(), status=status.HTTP_400_BAD_REQUEST)

#                         # delete tmp file if exists
#                         try:
#                             os.remove(tmp_filename)
#                         except:
#                             pass

#                     except:
#                         try:
#                             os.remove(tmp_filename)
#                         except:
#                             pass

#                     return Response({'uploaded_file': resp.json(), 'obj_data':serializer.data}, status=status.HTTP_200_OK)
#                 else:
#                     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#             else:
#                 return Response({"error":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)
#         except:
#             return Response({"error":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)

#     else:
#         return Response({"error":"ERRCODE: FEC02. Error occured while trying to submit form f99."}, status=status.HTTP_400_BAD_REQUEST)

"""
@api_view(["POST"])
def create_json_file(request):
   
   #creating a JSON file so that it is handy for all the public API's
   
   try:
       tmp_filename = '/tmp/' + new_data['committeeid'] + "_" + 'f99' + new_data['updated_at'].strftime("%Y_%m_%d_%H_%M") + ".json"
       json.dump(serializer.data, open(tmp_filename, 'w'))

"""

@api_view(['GET'])
def get_f99_reasons(request):
    """
    Json object the resons for filing
    """
    if request.method == 'GET':
        try:
            from django.conf import settings
            reason_data = json.load(open(os.path.join(settings.BASE_DIR,'sys_data', 'f99_default_reasons.json'),'r'))
            return Response(reason_data, status=status.HTTP_200_OK)
        except:
            return Response({'error':'ERR_0001: Server Error: F99 reasons file not retrievable.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_committee_details(request):
    try:
        cmte_id = get_comittee_id(request.user.username)
        with connection.cursor() as cursor:
            # GET all rows from committee table
            query_string = """SELECT cm.cmte_id AS "committeeid", cm.cmte_name AS "committeename", cm.street_1 AS "street1", cm.street_2 AS "street2", 
                cm.city, cm.state, cm.zip_code AS "zipcode", 
                cm.cmte_email_1 AS "email_on_file", cm.cmte_email_2 AS "email_on_file_1", cm.phone_number, cm.cmte_type, cm.cmte_dsgn, 
                cm.cmte_filing_freq, cm.cmte_filed_type, 
                cm.treasurer_last_name AS "treasurerlastname", cm.treasurer_first_name AS "treasurerfirstname", cm.treasurer_middle_name AS "treasurermiddlename", 
                cm.treasurer_prefix AS "treasurerprefix", cm.treasurer_suffix AS "treasurersuffix", cm.create_date AS "created_at", cm.cmte_type_category, f1.fax, 
                f1.tphone as "treasurerphone", f1.url as "website", f1.email as "treasureremail"
                FROM public.committee_master cm
                LEFT JOIN public.form_1 f1 ON f1.comid=cmte_id
                WHERE cm.cmte_id = %s ORDER BY cm.create_date, f1.sub_date DESC, f1.create_date DESC LIMIT 1"""
            cursor.execute("""SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id])
            modified_output = cursor.fetchone()[0]
        if modified_output is None:
            raise NoOPError('The Committee ID: {} does not match records in Committee table'.format(cmte_id))
        #     for row in cursor.fetchone():
        #         # print(row)
        #         forms_obj=row[0]
        #         # print(forms_obj)
        # if forms_obj is None:
        #     raise NoOPError('The Committee: {} does not have any reports listed'.format(cmte_id))
        # else:
        #     modified_output = {"committeeid": forms_obj.get('cmte_id'),
        #                         "committeename": forms_obj.get('cmte_name'),
        #                         "street1": forms_obj.get('street_1'),
        #                         "street2": forms_obj.get('street_2'),
        #                         "city": forms_obj.get('city'),
        #                         "state": forms_obj.get('state'),
        #                         "zipcode": forms_obj.get('zip_code'),
        #                         "treasurerprefix": forms_obj.get('treasurer_prefix'),
        #                         "treasurerfirstname": forms_obj.get('treasurer_first_name'),
        #                         "treasurermiddlename": forms_obj.get('treasurer_middle_name'),
        #                         "treasurerlastname": forms_obj.get('treasurer_last_name'),
        #                         "treasurersuffix": forms_obj.get('treasurer_suffix'),
        #                         "email_on_file": forms_obj.get('cmte_email_1'),
        #                         "email_on_file_1": forms_obj.get('cmte_email_2'),
        #                         "phone_number": forms_obj.get('phone_number'),
        #                         "cmte_type": forms_obj.get('cmte_type'),
        #                         "cmte_dsgn": forms_obj.get('cmte_dsgn'),
        #                         "cmte_filing_freq": forms_obj.get('cmte_filing_freq'),
        #                         "cmte_filed_type": forms_obj.get('cmte_filed_type'),
        #                         "created_at": forms_obj.get('create_date')}
        levin_accounts = get_levin_accounts(cmte_id)
        modified_output[0]['levin_accounts'] = levin_accounts
        return Response(modified_output[0], status=status.HTTP_200_OK)
    except Exception as e:
        return Response("The get_committee_details API is throwing  an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_committee(request):
    """
    fields for auto populating the data for creating the comm_info object
    """
    try:
        comm = Committee.objects.filter(committeeid=get_comittee_id(request.user.username)).last()
    except Committee.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    # get details of a single comm
    if request.method == 'GET':
        serializer = CommitteeSerializer(comm)
        return Response(serializer.data)


@api_view(['GET'])
def get_signee(request):
    """
    Gets the signee for the commitee .
    """
    try:
        comm = Committee.objects.filter(committeeid=get_comittee_id(request.user.username)).last()
    except Committee.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    # get details of a single comm
    if request.method == 'GET':
        serializer = CommitteeSerializer(comm)
        filtered_d = {key: val for key, val in serializer.data.items() if key not in ['street1', 'street2', 'created_at','state','city','zipcode']}
        # FIXME: This is to be redone after there is a discussion on how to model data for the signatories of each committee.
        filtered_d['email'] = request.user.email
        return Response(filtered_d)


@api_view(['POST'])
def update_committee(request, cid):
    try:
        is_read_only_or_filer_reports(request)
        # # update details of a single comm
        if request.method == 'POST':
             serializer = CommitteeSerializer(comm, data=request.data)
             if serializer.is_valid():
                 serializer.save()
                 return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)
@api_view(['POST'])
def create_committee(request):
    # insert a new record for a committee
    try:
        is_read_only_or_filer_reports(request)
        if request.method == 'POST':
            data = {
                'committeeid': request.data.get('committeeid'),
                'committeename': request.data.get('committeename'),
                'street1': request.data.get('street1'),
                'street2': request.data.get('street2'),
                'city': request.data.get('city'),
                'state': request.data.get('state'),
                'zipcode': int(request.data.get('zipcode')),
                'treasurerlastname': request.data.get('treasurerlastname'),
                'treasurerfirstname': request.data.get('treasurerfirstname'),
                'treasurermiddlename': request.data.get('treasurermiddlename'),
                'treasurerprefix': request.data.get('treasurerprefix'),
                'treasurersuffix': request.data.get('treasurersuffix'),
                'email_on_file' : request.data.get('email_on_file'),
                'email_on_file_1' : request.data.get('email_on_file_1'),
            }


            serializer = CommitteeSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)

# validate api for Form 99
@api_view(['POST'])
def validate_f99(request):
    # # get all comm info
    # if request.method == 'GET':
    #     comm_info = CommitteeInfo.objects.all()
    #     serializer = CommitteeInfoSerializer(comm_info, many=True)
    #     return Response(serializer.data)

    # insert a new record for a comm_info
    if request.method == 'POST':
        data = {
            'committeeid': request.data.get('committeeid'),
            'committeename': request.data.get('committeename'),
            'street1': request.data.get('street1'),
            'street2': request.data.get('street2'),
            'city': request.data.get('city'),
            'state': request.data.get('state'),
            'text': request.data.get('text'),
            'reason' :request.data.get('reason'),
            'zipcode': request.data.get('zipcode'),
            'treasurerlastname': request.data.get('treasurerlastname'),
            'treasurerfirstname': request.data.get('treasurerfirstname'),
            'treasurermiddlename': request.data.get('treasurermiddlename'),
            'treasurerprefix': request.data.get('treasurerprefix'),
            'treasurersuffix': request.data.get('treasurersuffix'),
            'email_on_file' : request.data.get('email_on_file'),
            'email_on_file_1' : request.data.get('email_on_file_1'),
            'file': request.data.get('file')
        }
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    try:
        
        comm = Committee.objects.filter(committeeid=request.data.get('committeeid')).last()

    except Committee.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    errormess = []

    if comm.committeename!=request.data.get('committeename'):
        errormess.append('Committee Name does not match the Form 1 data.')

    if comm.street1!=request.data.get('street1'):
        errormess.append('Street1 does not match the Form 1 data.')

    if 'street2' in request.data and comm.street2!=request.data.get('street2'):
        errormess.append('Street2 does not match the Form 1 data.')

    if comm.city!=request.data.get('city'):
        errormess.append('City does not match the Form 1 data.')

    if comm.state!=request.data.get('state'):
        errormess.append('State does not match the Form 1 data.')

    if comm.zipcode!= int(request.data.get('zipcode')) if request.data.get('zipcode') else '':
        errormess.append('Zipcode does not match the Form 1 data.')

    if comm.treasurerlastname!=request.data.get('treasurerlastname'):
        errormess.append('Treasurer Last Name does not match the Form 1 data.')

    if comm.treasurerfirstname!=request.data.get('treasurerfirstname'):
        errormess.append('Treasurer First Name does not match the Form 1 data.')

    if 'treasurermiddlename' in request.data and comm.treasurermiddlename!=request.data.get('treasurermiddlename'):
        errormess.append('Treasurer Middle Name does not match the Form 1 data.')

    if 'treasurerprefix' in request.data and comm.treasurerprefix!=request.data.get('treasurerprefix'):
        errormess.append('Treasurer Prefix does not match the Form 1 data.')

    if 'treasurersuffix' in request.data and comm.treasurersuffix!=request.data.get('treasurersuffix'):
        errormess.append('Treasurer Suffix does not match the Form 1 data.')

    if 'email_on_file_1' in request.data and comm.email_on_file_1!=request.data.get('email_on_file_1'):
        errormess.append('email_on_file_1 does not match the Form 1 data.')

    if 'email_on_file' in request.data and comm.email_on_file!=request.data.get('email_on_file'):
        errormess.append('email_on_file does not match the Form 1 data.')

    if len(request.data.get('text'))>20000:
        errormess.append('Text greater than 20000.')

    if len(request.data.get('text'))==0:
        errormess.append('Text field is empty.')

    conditions = [request.data.get('reason')=='MST', request.data.get('reason')=='MSM', request.data.get('reason')=='MSI', request.data.get('reason')=='MSW']
    if not any(conditions):
        errormess.append('Reason does not match the pre-defined codes.')
    """
    #pdf validation for type, extension and size
    if 'file' in request.data or request.data.get('file')=='':
        valid_mime_types = ['application/pdf']
        file = request.data.get('file')
        file_mime_type = magic.from_buffer(file.read(1024), mime=True)
        if file_mime_type not in valid_mime_types:
            errormess.append('This is not a pdf file type. Kindly open your document using a pdf reader before uploading it.')
        valid_file_extensions = ['.pdf']
        ext = os.path.splitext(file.name)[1]
        if ext.lower() not in valid_file_extensions:
            errormess.append('Unacceptable file extension. Only files with .pdf extensions are accepted.')
        if file._size > 33554432:
            errormess.append('The File size is more than 32 MB. Kindly reduce the size of the file before you upload it.')
    """
    if len(errormess)==0:
        errormess.append('Validation successful!')
        return JsonResponse(errormess, status=200, safe=False)
    else:
        return JsonResponse(errormess, status=400, safe=False)

@api_view(['GET'])
def get_rad_analyst_info(request):
    """
    ref: #https://api.open.fec.gov/v1/rad-analyst/?page=1&per_page=20&api_key=DEMO_KEY&sort_hide_null=false&sort_null_only=false
    """
    if request.method == 'GET':
        try:
            #import ipdb; ipdb.set_trace();
            if get_comittee_id(request.user.username):
                ab = requests.get('https://api.open.fec.gov/v1/rad-analyst/?page=1&per_page=20&api_key=50nTHLLMcu3XSSzLnB0hax2Jg5LFniladU5Yf25j&committee_id=' + get_comittee_id(request.user.username) + '&sort_hide_null=false&sort_null_only=false')
                return JsonResponse({"response":ab.json()['results']})
            else:
                return JsonResponse({"ERROR":"You must be logged in  for this operation."})
        except:
            return JsonResponse({"ERROR":"ERR_f99_03: Unexpected Error. Please contact administrator."})

@api_view(['GET'])
def get_form99list(request):
    """
    API that provides all the reports for a specific committee
    """
    if request.method == 'GET':
        try:
            cmte_id = get_comittee_id(request.user.username)
            viewtype = request.query_params.get('view')
            reportid = request.query_params.get('reportId')

            #commented by Mahendra 10052019
            #print ("[cmte_id]", cmte_id)
            print ("[viewtype]", viewtype)
            print ("[reportid]", reportid)

            forms_obj = None
            with connection.cursor() as cursor:
                if reportid in ["None", "null", " ", "","0"]:    
                    query_string =  """SELECT json_agg(t) FROM 
                                    (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, viewtype, 
                                            deleteddate    
                                     FROM   (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, 
                                         CASE
                                            WHEN (date_part('year', cvg_end_date) < date_part('year', now()) - integer '1') THEN 'archieve'
                                            WHEN (date_part('year', cvg_end_date) = date_part('year', now()) - integer '1') AND (date_part('month', now()) > integer '1') THEN 'archieve'
                                            ELSE 'current'
                                        END AS viewtype,
                                            deleteddate
                                         FROM public.reports_view WHERE cmte_id = %s AND last_update_date is not null AND (delete_ind <> 'Y' OR delete_ind is NULL)
                                    ) t1
                                    WHERE  viewtype = %s ORDER BY last_update_date DESC ) t; """
                else:
                    query_string =  """SELECT json_agg(t) FROM 
                                    (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, viewtype,
                                            deleteddate    
                                     FROM   (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, 
                                         CASE
                                            WHEN (date_part('year', cvg_end_date) < date_part('year', now()) - integer '1') THEN 'archieve'
                                            WHEN (date_part('year', cvg_end_date) = date_part('year', now()) - integer '1') AND (date_part('month', now()) > integer '1') THEN 'archieve'
                                            ELSE 'current'
                                        END AS viewtype,
                                            deleteddate
                                         FROM public.reports_view WHERE cmte_id = %s AND delete_ind is distinct from 'Y'
                                    ) t1
                                    WHERE report_id = %s  AND  viewtype = %s ORDER BY last_update_date DESC ) t; """

                #commented by Mahendra 10052019
                #print("query_string =", query_string)

                # print("query_string = ", query_string)
                # Pull reports from reports_view
                #query_string = """select form_fields from dynamic_forms_view where form_type='""" + form_type + """' and transaction_type='""" + transaction_type + """'"""
                if reportid in ["None", "null", " ", "","0"]:  
                    cursor.execute(query_string, [cmte_id, viewtype])
                else:
                    cursor.execute(query_string, [cmte_id, reportid, viewtype])

                for row in cursor.fetchall():
                    data_row = list(row)
                    forms_obj=data_row[0]
            print(forms_obj)
            if forms_obj is None:
               forms_obj = []

            # for submitted report, add FEC- to fec_id
            SUBMIT_STATUS = 'Filed'
            for obj in forms_obj:
                if obj['status'] == SUBMIT_STATUS:
                    obj['fec_id'] = 'FEC-' + str(obj.get('fec_id', ''))

            with connection.cursor() as cursor:

                if reportid in ["None", "null", " ", "","0"]:    
                    query_count_string =  """SELECT count('a') as totalreportsCount FROM 
                                    (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, 
                                            superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, 
                                            delete_ind, create_date, last_update_date,report_type_desc, viewtype, deleteddate    
                                     FROM   (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, 
                                            superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, 
                                            delete_ind, create_date, last_update_date, report_type_desc, 
                                         CASE
                                            WHEN (date_part('year', cvg_end_date) < date_part('year', now()) - integer '1') THEN 'archieve'
                                            WHEN (date_part('year', cvg_end_date) = date_part('year', now()) - integer '1') AND (date_part('month', now()) > integer '1') THEN 'archieve'
                                            ELSE 'current'
                                        END AS viewtype, deleteddate
                                         FROM public.reports_view WHERE cmte_id = %s AND (delete_ind <> 'Y' OR delete_ind is NULL) AND last_update_date is not null 
                                    ) t1
                                    WHERE  viewtype = %s ORDER BY last_update_date DESC ) t; """
                else:
                    query_count_string =  """SELECT count('a') as totalreportsCount FROM 
                                    (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, 
                                        superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, 
                                        delete_ind, create_date, last_update_date,report_type_desc, viewtype, deleteddate    
                                     FROM   (SELECT report_id, form_type, amend_ind, amend_number, cmte_id, report_type, cvg_start_date, cvg_end_date, due_date, 
                                            superceded_report_id, previous_report_id, status, filed_date, fec_id, fec_accepted_date, fec_status, most_recent_flag, delete_ind, create_date, last_update_date,report_type_desc, 
                                         CASE
                                            WHEN (date_part('year', cvg_end_date) < date_part('year', now()) - integer '1') THEN 'archieve'
                                            WHEN (date_part('year', cvg_end_date) = date_part('year', now()) - integer '1') AND (date_part('month', now()) > integer '1') THEN 'archieve'
                                            ELSE 'current'
                                        END AS viewtype, deleteddate
                                         FROM public.reports_view WHERE cmte_id = %s  AND (delete_ind <> 'Y' OR delete_ind is NULL) 
                                    ) t1
                                    WHERE report_id = %s  AND  viewtype = %s ORDER BY last_update_date DESC ) t; """

                #commented by Mahendra 10052019
                #print("query_count_string =", query_count_string)

                if reportid in ["None", "null", " ", "","0"]:  
                    cursor.execute(query_count_string, [cmte_id, viewtype])
                else:
                    cursor.execute(query_count_string, [cmte_id, reportid, viewtype])

                for row in cursor.fetchall():
                    data_row = list(row)
                    forms_cnt_obj=data_row[0]

            if forms_cnt_obj is None:
                forms_cnt_obj = []

            json_result = { 'reports': forms_obj, 'totalreportsCount':forms_cnt_obj}    
        except Exception as e:
            # print (str(e))
            return Response("The reports view api - get_form99list is throwing an error" + str(e), status=status.HTTP_400_BAD_REQUEST)

        #return Response(forms_obj, status=status.HTTP_200_OK)
        return Response(json_result, status=status.HTTP_200_OK)



        
        
#API to delete saved forms
@api_view(['POST'])
def delete_forms(request):
    """
    deletes the multiple saved reports based on report/form id. Returns success or fail message
    """
    try:
        is_read_only_or_filer_reports(request)
        if request.method == 'POST':
            for obj in request.data:
                try:
                    if obj.get('form_type') == 'F99':
                        comm_info = CommitteeInfo.objects.filter(is_submitted=False, isdeleted=False, id=obj.get('id')).first()
                        # or can be written like comm_info = CommitteeInfo.objects.filter(is_submitted=False, isdeleted=False, id=request.data.get('id'))[0]
                        # way to access single object out of multiple objects -> for object in objects:

                        if comm_info:
                            #print('%s') %new_data.get('committeename')
                            new_data = vars(comm_info)
                            new_data["isdeleted"]=True
                            new_data["deleted_at"]=datetime.datetime.now()
                            serializer = CommitteeInfoSerializer(comm_info, data=new_data)
                            if serializer.is_valid():
                                serializer.save()
                                #print(serializer.data)
                            else:
                                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            #print(comm_info.id)
                            return Response({"error":"ERRCODE: FEC03. Form with id %d is already deleted or has been submitted beforehand." %obj.get('id')}, status=status.HTTP_400_BAD_REQUEST)
                except:
                    return Response({"error":"There is an error while deleting forms."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"Forms deleted successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error":"ERRCODE: FEC02. POST method is expected."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)

#email through AWS SES
def email(boolean, data):
    SENDER = "donotreply@fec.gov"
    RECIPIENT = []

    RECIPIENT.append("%s" % data.get('email_on_file'))
    
    #print(data.get('additional_email_1'))
    if 'additional_email_1' in data and (not (data.get('additional_email_1')=='-' or data.get('additional_email_1') is None or data.get('additional_email_1') == 'null')):
        RECIPIENT.append("%s" % data.get('additional_email_1')) 
    
    #print(data.get('additional_email_2'))
    if 'additional_email_2' in data and (not (data.get('additional_email_2')=='-' or data.get('additional_email_2') is None or data.get('additional_email_2') == 'null')):
        RECIPIENT.append("%s" % data.get('additional_email_2'))

    #print(data.get('email_on_file_1'))
    if 'email_on_file_1' in data and (not (data.get('email_on_file_1')=='-' or data.get('email_on_file_1') is None or data.get('email_on_file_1') == 'null')):
        RECIPIENT.append("%s" % data.get('email_on_file_1'))
    
    SUBJECT = "Test - Form 99 submitted successfully"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Form 99 that we received has been validated and submitted\r\n"
                 "This email was sent by FEC.gov. If you are receiving this email in error or have any questions, please contact the FEC Electronic Filing Office toll-free at (800) 424-9530 ext. 1307 or locally at (202) 694-1307."
                )
                
    # The HTML body of the email.
    #final_html = email_ack1.html.replace('{{@REPID}}',1234567).replace('{{@REPLACE_CMTE_ID}}',C0123456)
    #t = Template(email_ack1)
    #c= Context({'@REPID':123458},)

    data['updated_at'] = maya.parse(data['updated_at']).datetime(to_timezone='US/Eastern', naive=True).strftime("%m-%d-%Y %T")
    data['created_at'] = maya.parse(data['created_at']).datetime(to_timezone='US/Eastern', naive=True).strftime("%m-%d-%Y %T")

    BODY_HTML = render_to_string('email_ack.html',{'data':data})
    #data.get('committeeid')

    """<html>
    <head></head>
    <body>
      <h1>Form 99 that we received has been validated and submitted</h1>
      <p>This email was sent by FEC.gov. If you are receiving this email in error or have any questions, please contact the FEC Electronic Filing Office toll-free at (800) 424-9530 ext. 1307 or locally at (202) 694-1307."</p>
    </body>
    </html>"""

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name='us-east-1')

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': 
                    RECIPIENT,
                
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
           
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])



"""
@api_view(['GET'])
def get_comm_lookup(request):
   
    #fields for comm lookup
    
    try:
        import ipdb; ipdb.set_trace()

        comm = CommitteeLookup.objects.get(cmte_id=get_comittee_id(request.user.username))
    except CommitteeLookup.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    # get details wrt to the committeeid
    if request.method == 'GET':
        new_obj = {'committeeid':comm.cmte_id, 'committee_type': comm.cmte_type, 'committee_name':comm.cmte_name, 'committee_design':comm.cmte_dsgn, 'committee_filing_freq':comm.cmte_filing_freq}
        return Response(new_obj)
"""
"""
@api_view(['GET'])
def get_filed_form_types(request):
   
    #Fields for identifying the committee type and committee design and filter the forms category 
    
    try:
        comm_id = get_comittee_id(request.user.username)
        
        #forms_obj = [obj.__dict__ for obj in RefFormTypes.objects.raw("select  rctf.category,rft.form_type,rft.form_description,rft.form_tooltip,rft.form_pdf_url from ref_form_types rft join ref_cmte_type_vs_forms rctf on rft.form_type=rctf.form_type where rctf.cmte_type='" + cmte_type + "' and rctf.cmte_dsgn='" + cmte_dsgn +  "'")]
        forms_obj = [obj.__dict__ for obj in My_Forms_View.objects.raw("select * from my_forms_view where cmte_id='"  + comm_id + "' order by category,form_type")]

        for form_obj in forms_obj:
            if form_obj['due_date']:
                form_obj['due_date'] = form_obj['due_date'].strftime("%m-%d-%Y")
            
        resp_data = [{k:v.strip(" ") for k,v in form_obj.items() if k not in ["_state"] and type(v) == str } for form_obj in forms_obj]
        return Response(resp_data, status=status.HTTP_200_OK)
    except:
        return Response({}, status=status.HTTP_404_NOT_FOUND)
"""

"""
@api_view(['GET'])
def get_report_types_(request):
    
    #fields fordentifying the committee type and committee design and filter the forms category 
    
    try:
        comm_id = get_comittee_id(request.user.username)

        #forms_obj = [obj.__dict__ for obj in RefFormTypes.objects.raw("select  rctf.category,rft.form_type,rft.form_description,rft.form_tooltip,rft.form_pdf_url from ref_form_types rft join ref_cmte_type_vs_forms rctf on rft.form_type=rctf.form_type where rctf.cmte_type='" + cmte_type + "' and rctf.cmte_dsgn='" + cmte_dsgn +  "'")]
        forms_obj = [obj.__dict__ for obj in My_Forms_View.objects.raw("select * from my_forms_view where cmte_id='"  + comm_id + "' order by category,form_type")]

        for form_obj in forms_obj:
            if form_obj['due_date']:
                form_obj['due_date'] = form_obj['due_date'].strftime("%m-%d-%Y")

        resp_data = [{k:v.strip(" ") for k,v in form_obj.items() if k not in ["_state"] and type(v) == str } for form_obj in forms_obj]
        return Response(resp_data, status=status.HTTP_200_OK)
    except:
        return Response({}, status=status.HTTP_404_NOT_FOUND)
"""

@api_view(['POST'])
def save_print_f99(request):
    """"
    Fetches the last unsubmitted comm_info object saved in db. This obviously is for the object persistence between logins.
    """
    #import ipdb; ipdb.set_trace()
    logger.debug("Incoming parameters: save_print_f99" + str(request.data))
    # token_use = request.auth.decode("utf-8")

    # token_use = "JWT" + " " + token_use

    # if 'file' in request.data:
    #     filename = request.data.get('file').name
    #     attachment = request.data.get('file')
    #     decode_file = attachment.read()
    #     #attachment = open(request.data.get('file'), 'rb')
    #     files = {'file': (filename, decode_file, 'application/pdf')}

    #     #print(request._request.content)
    #     #request._request.content
    #     #'file': ('attachment.pdf', myfile, 'application/pdf')
    #     createresp = requests.post(settings.NXG_FEC_API_URL + settings.NXG_FEC_API_VERSION + "f99/create_f99_info", data=request.data, files=files, headers={'Authorization': token_use})
    #     #createresp = 
    # else:
    #     createresp = requests.post(settings.NXG_FEC_API_URL + settings.NXG_FEC_API_VERSION + "f99/create_f99_info", data=request.data, headers={'Authorization': token_use})
    
    createresp = create_f99_info(request._request)

    if createresp.status_code != 201:
        entity_status = status.HTTP_400_BAD_REQUEST
        return Response(createresp.data, status=entity_status)

    else:
        #print(createresp.content)
        create_json_data = json.loads(createresp.content.decode("utf-8"))
        #create_json_data = {"id" : "12"}

    # #print(request.auth)
    # if not createresp.ok:
    #     return Response(createresp.json(), status=status.HTTP_400_BAD_REQUEST)
    # #try:
    # create_json_data = json.loads(createresp.text)
    est = pytz.timezone('US/Eastern')

    comm_info = CommitteeInfo.objects.filter(id=create_json_data['id']).last()
    if comm_info:
        header = {
                "version":"8.3",
                "softwareName":"ABC Inc",
                "softwareVersion":"1.02 Beta",
                "additionalInfomation":"Any other useful information"
        }

        serializer = CommitteeInfoSerializer(comm_info)
        conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket("dev-efile-repo")
        k = Key(bucket)
        k.content_type = "application/json"
        data_obj = {}
        data_obj['header'] = header
        f99data = {}
        f99data['committeeId'] = comm_info.committeeid
        f99data['committeeName'] = comm_info.committeename
        f99data['street1'] = comm_info.street1
        f99data['street2'] = comm_info.street2
        f99data['city'] = comm_info.city
        f99data['state'] = comm_info.state
        f99data['zipCode'] = str(comm_info.zipcode)
        f99data['treasurerLastName'] = comm_info.treasurerlastname
        f99data['treasurerFirstName'] = comm_info.treasurerfirstname
        f99data['treasurerMiddleName'] = comm_info.treasurermiddlename
        f99data['treasurerPrefix'] = comm_info.treasurerprefix
        f99data['treasurerSuffix'] = comm_info.treasurersuffix
        f99data['reason'] = comm_info.reason
        f99data['text'] = comm_info.text
        f99data['dateSigned'] = datetime.datetime.now().strftime('%m/%d/%Y')
        #f99data['dateSigned'] = '5/15/2019'
        f99data['email1'] = comm_info.email_on_file
        f99data['email2'] = comm_info.email_on_file_1
        f99data['formType'] = comm_info.form_type
        f99data['attachement'] = 'X'
        f99data['password'] = "test"

        #data_obj['data'] = serializer.data
        data_obj['data'] = f99data
        k.set_contents_from_string(json.dumps(data_obj))            
        url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")

        tmp_filename = '/tmp/' + comm_info.committeeid + '_' + str(comm_info.id) + '_f99.json'   
        #tmp_filename = comm_info.committeeid + '_' + str(comm_info.id) + '_f99.json'            
        vdata = {}
        #commented by Mahendra 10052019
        #print ("url= ", url)
        #print ("tmp_filename= ", tmp_filename)


        vdata['wait'] = 'false'
        #print("vdata",vdata)
        json.dump(data_obj, open(tmp_filename, 'w'))

        #with open('data.json', 'w') as outfile:
         #   json.dump(data, outfile, ensure_ascii=False)
        
         # variables to be sent along the JSON file in form-data
        filing_type='FEC'
        vendor_software_name='FECFILE'

        data_obj = {
                'form_type': 'F99',
                'filing_type':filing_type,
                'vendor_software_name':vendor_software_name,
            }

        #print(comm_info.file)
        
        if not (comm_info.file in [None, '', 'null', ' ',""]):
            filename = comm_info.file.name 
            #print(filename)
            myurl = "https://{}.s3.amazonaws.com/media/".format(settings.AWS_STORAGE_BUCKET_NAME) + filename
            #print(myurl)
            #url_request = urllib.request.Request(myurl, headers = {"User-Agent", "Mozilla/5.0"})
            url_request = urllib.request.Request(myurl)
            myfile = urllib.request.urlopen(url_request)

            #s3 = boto3.client('s3')

            #file_object = s3.get_object(Bucket='settings.AWS_STORAGE_BUCKET_NAME', Key='settings.MEDIAFILES_LOCATION' + "/" + 'comm_info.file')

            #attachment = open(file_object['Body'], 'rb')

            """
                file_obj = {
                    'json_file': ('data.json', open('data.json', 'r'), 'application/json'),
                    'attachment_file': ('attachment.pdf', myfile, 'application/pdf')
                }
            else:
                file_obj = {
                    'json_file': ('data.json', open('data.json', 'r'), 'application/json')
                }
            """
            file_obj = {
                'json_file': ('data.json', open(tmp_filename, 'r'), 'application/json'),
                'attachment_file': ('attachment.pdf', myfile, 'application/pdf')
            }
        else:
            file_obj = {
                'json_file': ('data.json', open(tmp_filename, 'r'), 'application/json')
            }

        #printresp = requests.post("http://" + settings.NXG_FEC_API_URL + settings.NXG_FEC_API_VERSION + "f99/print_pdf", data=data_obj, files=file_obj)
        # printresp = requests.post("http://" + settings.NXG_FEC_API_URL + settings.NXG_FEC_API_VERSION + "f99/print_pdf", data=data_obj, files=file_obj, headers={'Authorization': token_use})
        printresp = requests.post(settings.NXG_FEC_PRINT_API_URL + settings.NXG_FEC_PRINT_API_VERSION, data=data_obj, files=file_obj)

        if not printresp.ok:
            return Response(printresp.json(), status=status.HTTP_400_BAD_REQUEST)
        else:
            #dictcreate = createresp.json()
            dictprint = printresp.json()
            merged_dict = {**create_json_data, **dictprint}
            #merged_dict = {key: value for (key, value) in (dictcreate.items() + dictprint.items())}
            return JsonResponse(merged_dict, status=status.HTTP_201_CREATED)
            #return Response(printresp.json(), status=status.HTTP_201_CREATED)
        
    else:
        return Response({"FEC Error 003":"This form Id number does not exist"}, status=status.HTTP_400_BAD_REQUEST)
    """    
    except CommitteeInfo.DoesNotExist:
        return Response({"FEC Error 004":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({"FEC Error 006":"This form Id number is not an integer"}, status=status.HTTP_400_BAD_REQUEST)
    """

@api_view(['POST'])
def update_print_f99(request):
    """"
    Fetches the last unsubmitted comm_info object saved in db. This obviously is for the object persistence between logins.
    """
    #import ipdb; ipdb.set_trace()
    # token_use = request.auth.decode("utf-8")

    # token_use = "JWT" + " " + token_use

    # createresp = requests.post(settings.NXG_FEC_API_URL + settings.NXG_FEC_API_VERSION + "f99/update_f99_info", data=request.data, headers={'Authorization': token_use})
    # if not createresp.ok:
    #     return Response(createresp.json(), status=status.HTTP_400_BAD_REQUEST)

    updateresp = update_f99_info(request._request, print_flag=True)

    if updateresp.status_code != 201:
        update_json_data = json.loads(updateresp.content.decode("utf-8"))
        entity_status = status.HTTP_400_BAD_REQUEST
        return Response(updateresp.data, status=entity_status)

    else:
        #print(updateresp.content)
        update_json_data = json.loads(updateresp.content.decode("utf-8"))

    est = pytz.timezone('US/Eastern')

    #try:
    comm_info = CommitteeInfo.objects.filter(id=update_json_data['id']).last()
    if comm_info:
        header = {
                "version":"8.3",
                "softwareName":"ABC Inc",
                "softwareVersion":"1.02 Beta",
                "additionalInfomation":"Any other useful information"
        }

        serializer = CommitteeInfoSerializer(comm_info)
        conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket("dev-efile-repo")
        k = Key(bucket)
        k.content_type = "application/json"
        data_obj = {}
        data_obj['header'] = header
        f99data = {}
        f99data['committeeId'] = comm_info.committeeid
        f99data['committeeName'] = comm_info.committeename
        f99data['street1'] = comm_info.street1
        f99data['street2'] = comm_info.street2
        f99data['city'] = comm_info.city
        f99data['state'] = comm_info.state
        f99data['zipCode'] = str(comm_info.zipcode)
        f99data['treasurerLastName'] = comm_info.treasurerlastname
        f99data['treasurerFirstName'] = comm_info.treasurerfirstname
        f99data['treasurerMiddleName'] = comm_info.treasurermiddlename
        f99data['treasurerPrefix'] = comm_info.treasurerprefix
        f99data['treasurerSuffix'] = comm_info.treasurersuffix
        f99data['reason'] = comm_info.reason
        f99data['text'] = comm_info.text
        f99data['dateSigned'] = datetime.datetime.now().strftime('%m/%d/%Y')
        #f99data['dateSigned'] = '5/15/2019'
        f99data['email1'] = comm_info.email_on_file
        f99data['email2'] = comm_info.email_on_file_1
        f99data['formType'] = comm_info.form_type
        f99data['attachement'] = 'X'
        f99data['password'] = "test"

        #data_obj['data'] = serializer.data
        data_obj['data'] = f99data
        k.set_contents_from_string(json.dumps(data_obj))            
        url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")

        tmp_filename = '/tmp/' + comm_info.committeeid + '_' + str(comm_info.id) + '_f99.json'   
        #tmp_filename = comm_info.committeeid + '_' + str(comm_info.id) + '_f99.json'            
        vdata = {}
        #commented by Mahendra 10052019
        #print ("url= ", url)
        #print ("tmp_filename= ", tmp_filename)


        vdata['wait'] = 'false'
        #print("vdata",vdata)
        json.dump(data_obj, open(tmp_filename, 'w'))

        #with open('data.json', 'w') as outfile:
         #   json.dump(data, outfile, ensure_ascii=False)
        
        #obj = open('data.json', 'w')
        #obj.write(serializer.data)
        #obj.close

        # variables to be sent along the JSON file in form-data
        filing_type='FEC'
        vendor_software_name='FECFILE'

        data_obj = {
                'form_type':'F99',
                'filing_type':filing_type,
                'vendor_software_name':vendor_software_name,
            }

        #print(comm_info.file)
        
        if not (comm_info.file in [None, '', 'null', ' ',""]):
            filename = comm_info.file.name 
            #print(filename)
            myurl = "https://{}.s3.amazonaws.com/media/".format(settings.AWS_STORAGE_BUCKET_NAME) + filename
            #myurl = "https://fecfile-filing.s3.amazonaws.com/media/" + filename
            #print(myurl)
            myfile = urllib.request.urlopen(myurl)

            #s3 = boto3.client('s3')

            #file_object = s3.get_object(Bucket='settings.AWS_STORAGE_BUCKET_NAME', Key='settings.MEDIAFILES_LOCATION' + "/" + 'comm_info.file')

            #attachment = open(file_object['Body'], 'rb')

            
            """
            file_obj = {
                'json_file': ('data.json', open('data.json', 'rb'), 'application/json'),
                'attachment_file': ('attachment.pdf', myfile, 'application/pdf')
            }
        else:
            file_obj = {
                'json_file': ('data.json', open('data.json', 'rb'), 'application/json')
            }
            """

            file_obj = {
                'json_file': ('data.json', open(tmp_filename, 'rb'), 'application/json'),
                'attachment_file': ('attachment.pdf', myfile, 'application/pdf')
            }
        else:
            file_obj = {
                'json_file': ('data.json', open(tmp_filename, 'rb'), 'application/json')
            }

        # printresp = requests.post("http://" + settings.NXG_FEC_API_URL + settings.NXG_FEC_API_VERSION + "f99/print_pdf", data=data_obj, files=file_obj)
        # printresp = requests.post("http://" + settings.NXG_FEC_API_URL + settings.NXG_FEC_API_VERSION + "f99/print_pdf", data=data_obj, files=file_obj, headers={'Authorization': token_use})
        printresp = requests.post(settings.NXG_FEC_PRINT_API_URL + settings.NXG_FEC_PRINT_API_VERSION, data=data_obj, files=file_obj)
        if not printresp.ok:
            return Response(printresp.json(), status=status.HTTP_400_BAD_REQUEST)
        else:
            #dictcreate = createresp.json()
            dictprint = printresp.json()
            merged_dict = {**update_json_data, **dictprint}
            #merged_dict = {key: value for (key, value) in (dictcreate.items() + dictprint.items())}
            return JsonResponse(merged_dict, status=status.HTTP_201_CREATED)
            #return Response(printresp.json(), status=status.HTTP_201_CREATED)
    else:
        return Response({"FEC Error 003":"This form Id number does not exist"}, status=status.HTTP_400_BAD_REQUEST)
    """    
    except CommitteeInfo.DoesNotExist:
        return Response({"FEC Error 004":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({"FEC Error 006":"This form Id number is not an integer"}, status=status.HTTP_400_BAD_REQUEST)
    """
    
def set_need_appearances_writer(writer):

    try:

        catalog = writer._root_object

        # get the AcroForm tree and add "/NeedAppearances attribute

        if "/AcroForm" not in catalog:

            writer._root_object.update({

                NameObject("/AcroForm"): IndirectObject(len(writer._objects), 0, writer)})

 

        need_appearances = NameObject("/NeedAppearances")

        writer._root_object["/AcroForm"][need_appearances] = BooleanObject(True)

        return writer

 

    except Exception as e:

        print('set_need_appearances_writer() catch : ', repr(e))

        return writer

def update_checkbox_values(page, fields):
   for j in range(0, len(page['/Annots'])):
       writer_annot = page['/Annots'][j].getObject()
       for field in fields:
           if writer_annot.get('/T') == field:
               writer_annot.update({
                   NameObject("/V"): NameObject(fields[field]),
                   NameObject("/AS"): NameObject(fields[field])
               }) 
 

# API which prints Form 99 data

@api_view(['POST'])

def print_pdf(request):

    #try:
    data1 = request.data.get('data1')
    #buff = data1.read()


    data_decode = json.load(data1)
    #print(data_decode['IMGNO'])
    #if data_decode['REASON_TYPE'] = "MST":
    #    data_decode['']

    infile = "templates/forms/F99.pdf"

    outfile = 'templates/forms/media/{}.pdf'.format(data_decode['IMGNO'])

    #print(data_decode['REASON_TYPE'])

    data_decode['FILER_FEC_ID_NUMBER'] = data_decode['FILER_FEC_ID_NUMBER'][1:]

    if data_decode['REASON_TYPE'] == 'MST':
        reason_type_data = {"REASON_TYPE_MST":"/MST"}

    if data_decode['REASON_TYPE'] == 'MSM':
        reason_type_data = {"REASON_TYPE_MSM":"/MSM"}

    if data_decode['REASON_TYPE'] == 'MSI':
        reason_type_data = {"REASON_TYPE_MSI":"/MSI"}

    if data_decode['REASON_TYPE'] == 'MSW':
        reason_type_data = {"REASON_TYPE_MSW":"/MSW"}
    # open the input file

    input_stream = open(infile, "rb")

    pdf_reader = PdfFileReader(input_stream, strict=True)

    if "/AcroForm" in pdf_reader.trailer["/Root"]:

        pdf_reader.trailer["/Root"]["/AcroForm"].update(

            {NameObject("/NeedAppearances"): BooleanObject(True)})



    pdf_writer = PdfFileWriter()

    set_need_appearances_writer(pdf_writer)

    if "/AcroForm" in pdf_writer._root_object:
        pdf_writer._root_object["/AcroForm"].update(
            {NameObject("/NeedAppearances"): BooleanObject(True)})

    for page_num in range(pdf_reader.numPages):

        page_obj = pdf_reader.getPage(page_num)

        pdf_writer.addPage(page_obj)

        update_checkbox_values(page_obj, reason_type_data)

        pdf_writer.updatePageFormFieldValues(page_obj, data_decode)

        #print(data_decode)



    # Add the F99 attachment
    if 'file' in request.data:
        #attachment_file = "templates/forms/F99_Attachment.pdf"
        attachment_stream = request.data.get('file')

        #attachment_stream = open(attachment_file, "rb")

        attachment_reader = PdfFileReader(attachment_stream, strict=True)

        for attachment_page_num in range(attachment_reader.numPages):

            attachment_page_obj = attachment_reader.getPage(attachment_page_num)

            pdf_writer.addPage(attachment_page_obj)

 

    output_stream = open(outfile, "wb")

    pdf_writer.write(output_stream)

    input_stream.close()

    output_stream.close()

    s3 = boto3.resource('s3')
    s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME).upload_file(outfile, 'media/{}.pdf'.format(data_decode['IMGNO']))

    resp = {
        'printpriview_filename' : '{}.pdf'.format(data_decode['IMGNO']),
        'printpriview_fileurl' : "https://" + "{}".format(settings.AWS_STORAGE_BUCKET_NAME) + ".s3.amazonaws.com/media/" + "{}.pdf".format(data_decode['IMGNO'])
    }

    return JsonResponse(resp, status=status.HTTP_201_CREATED)


def check_F99_Reason_Text(strReasonText):
    print("In check_F99_Reason_Text...")
    try:
        """f = open(r'/home/mahendra/Downloads/test.html', 'r')
        for line in f:
            for word in line.split():
                validate_HTMLtag(word)      
        return "" 
        """ 
        for word in strReasonText.split():
            validate_HTMLtag(word)      
        return "" 
    except Exception as e:
        return Response("The check_F99_Reason_Text function is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)


def validate_HTMLtag(strWord):
    print("validate_HTMLtag...")
    print(" strWord = ", strWord)
    try:
        valideTags=['div','br','span','blockquote','ul','ol','li','b','u','i']
        if ('</' in strWord and '>' in strWord) and ('<div' not in strWord or '<span' not in strWord ): 
            print(" word check strWord = ", strWord)
            intstartpos=strWord.find('</'); 
            substr=strWord[intstartpos+2]
            intendpos=substr.find('>'); 
            strsearch=strWord[intstartpos+2:intendpos]
            print(strsearch)
            if strsearch not in valideTags:
                print(" Wrong tag =", strsearch) 
        return ""  
    except Exception as e:
        return Response("The validate_HTMLtag function is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_f99_report_info(request):
    """
    Get F99 report details
    """
    #print("request.query_params.get('reportid')=", request.query_params.get('reportid'))
    try:
        if ('reportid' in request.query_params and (not request.query_params.get('reportid') =='')):
            #print("you are here1")
            if int(request.query_params.get('reportid'))>=1:
                #print("you are here2")
                id_comm = CommitteeInfo()
                id_comm.id = request.query_params.get('reportid')
                #comm_info = CommitteeInfo.objects.filter(committeeid=request.data['committeeid'], id=request.data['reportid']).last()
                comm_info = CommitteeInfo.objects.filter(committeeid=get_comittee_id(request.user.username), id=request.query_params.get('reportid')).last()
                serializer = CommitteeInfoSerializer(comm_info)
                if comm_info:
                    return JsonResponse(serializer.data, status=status.HTTP_200_OK)
    except CommitteeInfo.DoesNotExist:
            return Response({"FEC Error 004":"There is no submitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def submit_formf99(request):
    """"
    Fetches the last unsubmitted comm_info object saved in db. This obviously is for the object persistence between logins.
    """
    try:
        #comm_info = CommitteeInfo.objects.filter(id=update_json_data['id']).last()

        comm_info = CommitteeInfo.objects.filter(committeeid=request.data.get('cmte_id'), id=request.data.get('reportid')).last()
        
        if comm_info:
            header = {
                    "version":"8.3",
                    "softwareName":"ABC Inc",
                    "softwareVersion":"1.02 Beta",
                    "additionalInfomation":"Any other useful information"
            }

            serializer = CommitteeInfoSerializer(comm_info)
            conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
            bucket = conn.get_bucket("dev-efile-repo")
            k = Key(bucket)
            k.content_type = "application/json"
            data_obj = {}
            data_obj['header'] = header
            f99data = {}
            f99data['committeeId'] = comm_info.committeeid
            f99data['committeeName'] = comm_info.committeename
            f99data['street1'] = comm_info.street1
            f99data['street2'] = comm_info.street2
            f99data['city'] = comm_info.city
            f99data['state'] = comm_info.state
            f99data['zipCode'] = str(comm_info.zipcode)
            f99data['treasurerLastName'] = comm_info.treasurerlastname
            f99data['treasurerFirstName'] = comm_info.treasurerfirstname
            f99data['treasurerMiddleName'] = comm_info.treasurermiddlename
            f99data['treasurerPrefix'] = comm_info.treasurerprefix
            f99data['treasurerSuffix'] = comm_info.treasurersuffix
            f99data['reason'] = comm_info.reason
            f99data['text'] = comm_info.text
            f99data['dateSigned'] = datetime.datetime.now().strftime('%m/%d/%Y')
            f99data['email1'] = comm_info.email_on_file
            f99data['email2'] = comm_info.email_on_file_1
            f99data['formType'] = comm_info.form_type
            f99data['attachement'] = 'X'
            f99data['password'] = "test"

            data_obj['data'] = f99data
            k.set_contents_from_string(json.dumps(data_obj))            
            url = k.generate_url(expires_in=0, query_auth=False).replace(":443","")

            tmp_filename = '/tmp/' + comm_info.committeeid + '_' + str(comm_info.id) + '_f99.json'   
            #tmp_filename = comm_info.committeeid + '_' + str(comm_info.id) + '_f99.json'            
            vdata = {}
            vdata['wait'] = 'false'
            json.dump(data_obj, open(tmp_filename, 'w'))

            # variables to be sent along the JSON file in form-data
            filing_type='FEC'
            vendor_software_name='FECFILE'
            form_type = comm_info.form_type
            data_obj = {
                    'form_type':form_type,
                    'filing_type':filing_type,
                    'vendor_software_name':vendor_software_name,
                }

            if not (comm_info.file in [None, '', 'null', ' ',""]):
                filename = comm_info.file.name 
                myurl = "https://{}.s3.amazonaws.com/media/".format(settings.AWS_STORAGE_BUCKET_NAME) + filename
                myfile = urllib.request.urlopen(myurl)

                file_obj = {
                    'fecDataFile': ('data.json', open(tmp_filename, 'rb'), 'application/json'),
                    'fecPDFAttachment': ('attachment.pdf', myfile, 'application/pdf')
                }
            else:
                file_obj = {
                    'fecDataFile': ('data.json', open(tmp_filename, 'rb'), 'application/json')
                }

            #printresp = requests.post(settings.NXG_FEC_PRINT_API_URL + settings.NXG_FEC_PRINT_API_VERSION, data=data_obj, files=file_obj)
            resp = requests.post("http://" + settings.DATA_RECEIVE_API_URL +
                                 "/v1/upload_filing", data=data_obj, files=file_obj)
            if not resp.ok:
                return Response(resp.json(), status=status.HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse(resp.json(), status=status.HTTP_201_CREATED)

        else:
            return Response({"FEC Error 003":"This form Id number does not exist"}, status=status.HTTP_400_BAD_REQUEST)

    except comm_info.DoesNotExist:
        return Response({"FEC Error 004":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({"FEC Error 006":"This form Id number is not an integer"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response("The submit_f99 API is throwing an error: " + str(e), status=status.HTTP_400_BAD_REQUEST)
