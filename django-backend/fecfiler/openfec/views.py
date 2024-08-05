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

        logger.debug(f"\n\nHi, I'm here! {pk}\n\n")
        if settings.FLAG__EFO_TARGET == "PRODUCTION":
            response = requests.get(
                f"{settings.FEC_API}committee/{pk}/?api_key={settings.FEC_API_KEY}"
            )
            return HttpResponse(response)
        else:
            return HttpResponse(self.get_committee_from_test_efo(pk))


    def get_committee_from_test_efo(self, pk=None):
        headers = {"Content-Type": "application/json"}
        params = {
            "api_key": settings.FEC_API_KEY,
            "per_page": 100,
        }
        endpoint = f"{settings.FEC_API}/efile/test-form1/"
        results = []
        page = 1
        last_good_response = None
        while True:
            params["page"] = page
            response = requests.get(endpoint, headers=headers, params=params).json()

            if not response.get('results'):
                break

            last_good_response = response
            results.append(response['results'])
            page += 1

            if page >= response['pagination']['pages']:
                break

        matching_results = []
        for result in results:
            if pk in result['committee_name'] or pk in result['committee_id']:
                matching_results.append(result)

        if last_good_response is not None:
            last_good_response['results'] = matching_results
        return last_good_response



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
    filings older than 6 months. The other endpoint returns a committee's current data
    informed by their most recent F1 and F2 filings."""
    headers = {"Content-Type": "application/json"}
    params = {
        "api_key": settings.FEC_API_KEY,
        "committee_id": committee_id,
    }

    if settings.FLAG__EFO_TARGET == "PRODUCTION":
        endpoints = [
            f"{settings.FEC_API}efile/form1/",
            f"{settings.FEC_API}committee/{committee_id}/"
        ]
    else:
        endpoints = [f"{settings.FEC_API}/efile/test-form1/"]

    logger.debug(f"\n\nF1 Retrieval Endpoints: {endpoints}\n\n")
    for endpoint in endpoints:
        response = requests.get(endpoint, headers=headers, params=params).json()
        logger.debug(f"\n\nResults:\n\n{response}\n\n")
        results = response["results"]
        if len(results) > 0:
            return results[0]
