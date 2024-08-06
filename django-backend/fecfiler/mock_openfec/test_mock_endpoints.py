from django.test import TestCase
from django.core.management import call_command
from fecfiler.mock_openfec.mock_endpoints import query_filings
from unittest.mock import patch


class MockEndpointsTest(TestCase):

    def setUp(self):
        pass

    def test_query_filings(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "REDIS"

            call_command("load_committee_data")
            response = query_filings("NOT FINDABLE", "F3")
            self.assertEqual(len(response["results"]), 0)
            response = query_filings("NOT FINDABLE", "F1")
            self.assertEqual(len(response["results"]), 0)
            response = query_filings("st Com", "F1")
            self.assertEqual(len(response["results"]), 2)
