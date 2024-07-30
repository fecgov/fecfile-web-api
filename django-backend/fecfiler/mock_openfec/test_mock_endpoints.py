from django.test import TestCase
from django.core.management import call_command
from fecfiler.mock_openfec.mock_endpoints import query_filings


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
        self.assertEqual(len(response["results"]), 2)
