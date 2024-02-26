from rest_framework import viewsets
from django.http.response import HttpResponse, HttpResponseServerError
from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.mock_openfec.mock_endpoints import query_filings
import requests
from fecfiler.settings import (
    FEC_API_COMMITTEE_LOOKUP_IDS_OVERRIDE,
    FEC_API_KEY,
    MOCK_OPENFEC_REDIS_URL,
    BASE_DIR,
    FEC_API,
)

import os
import json
import structlog

logger = structlog.get_logger(__name__)


class OpenfecViewSet(viewsets.GenericViewSet):
    @action(detail=True)
    def committee(self, request, pk=None):
        cids_to_override = (
            list(map(str.strip, FEC_API_COMMITTEE_LOOKUP_IDS_OVERRIDE.split(",")))
            if FEC_API_COMMITTEE_LOOKUP_IDS_OVERRIDE
            else []
        )
        cid_to_override = next((cid for cid in cids_to_override if cid == pk), None)
        if cid_to_override:
            mock_committee_account = get_test_efo_mock_committee_account(
                cid_to_override
            )
            if mock_committee_account:
                return Response(
                    {  # same as api.open.fec.gov
                        "api_version": "1.0",
                        "results": [
                            mock_committee_account,
                        ],
                        "pagination": {
                            "pages": 1,
                            "per_page": 20,
                            "count": 1,
                            "page": 1,
                        },
                    }
                )
            else:
                logger.error(
                    "Failed to find mock committee account data for "
                    "committee id to override: " + cid_to_override
                )
                return HttpResponseServerError()
        else:
            resp = requests.get(f"{FEC_API}committee/{pk}/?api_key={FEC_API_KEY}")
            return HttpResponse(resp)

    @action(detail=True)
    def f1_filing(self, request, pk=None):
        return Response(retrieve_recent_f1(pk))

    @action(detail=False)
    def query_filings(self, request):
        query = request.query_params.get("query")
        form_type = request.query_params.get("form_type")
        if MOCK_OPENFEC_REDIS_URL:
            response = query_filings(query, form_type)
        else:
            params = {
                "api_key": FEC_API_KEY,
                "q_filer": query,
                "sort": "-receipt_date",
                "form_type": form_type,
                "most_recent": True,
            }
            fec_response = requests.get(f"{FEC_API}filings/", params)
            response = fec_response.json()
        return Response(response)


def retrieve_recent_f1(committee_id):
    """Gets the most recent F1 filing
    First checks the realtime enpdpoint for a recent F1 filing.  If none is found, a request is
    made to a different endpoint that is updated nightly.  The realtime endpoint will have
    more recent filings, but does not provide filings older than 6 months.
    The nightly endpoint keeps a longer history"""
    headers = {"Content-Type": "application/json"}
    params = {
        "api_key": FEC_API_KEY,
        "committee_id": committee_id,
        "sort": "-receipt_date",
        "form_type": "F1",
    }
    endpoints = [f"{FEC_API}efile/filings/", f"{FEC_API}filings/"]
    for endpoint in endpoints:
        response = requests.get(endpoint, headers=headers, params=params).json()
        results = response["results"]
        if len(results) > 0:
            return results[0]


def get_test_efo_mock_committee_account(committee_id):
    mock_committee_accounts = get_test_efo_mock_committee_accounts()
    return next(
        (
            committee
            for committee in mock_committee_accounts
            if committee["committee_id"] == committee_id
        ),
        None,
    )


def get_test_efo_mock_committee_accounts():
    mock_committee_accounts_file = "committee_accounts.json"
    mock_committee_accounts_file_path = os.path.join(
        BASE_DIR, "openfec/test_efo_mock_data/", mock_committee_accounts_file
    )
    with open(mock_committee_accounts_file_path) as fp:
        return json.load(fp)
