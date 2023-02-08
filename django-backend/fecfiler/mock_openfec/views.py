from .models import MockCommitteeDetail
from .serializers import MockCommitteeDetailSerializer
from rest_framework import viewsets
from django.http.response import HttpResponse
from rest_framework.response import Response
import requests
from fecfiler.settings import FEC_API, FEC_API_KEY


class MockCommitteeDetailViewSet(viewsets.ModelViewSet):

    def retrieve(self, request, pk=None):
        queryset = MockCommitteeDetail.objects.all()
        try:
            mock_committee_detail = queryset.get(committee_id=pk)
        except MockCommitteeDetail.DoesNotExist:
            resp = requests.get(f'{FEC_API}committee/{pk}/?api_key={FEC_API_KEY}')
            return HttpResponse(resp)
        serializer = MockCommitteeDetailSerializer(mock_committee_detail)
        retval = {  # same as api.open.fec.gov
            "api_version": "1.0",
            "results": [
                serializer.data,
            ],
            "pagination": {
                "pages": 1,
                "per_page": 20,
                "count": 1,
                "page": 1
            }
        }
        return Response(retval)
