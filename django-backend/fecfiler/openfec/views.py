from rest_framework import viewsets
from django.http.response import HttpResponse, HttpResponseBadRequest
from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.mock_openfec.mock_endpoints import query_filings, committee
import requests
import fecfiler.settings as settings
from fecfiler.committee_accounts.utils import (
    check_can_create_committee_account,
    retrieve_recent_f1,
)

import structlog

logger = structlog.get_logger(__name__)


class OpenfecViewSet(viewsets.GenericViewSet):
    @action(detail=True)
    def committee(self, request, pk=None):
        check_can_create = request.query_params.get("check_can_create")
        if check_can_create == "true" and not check_can_create_committee_account(
            pk, request.user
        ):
            return HttpResponseBadRequest()
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
