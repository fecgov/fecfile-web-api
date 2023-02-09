from django.test import TestCase, RequestFactory
from fecfiler.authentication.models import Account
from .views import OpenfecViewSet
from unittest.mock import Mock, patch


class OpenfecViewSetTest(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_accounts",
    ]

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()

    def test_get_committee_no_override(self):
        request = self.factory.get(
            "/api/v1/openfec/C12345678/committee/"
        )
        request.user = self.user
        with patch('fecfiler.openfec.views.requests') as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = None
            response = OpenfecViewSet.as_view({
                "get": "committee"
            })(request, pk='C12345678')
            self.assertEqual(response.status_code, 200)

    def test_get_committee_override_data_not_found(self):
        with patch('fecfiler.openfec.views.base') as base:
            base.FEC_API_COMMITTEE_LOOKUP_IDS_OVERRIDE = 'C12345678'
            base.BASE_DIR = 'fecfiler/'
            request = self.factory.get(
                "/api/v1/openfec/C12345678/committee/"
            )
            request.user = self.user
            response = OpenfecViewSet.as_view({
                "get": "committee"
            })(request, pk='C12345678')
            self.assertEqual(response.status_code, 500)

    def test_get_committee_override_happy_path(self):
        with patch('fecfiler.openfec.views.base') as base:
            base.FEC_API_COMMITTEE_LOOKUP_IDS_OVERRIDE = 'C00100230'
            base.BASE_DIR = 'fecfiler/'
            request = self.factory.get(
                "/api/v1/openfec/C00100230/committee/"
            )
            request.user = self.user
            response = OpenfecViewSet.as_view({
                "get": "committee"
            })(request, pk='C00100230')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.data['results'][0]['committee_id'], 'C00100230'
            )
            self.assertEqual(
                response.data['results'][0]['name'], 'TEST_COMMITTEE_NAME5'
            )
            self.assertEqual(
                response.data['results'][0]['committee_type_full'], 'TEST_COMMITTEE_TYPE5'
            )

    def test_get_filings_invalid_resp(self):
        request = self.factory.get(
            "/api/v1/openfec/C00100230/filings/"
        )
        request.user = self.user
        with patch('fecfiler.openfec.views.requests') as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = None
            response = OpenfecViewSet.as_view({
                "get": "filings"
            })(request, pk='C00100230')
            self.assertEqual(response.status_code, 200)

    def test_get_filings_happy_path(self):
        request = self.factory.get(
            "/api/v1/openfec/C00100230/filings/"
        )
        request.user = self.user
        with patch('fecfiler.openfec.views.requests') as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response_object = {}
            mock_response_object['results'] = [{}]
            mock_response_object['results'][0]['form_type'] = 'F1'
            mock_response.json.return_value = mock_response_object
            response = OpenfecViewSet.as_view({
                "get": "filings"
            })(request, pk='C00100230')
            self.assertEqual(response.status_code, 200)
