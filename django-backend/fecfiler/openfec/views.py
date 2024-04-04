from rest_framework import viewsets
from django.http.response import HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.mock_openfec.mock_endpoints import query_filings, committee
import requests
import fecfiler.settings as settings

import structlog

logger = structlog.get_logger(__name__)


class OpenfecViewSet(viewsets.GenericViewSet):
    @action(detail=True)
    def committee(self, request, pk=None):
        response = committee(pk)
        if response:
            return Response(response)
        response = requests.get(
            f"{settings.FEC_API}committee/{pk}/?api_key={settings.FEC_API_KEY}"
        )
        return HttpResponse(response)

    @action(detail=True)
    def f1_filing(self, request, pk=None):
        return Response(retrieve_recent_f1(pk))

    @action(detail=False)
    def query_filings(self, request):
        query = request.query_params.get("query")
        form_type = request.query_params.get("form_type")
        if settings.MOCK_OPENFEC_REDIS_URL:
            response = query_filings(query, form_type)
        else:
            params = {
                "api_key": settings.FEC_API_KEY,
                "q_filer": query,
                "sort": "-receipt_date",
                "form_type": form_type,
                "most_recent": True,
            }
            fec_response = requests.get(f"{settings.FEC_API}filings/", params)
            response = fec_response.json()
        return Response(response)


def retrieve_recent_f1(committee_id):
    """Gets the most recent F1 filing
    First checks the realtime enpdpoint for a recent F1 filing.  If none is found,
    a request is made to a different endpoint that is updated nightly.
    The realtime endpoint will have more recent filings, but does not provide
    filings older than 6 months. The nightly endpoint keeps a longer history"""
    headers = {"Content-Type": "application/json"}
    params = {
        "api_key": settings.FEC_API_KEY,
        "committee_id": committee_id,
        "sort": "-receipt_date",
        "form_type": "F1",
    }
    endpoints = [f"{settings.FEC_API}efile/filings/", f"{settings.FEC_API}filings/"]
    for endpoint in endpoints:
        response = requests.get(endpoint, headers=headers, params=params).json()
        results = response["results"]
        if len(results) > 0:
            return results[0]
