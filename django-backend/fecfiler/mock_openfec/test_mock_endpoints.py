from django.test import TestCase
from django.core.management import call_command
from fecfiler.settings import MOCK_OPENFEC_REDIS_URL
from fecfiler.mock_openfec.mock_endpoints import query_filings
import redis
import json
from fecfiler.mock_openfec.mock_endpoints import COMMITTEE_DATA_REDIS_KEY


class MockEndpointsTest(TestCase):

    def setUp(self):
        pass

    def test_query_filings(self):
        call_command("load_committee_data")
        response = query_filings("NOT FINDABLE", "F3")
        self.assertEqual(len(response["results"]), 0)
        response = query_filings("NOT FINDABLE", "F1")
        self.assertEqual(len(response["results"]), 0)
        response = query_filings("st Com", "F1")
        self.assertEqual(len(response["results"]), 1)
