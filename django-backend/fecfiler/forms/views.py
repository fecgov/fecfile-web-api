from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
#from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .models import CommitteeInfo, Committee
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

# API view functionality for GET DELETE and PUT
# Exception handling is taken care to validate the committeinfo
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
        comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username,  is_submitted=False).last() #,)

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
        comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username,  is_submitted=False).last() #,)
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
            'email_on_file_1' : request.data.get('email_on_file_1'),
            'email_on_file_2': request.data.get('email_on_file_2'),
            #'file': request.data.get('file'),
        }

        serializer = CommitteeInfoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
def update_f99_info(request):
    """
    Updates the last unsubmitted comm_info object only. you can use this to change the 'text' and 'is_submitted' field as well as any other field.
    """
    # update details of a single comm_info
    if request.method == 'POST':
        try:
            #import ipdb; ipdb.set_trace()
            # fetch last comm_info object created, else return 404
            try:
                comm_info = CommitteeInfo.objects.get(committeeid=request.user.username,id=request.data.get('id'), is_submitted=False) #.last()
            except CommitteeInfo.DoesNotExist:
                return Response({"error":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)            
        except:
            #logger.
            return Response({"error":"An unexpected error occurred" + str(sys.exc_info()[0]) + ". Please contact administrator"}, status=status.HTTP_400_BAD_REQUEST) 
        
        incoming_data = request.data
        # overwrite is_submitted just in case user sends it, all submit changes to go via submit_comm_info api as we save to s3 and call fec api.
        incoming_data['is_submitted'] = False
        # just making sure that committeeid is not updated by mistake
        #incoming_data.committeeid=request.user.username
        incoming_data['committeeid'] = request.user.username
        serializer = CommitteeInfoSerializer(comm_info, data=incoming_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
         
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def submit_comm_info(request):
    """
    Submits the last unsubmitted but saved comm_info object only. Returns the saved object with updated timestamp and comm_info details
    validate_api/s3 not being called currently
    """
    #import ipdb; ipdb.set_trace()
    if request.method == 'POST':
        try:
            comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username).last()
            #print(comm_info.pk)
            if comm_info:
                new_data = comm_info.__dict__
                new_data["is_submitted"]=True
                new_data["updated_at"]=datetime.datetime.now()
                serializer = CommitteeInfoSerializer(comm_info, data=new_data)
                if serializer.is_valid():
                    serializer.save()
                    email(True, serializer.data)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)                    
        except:
            return Response({"error":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)

    else:
        return Response({"error":"ERRCODE: FEC02. Error occured while trying to submit form f99."}, status=status.HTTP_400_BAD_REQUEST)

    
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
#             comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username).last()
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
def get_committee(request):
    """
    fields for auto populating the data for creating the comm_info object
    """
    try:
        comm = Committee.objects.filter(committeeid=request.user.username).last()
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
        comm = Committee.objects.filter(committeeid=request.user.username).last()
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
    # # update details of a single comm
    if request.method == 'POST':
         serializer = CommitteeSerializer(comm, data=request.data)
         if serializer.is_valid():
             serializer.save()
             return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
@api_view(['POST'])
def create_committee(request):
    # insert a new record for a committee
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
        }


        serializer = CommitteeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            #'file': request.data.get('file'),
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

    if len(request.data.get('text'))>20000:
        errormess.append('Text greater than 20000.')

    if len(request.data.get('text'))==0:
        errormess.append('Text field is empty.')

    conditions = [request.data.get('reason')=='MST', request.data.get('reason')=='MSM', request.data.get('reason')=='MSI', request.data.get('reason')=='MSW']
    if not any(conditions):
        errormess.append('Reason does not match the pre-defined codes.')

    #pdf validation for type, extension and size
    # if 'file' in request.data:
    #     valid_mime_types = ['application/pdf']
    #     file = request.data.get('file')
    #     file_mime_type = magic.from_buffer(file.read(1024), mime=True)
    #     if file_mime_type not in valid_mime_types:
    #         errormess.append('This is not a pdf file type. Kindly open your document using a pdf reader before uploading it.')
    #     valid_file_extensions = ['.pdf']
    #     ext = os.path.splitext(file.name)[1]
    #     if ext.lower() not in valid_file_extensions:
    #         errormess.append('Unacceptable file extension. Only files with .pdf extensions are accepted.')
    #     if file._size > 33554432:
    #         errormess.append('The File size is more than 32 MB. Kindly reduce the size of the file before you upload it.')

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
            if request.user.username:
                ab = requests.get('https://api.open.fec.gov/v1/rad-analyst/?page=1&per_page=20&api_key=50nTHLLMcu3XSSzLnB0hax2Jg5LFniladU5Yf25j&committee_id=' + request.user.username + '&sort_hide_null=false&sort_null_only=false')
                return JsonResponse({"response":ab.json()['results']})
            else:
                return JsonResponse({"ERROR":"You must be logged in  for this operation."})
        except:
            return JsonResponse({"ERROR":"ERR_f99_03: Unexpected Error. Please contact administrator."})


@api_view(['GET'])
def get_form99list(request):
    """
    fields for auto populating the form 99 reports data
    """
    try:

        comm = CommitteeInfo.objects.filter(committeeid=request.user.username)

    except CommitteeInfo.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    # get details of a form 99 records
    if request.method == 'GET':

        serializer = CommitteeInfoListSerializer(comm)
        return Response(serializer.data)

#API to delete saved forms
@api_view(['POST'])
def delete_forms(request):
    """
    deletes the multiple saved reports based on report/form id. Returns success or fail message
    """
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
    
#email through AWS SES
def email(boolean, data):
    SENDER = "donotreply@fec.gov"
    RECIPIENT = []

    RECIPIENT.append("%s" % data.get('email_on_file'))

    if 'additional_email_1' in data and (not data.get('additional_email_1')=='-'):
        RECIPIENT.append("%s" % data.get('additional_email_1')) 

    if 'additional_email_2' in data and (not data.get('additional_email_2')=='-'):
        RECIPIENT.append("%s" % data.get('additional_email_2'))
    
    SUBJECT = "Test - Form 99 submitted successfully"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Form 99 that we received has been validated and submitted\r\n"
                 "This email was sent by FEC.gov. If you are receiving this email in error or have any questions, please contact the FEC Electronic Filing Office toll-free at (800) 424-9530 ext. 1307 or locally at (202) 694-1307."
                )
                
    # The HTML body of the email.
    #final_html = email_ack1.html.replace('{{@REPID}}',1234567).replace('{{@REPLACE_CMTE_ID}}',C0123456)
    #t = Template(email_ack1)
    #c= Context({'@REPID':123458},)
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
    client = boto3.client('ses', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,region_name=settings.AWS_REGION)

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
