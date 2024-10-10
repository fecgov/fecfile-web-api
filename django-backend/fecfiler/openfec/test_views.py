from django.test import TestCase, RequestFactory
from fecfiler.user.models import User
from .views import OpenfecViewSet
from unittest.mock import Mock, patch


class OpenfecViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_get_committee_no_override(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            request = self.factory.get("/api/v1/openfec/C12345678/committee/")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_requests.get.return_value = mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = None
                response = OpenfecViewSet.as_view({"get": "committee"})(
                    request, pk="C12345678"
                )
                self.assertEqual(response.status_code, 200)

    def test_get_committee_no_override_from_test_efo(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            request = self.factory.get("/api/v1/openfec/C12345678/committee/")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_requests.get.return_value = mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}
                response = OpenfecViewSet.as_view({"get": "committee"})(
                    request, pk="C12345678"
                )
                self.assertEqual(response.status_code, 200)

    def test_get_committee_override_data_not_found(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            settings.BASE_DIR = "fecfiler/"
            request = self.factory.get("/api/v1/openfec/C87654321/committee/")
            request.user = self.user
            response = OpenfecViewSet.as_view({"get": "committee"})(
                request, pk="C87654321"
            )
            self.assertEqual(response.status_code, 500)

    def test_get_committee_from_production(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            settings.FEC_API = "https://not-real.api/"
            settings.FEC_API_KEY = "MOCK_KEY"
            request = self.factory.get("/api/v1/openfec/C12345678/committee/")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                was_called_with = []
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}

                def mock_get(*args, **kwargs):
                    was_called_with.append([args, kwargs])
                    return mock_response

                mock_requests.get = mock_get

                response = OpenfecViewSet.as_view({"get": "committee"})(
                    request, pk="C12345678"
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(was_called_with), 1)
                called_with_args = was_called_with[0][0]
                self.assertIn(
                    "https://not-real.api/committee/C12345678/?api_key=MOCK_KEY",
                    called_with_args
                )

    def test_get_committee_from_test(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            settings.FEC_API_STAGE = "https://stage.not-real.api/"
            settings.FEC_API_KEY = "MOCK_KEY"
            request = self.factory.get("/api/v1/openfec/C12345678/committee/")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                was_called_with = []
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}

                def mock_get(*args, **kwargs):
                    was_called_with.append([args, kwargs])
                    return mock_response

                mock_requests.get = mock_get

                response = OpenfecViewSet.as_view({"get": "committee"})(
                    request, pk="C12345678"
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(was_called_with), 1)
                called_with_args = was_called_with[0][0]
                self.assertIn(
                    "https://stage.not-real.api/efile/test-form1/",
                    called_with_args
                )

    def test_get_filings_invalid_resp(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            request = self.factory.get("/api/v1/openfec/C00100230/f1_filing/")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_requests.get.return_value = mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"results": []}
                response = OpenfecViewSet.as_view({"get": "f1_filing"})(
                    request, pk="C00100230"
                )
                self.assertEqual(response.status_code, 200)

    def test_get_filings_happy_path(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            request = self.factory.get("/api/v1/openfec/C00100230/f1_filing/")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_requests.get.return_value = mock_response = Mock()
                mock_response.status_code = 200
                mock_response_object = {}
                mock_response_object["results"] = [{}]
                mock_response_object["results"][0]["form_type"] = "F1"
                mock_response.json.return_value = mock_response_object
                response = OpenfecViewSet.as_view({"get": "f1_filing"})(
                    request, pk="C00100230"
                )
                self.assertEqual(response.status_code, 200)

    def test_get_filings_from_test_efo_happy_path(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            request = self.factory.get("/api/v1/openfec/C00100230/f1_filing/")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_requests.get.return_value = mock_response = Mock()
                mock_response.status_code = 200
                mock_response_object = {}
                mock_response_object["results"] = [{}]
                mock_response_object["results"][0]["form_type"] = "F1"
                mock_response.json.return_value = mock_response_object
                response = OpenfecViewSet.as_view({"get": "f1_filing"})(
                    request, pk="C00100230"
                )
                self.assertEqual(response.status_code, 200)

    def test_query_filings_from_test_efo(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            request = self.factory.get("/api/v1/openfec/query_filings/?query=C00")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_requests.get.return_value = mock_response = Mock()
                mock_response.status_code = 200
                mock_response_object = {}
                mock_response_object["results"] = [{}]
                mock_response_object["results"][0]["form_type"] = "F1"
                mock_response.json.return_value = mock_response_object
                response = OpenfecViewSet.as_view({"get": "f1_filing"})(
                    request, pk="C00100230"
                )
                self.assertEqual(response.status_code, 200)
