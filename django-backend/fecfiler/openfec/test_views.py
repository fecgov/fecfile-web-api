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
            settings.FLAG__EFO_TARGET = "PRODUCTION"
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

    def test_get_committee_from_test_efo(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__EFO_TARGET = "TEST"
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

    def test_get_committee_override_data_not_found(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__EFO_TARGET = "PRODUCTION"
            settings.BASE_DIR = "fecfiler/"
            request = self.factory.get("/api/v1/openfec/C87654321/committee/")
            request.user = self.user
            response = OpenfecViewSet.as_view({"get": "committee"})(
                request, pk="C87654321"
            )
            self.assertEqual(response.status_code, 500)

    def test_get_committee_override_happy_path(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__EFO_TARGET = "PRODUCTION"
            settings.BASE_DIR = "fecfiler/"
            request = self.factory.get("/api/v1/openfec/C12345678/committee/")
            request.user = self.user
            response = OpenfecViewSet.as_view({"get": "committee"})(
                request, pk="C12345678"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["results"][0]["committee_id"], "C12345678")
            self.assertEqual(
                response.data["results"][0]["name"], "Test Committee"
            )
            self.assertEqual(response.data["results"][0]["committee_type"], "O")

    def test_get_filings_invalid_resp(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__EFO_TARGET = "PRODUCTION"
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
            settings.FLAG__EFO_TARGET = "PRODUCTION"
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
