from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CommitteeInfo
from .serializers import CommitteeInfoSerializer
import json
import os
# API view functionality for GET DELETE and PUT
# Exception handling is taken care to validate the committeinfo


@api_view(['GET', 'DELETE', 'PUT'])
def get_delete_update_comm_info(request, pk):
    try:
        comm_info = CommitteeInfo.objects.get(pk=pk)
    except CommitteeInfo.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # get details of a single comm_info
    if request.method == 'GET':
        serializer = CommitteeInfoSerializer(comm_info)
        return Response(serializer.data)    
    # delete a single comm_info
    # elif request.method == 'DELETE':
    #     return Response({})
    # # update details of a single comm_info
    # elif request.method == 'PUT':
    #     serializer = CommitteeInfoSerializer(comm_info, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#GET POST calls for form99

@api_view(['GET', 'POST'])
def get_post_comm_info(request):
    # get all comm info
    if request.method == 'GET':
        comm_info = CommitteeInfo.objects.all()
        serializer = CommitteeInfoSerializer(comm_info, many=True)
        return Response(serializer.data)
        
    # insert a new record for a comm_info
    elif request.method == 'POST':
        data = {
            'committeeid': request.data.get('committeeid'),
            'committeename': request.data.get('committeename'),
            'street1': request.data.get('street1'),
            'street2': request.data.get('street2'),
            'city': request.data.get('city'),
            'state': request.data.get('state'),
            'text': request.data.get('text'),
            'zipcode': int(request.data.get('zipcode')),
            'treasurerlastname': request.data.get('treasurerlastname'),
            'treasurerfirstname': request.data.get('treasurerfirstname'),
            'treasurermiddlename': request.data.get('treasurermiddlename'),
            'treasurerprefix': request.data.get('treasurerprefix'),
            'treasurersuffix': request.data.get('treasurersuffix')
        }


        serializer = CommitteeInfoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_f99_reasons(request):
    if request.method == 'GET':        
        try:
            from django.conf import settings
            reason_data = json.load(open(os.path.join(settings.BASE_DIR,'sys_data', "f99_default_reasons.json"),'r'))
            return Response(reason_data, status=status.HTTP_200_OK)
        except:
            return Response({'error':'ERR_0001: Server Error: F99 reasons file not retrievable.'}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
def get_committee(request, cid):
    try:
        comm = Committee.objects.get(committeeid=cid)
    except Committee.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

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
    # insert a new record for a comm
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
