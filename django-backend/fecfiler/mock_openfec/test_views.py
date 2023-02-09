from django.test import TestCase, RequestFactory
from fecfiler.authentication.models import Account
from .views import MockCommitteeDetailViewSet, MockRecentFilingsViewSet
from unittest.mock import Mock, patch


class MockCommitteeDetailViewSetTest(TestCase):
    fixtures = [
        "test_efo_committee_accounts",
        "test_committee_accounts",
        "test_accounts",
    ]

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()

    def test_get_committee_data_happy_path(self):
        request = self.factory.get(
            "/api/v1/mock_openfec/committee/C00100230/"
        )
        request.user = self.user
        response = MockCommitteeDetailViewSet.as_view({
            "get": "retrieve"
        })(request, pk='C00100230')
        self.assertEqual(response.status_code, 200)

    def test_get_committee_data_cid_not_found(self):
        request = self.factory.get(
            "/api/v1/mock_openfec/committee/C12345678/"
        )
        request.user = self.user
        with patch('fecfiler.mock_openfec.views.requests') as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = None
            response = MockCommitteeDetailViewSet.as_view({
                "get": "retrieve"
            })(request, pk='C12345678')
            self.assertEqual(response.status_code, 200)


class MockRecentFilingsViewSetTest(TestCase):
    fixtures = [
        "test_efo_committee_accounts",
        "test_committee_accounts",
        "test_accounts",
    ]

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()

    def test_get_recent_filings_happy_path(self):
        request = self.factory.get(
            "/api/v1/mock_openfec/filings/C00100230/"
        )
        request.user = self.user
        with patch('fecfiler.mock_openfec.views.requests') as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response_object = {}
            mock_response_object['results'] = [{}]
            mock_response_object['results'][0]['form_type'] = 'F1'
            mock_response.json.return_value = mock_response_object
            response = MockRecentFilingsViewSet.as_view({
                "get": "retrieve"
            })(request, pk='C00100230')
            self.assertEqual(response.status_code, 200)

    def test_get_recent_filings_invalid_resp(self):
        request = self.factory.get(
            "/api/v1/mock_openfec/filings/C00100230/"
        )
        request.user = self.user
        with patch('fecfiler.mock_openfec.views.requests') as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = None
            response = MockRecentFilingsViewSet.as_view({
                "get": "retrieve"
            })(request, pk='C00100230')
            self.assertEqual(response.status_code, 200)
