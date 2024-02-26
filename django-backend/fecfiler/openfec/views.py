from rest_framework import viewsets
from django.http.response import HttpResponse, HttpResponseServerError
from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.mock_openfec.views import MockOpenfecViewSet
from fecfiler.mock_openfec.mock_endpoints import query_filings
import requests
from fecfiler.settings import (
    FEC_API_COMMITTEE_LOOKUP_IDS_OVERRIDE,
    FEC_API_KEY,
    MOCK_OPENFEC_URL,
    BASE_DIR,
    FEC_API,
)

import os
import json
import structlog

logger = structlog.get_logger(__name__)


class OpenfecViewSet(viewsets.ModelViewSet):
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
    def filings(self, request, pk=None):
        headers = {"Content-Type": "application/json"}
        params = {"api_key": FEC_API_KEY, "committee_id": pk, "sort": "-receipt_date"}

        resp = requests.get(f"{FEC_API}efile/filings/", headers=headers, params=params)
        retval = get_recent_f1_from_openfec_resp(resp)
        if not retval:
            params["per_page"] = 1
            params["page"] = 1
            params["form_type"] = "F1"
            resp = requests.get(f"{FEC_API}filings/", headers=headers, params=params)
            retval = get_recent_f1_from_openfec_resp(resp)

        return Response(retval)

    @action(detail=False)
    def query_filings(self, request):
        query = request.query_params.get("query")
        form_type = request.query_params.get("form_type")
        if MOCK_OPENFEC_URL:
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


def get_recent_f1_from_openfec_resp(resp: requests.Response):
    if resp:
        try:
            filing_list = resp.json()["results"]
            return next(
                (
                    filing
                    for filing in filing_list
                    if filing["form_type"].startswith("F1")
                ),
                None,
            )
        except Exception as error:
            logger.error(
                f"Failed to process response from {resp.url} due to error: {str(error)}"
            )
    return None


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
