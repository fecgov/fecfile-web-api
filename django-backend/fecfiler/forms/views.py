from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CommitteeInfo, Committee
from .serializers import CommitteeInfoSerializer, CommitteeSerializer
import json
import os
from django.views.decorators.csrf import csrf_exempt
import logging
# API view functionality for GET DELETE and PUT
# Exception handling is taken care to validate the committeinfo
logger = logging.getLogger(__name__)

@api_view(['GET'])
def fetch_f99_info(request):

    """"
    Fetches the last unsubmitted comm_info object saved in db. This obviously is for the object persistence between logins.
    """
    try: 
        # fetch last comm_info object created that is not submitted, else return None
        comm_info = CommitteeInfo.objects.filter(committeeid=request.user.username,  is_submitted=False).last() #,)
    except CommitteeInfo.DoesNotExist:
        return Response({}) #status=status.HTTP_404_NOT_FOUND)

    # get details of a single comm_info
    if request.method == 'GET':
        serializer = CommitteeInfoSerializer(comm_info)
        return Response(serializer.data)    
    # delete a single comm_info
    # elif request.method == 'DELETE':
    #     return Response({})


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
            'reason' :request.data.get('text'),
            'zipcode': request.data.get('zipcode'),
            'treasurerlastname': request.data.get('treasurerlastname'),
            'treasurerfirstname': request.data.get('treasurerfirstname'),
            'treasurermiddlename': request.data.get('treasurermiddlename'),
            'treasurerprefix': request.data.get('treasurerprefix'),
            'treasurersuffix': request.data.get('treasurersuffix'),
            'is_submitted': request.data.get('is_submitted'),
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
    if request.method == 'POST':
        serializer = CommitteeInfoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        '''try:
	    submit_comm_info = CommitteeInfo.objects.all
        except CommitteeInfo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)'''


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
        #import pdb; pdb.set_trace()
        #comm = Committee.objects.get(committeeid=request.user.username)
        comm = Committee.objects.filter(committeeid=request.user.username).last() 
    except Committee.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)

    # get details of a single comm
    if request.method == 'GET':
        serializer = CommitteeSerializer(comm)
        return Response(serializer.data)    

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
            'treasurersuffix': request.data.get('treasurersuffix')
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
            'treasurersuffix': request.data.get('treasurersuffix')
        }
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    try:
        #   import pdb; pdb.set_trace()
        comm = Committee.objects.get(committeeid=request.data.get('committeeid'))

    except Committee.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    count = 0

    if comm.committeename!=request.data.get('committeename'):
        logger.error('Committee Name')
        count = count +1

    if comm.street1!=request.data.get('street1'):
        logger.error('Street1')
        count = count +1
    
    if comm.street2!=request.data.get('street2'):
        logger.error('Street2')
        count = count +1

    if comm.city!=request.data.get('city'):
        logger.error('City')
        count = count +1
    
    if comm.state!=request.data.get('state'):
        logger.error('State')
        count = count +1

    if comm.treasurerlastname!=request.data.get('treasurerlastname'):
        logger.error('treasurer last name')
        count = count +1
    
    if comm.treasurerfirstname!=request.data.get('treasurerfirstname'):
        logger.error('treasurer first name')
        count = count +1

    if comm.treasurermiddlename!=request.data.get('treasurermiddlename'):
        logger.error('treasurer middle name')
        count = count +1

    if comm.treasurerprefix!=request.data.get('treasurerprefix'):
        logger.error('Treasurer Prefix')
        count = count +1

    if comm.treasurersuffix!=request.data.get('treasurersuffix'):
        logger.error('Treassurer Suffix')
        count = count +1

    if len(request.data.get('text'))>20000:
        logger.error('Text greater than 20000')
        count = count +1

    conditions = [request.data.get('reason')=='MST', request.data.get('reason')=='MSM', request.data.get('reason')=='MSI', request.data.get('reason')=='MSW']
    if not any(conditions):
        logger.error('Invalid Reason')
        count = count +1

    if count==0:
        return Response(status=status.HTTP_201_CREATED)
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)