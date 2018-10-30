from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .models import CommitteeInfo, Committee
from .serializers import CommitteeInfoSerializer, CommitteeSerializer
import json
import os
from django.views.decorators.csrf import csrf_exempt
import logging
import datetime
import magic
from django.http import JsonResponse

# API view functionality for GET DELETE and PUT
# Exception handling is taken care to validate the committeinfo
logger = logging.getLogger(__name__)

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
#@csrf_exempt
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
            'file': request.data.get('file'),
            
        }

        serializer = CommitteeInfoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def update_f99_info(request):
    """
    Updates the last unsubmitted comm_info object only. you can use this to change the 'text' and 'is_submitted' field as well as any other field.
    """
    # update details of a single comm_info
    if request.method == 'POST':
        try:
            # fetch last comm_info object created, else return 404  
            comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username).last()
        except CommitteeInfo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = CommitteeInfoSerializer(comm_info, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def submit_comm_info(request):
    """
    Submits the last unsubmitted but saved comm_info object only. Returns the saved object with updated timestamp and comm_info details
    """
    #import ipdb; ipdb.set_trace()
    if request.method == 'POST':
        try:
            comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username).last()
            if comm_info:
                new_data = comm_info.__dict__
                new_data["is_submitted"]=True
                new_data["updated_at"]=datetime.datetime.now()
                serializer = CommitteeInfoSerializer(comm_info, data=new_data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)                    
        except:
            return Response({"error":"There is no unsubmitted data. Please create f99 form object before submitting."}, status=status.HTTP_400_BAD_REQUEST)

    else:
        return Response({"error":"ERRCODE: FEC02. Error occured while trying to submit form f99."}, status=status.HTTP_400_BAD_REQUEST)

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
        #import ipdb; ipdb.set_trace();
        return Response(filtered_d)    
    
    
@api_view(['POST'])
def update_committee(request, cid):   
    # # update details of a single comm
    if request.method == 'POST':
         serializer = CommitteeSerializer(comm, data=request.data)
         if serializer.is_valid():
             serializer.save()
             return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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
            'file': request.data.get('file'),
        }
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    try:        
        comm = Committee.objects.get(committeeid=request.data.get('committeeid'))

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
    
    if comm.zipcode!=int(request.data.get('zipcode')):
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
    if 'file' in request.data:
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
            
    if len(errormess)==0:
        errormess.append('Validation successful!')
        return JsonResponse(errormess, status=200, safe=False)
    else:
        return JsonResponse(errormess, status=400, safe=False)

