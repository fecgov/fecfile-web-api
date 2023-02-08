from .models import MockCommitteeDetail
from .serializers import MockCommitteeDetailSerializer
from rest_framework import viewsets
from django.http.response import HttpResponse
from rest_framework.response import Response
import requests
from fecfiler.settings import FEC_API, FEC_API_KEY

import logging

logger = logging.getLogger(__name__)


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


class MockRecentFilingsViewSet(viewsets.ModelViewSet):

    def retrieve(self, request, pk=None):

        headers = {
            'Content-Type': 'application/json'
        }
        params = {
            'api_key': FEC_API_KEY,
            'committee_id': pk,
            'sort': '-receipt_date'
        }

        resp = requests.get(f'{FEC_API}efile/filings/', headers=headers, params=params)
        retval = get_recent_f1_from_openfec_resp(resp)
        if not retval:
            params['per_page'] = 1
            params['page'] = 1
            params['form_type'] = 'F1'
            resp = requests.get(f'{FEC_API}filings/', headers=headers, params=params)
            retval = get_recent_f1_from_openfec_resp(resp)

        return Response(retval)


def get_recent_f1_from_openfec_resp(resp: requests.Response):
    if resp:
        try:
            filing_list = resp.json()['results']
            return next((
                filing for filing in filing_list if filing['form_type'].startswith('F1')
            ), None)
        except Exception as error:
            logger.error(
                f'Failed to process response from {resp.url} due to error: {str(error)}'
            )
    return None
