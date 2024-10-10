from math import ceil
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
        match settings.FLAG__COMMITTEE_DATA_SOURCE:
            case "PRODUCTION":
                response = requests.get(
                    f"{settings.FEC_API}committee/{pk}/?api_key={settings.FEC_API_KEY}"
                )
                return HttpResponse(response)
            case "TEST":
                return Response(self.get_committee_from_test_efo(pk))
            case "REDIS":
                response = committee(pk)
                return Response(response)
            case _:
                error_message = f"""FLAG__COMMITTEE_DATA_SOURCE improperly configured: {
                    settings.FLAG__COMMITTEE_DATA_SOURCE
                }"""
                response = Response()
                response.status_code = 500
                response.content = error_message
                logger.exception(Exception(error_message))
                return response

    def get_committee_from_test_efo(self, pk=None):
        headers = {"Content-Type": "application/json"}
        params = {
            "api_key": settings.FEC_API_KEY,
            "committee_id": pk,
        }
        endpoint = f"{settings.FEC_API_STAGE}efile/test-form1/"
        response = requests.get(endpoint, headers=headers, params=params)
        response_data = response.json()
        results = response_data.get('results', [])
        if results:
            results[0]['name'] = results[0].get('committee_name', None)

        return {
            'api_version': response_data.get('api_version', None),
            'results': response_data.get('results', [])[:1],
        }

    def query_filings_from_test_efo(self, query):
        headers = {"Content-Type": "application/json"}
        params = {
            "api_key": settings.FEC_API_KEY,
            "per_page": 100,
        }
        endpoint = f"{settings.FEC_API_STAGE}efile/test-form1/"
        results = []
        page = 1
        last_good_response = {}
        while True:
            params["page"] = page
            response = requests.get(endpoint, headers=headers, params=params).json()

            if not response.get('results'):
                break

            last_good_response = response
            results += response['results']
            page += 1

            if page >= response['pagination']['pages']:
                break

        matching_results = []
        found_committees = {}
        for result in results:
            if query in result['committee_name'] or query in result['committee_id']:
                if not found_committees.get(result['committee_id']):
                    found_committees[result['committee_id']] = result['committee_name']
                    matching_results.append(result)

        return {
            'api_version': last_good_response.get('api_version', None),
            'results': matching_results[:20],
            'pagination': {
                'per_page': 20,
                'count': len(matching_results),
                'page': 1,
                'pages': ceil(len(matching_results) / 20)
            }
        }

    @action(detail=True)
    def f1_filing(self, request, pk=None):
        return Response(retrieve_recent_f1(pk))

    @action(detail=False)
    def query_filings(self, request):
        query = request.query_params.get("query")
        form_type = request.query_params.get("form_type")
        match settings.FLAG__COMMITTEE_DATA_SOURCE:
            case "PRODUCTION":
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
            case "TEST":
                return Response(self.query_filings_from_test_efo(query))
            case "REDIS":
                return Response(query_filings(query, form_type))
            case _:
                error_message = f"""FLAG__COMMITTEE_DATA_SOURCE improperly configured: {
                    settings.FLAG__COMMITTEE_DATA_SOURCE
                }"""
                response = Response()
                response.status_code = 500
                response.content = error_message
                logger.exception(Exception(error_message))
                return response


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

    endpoints = []
    match settings.FLAG__COMMITTEE_DATA_SOURCE:
        case "PRODUCTION":
            endpoints = [
                f"{settings.FEC_API}efile/form1/",
                f"{settings.FEC_API}committee/{committee_id}/"
            ]
        case "TEST":
            endpoints = [f"{settings.FEC_API_STAGE}efile/test-form1/"]
        case _:
            error_message = f"""FLAG__COMMITTEE_DATA_SOURCE improperly configured: {
                settings.FLAG__COMMITTEE_DATA_SOURCE
            }"""
            response = Response()
            response.status_code = 500
            response.content = error_message
            logger.exception(Exception(error_message))
            return response

    for endpoint in endpoints:
        response = requests.get(endpoint, headers=headers, params=params).json()
        results = response["results"]
        if len(results) > 0:
            return results[0]
