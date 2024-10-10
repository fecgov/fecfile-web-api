from django.test import TestCase, RequestFactory
from fecfiler.user.models import User
from .views import OpenfecViewSet
from unittest.mock import Mock, patch


class OpenfecViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_get_committee_from_production(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            settings.FEC_API = "https://not-real.api/"
            settings.FEC_API_KEY = "MOCK_KEY"
            request = self.factory.get("/api/v1/openfec/C12345678/committee/")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}
                mock_requests.get = Mock()
                mock_requests.get.return_value = mock_response

                response = OpenfecViewSet.as_view({"get": "committee"})(
                    request, pk="C12345678"
                )
                was_called_with = mock_requests.get.call_args.args
                self.assertEqual(response.status_code, 200)
                self.assertNotEqual(len(was_called_with), 0)
                self.assertIn(
                    "https://not-real.api/committee/C12345678/?api_key=MOCK_KEY",
                    was_called_with
                )

    def test_get_committee_from_test(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            settings.FEC_API_STAGE = "https://stage.not-real.api/"
            settings.FEC_API_KEY = "MOCK_KEY"
            request = self.factory.get("/api/v1/openfec/C12345678/committee/")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}
                mock_requests.get = Mock()
                mock_requests.get.return_value = mock_response

                response = OpenfecViewSet.as_view({"get": "committee"})(
                    request, pk="C12345678"
                )
                was_called_with = mock_requests.get.call_args.args
                self.assertEqual(response.status_code, 200)
                self.assertNotEqual(len(was_called_with), 0)
                self.assertIn(
                    "https://stage.not-real.api/efile/test-form1/",
                    was_called_with
                )

    def test_get_committee_from_redis(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "REDIS"
            request = self.factory.get("/api/v1/openfec/C12345678/committee/")
            request.user = self.user
            with patch("fecfiler.openfec.views.committee") as mock_committee:
                OpenfecViewSet.as_view({"get": "committee"})(
                    request, pk="C12345678"
                )
                was_called_with = mock_committee.call_args.args or []
                self.assertNotEqual(len(was_called_with), 0)
                self.assertIn(
                    "C12345678",
                    was_called_with
                )

    def test_get_committee_from_invalid(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            with patch("fecfiler.utils") as mock_utils:
                mock_utils.UNIT_TESTS_RUNNING = True
                def error_raiser(exception, context):
                    print("I GOT CALLED")
                    raise exception

                mock_utils.custom_exception_handler = error_raiser

                settings.FLAG__COMMITTEE_DATA_SOURCE = "INVALID"
                request = self.factory.get("/api/v1/openfec/C12345678/committee/")
                request.user = self.user

                expected_error = "FLAG__COMMITTEE_DATA_SOURCE improperly configured: INVALID"
                response = OpenfecViewSet.as_view({"get": "committee"})(request, pk="C12345678")
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.content.decode(), expected_error)

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
