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
# API view functionality for GET DELETE and PUT
# Exception handling is taken care to validate the committeinfo


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
            #'reason' :request.data.get('text'),
            'reason' :request.data.get('reason'),
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
