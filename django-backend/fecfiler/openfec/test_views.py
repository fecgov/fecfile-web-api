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
            with patch("fecfiler.openfec.views.mock_committee") as mock_committee:
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
            settings.FLAG__COMMITTEE_DATA_SOURCE = "INVALID"
            request = self.factory.get("/api/v1/openfec/C12345678/committee/")
            request.user = self.user

            error = "FLAG__COMMITTEE_DATA_SOURCE improperly configured: INVALID"
            response = OpenfecViewSet.as_view({"get": "committee"})(
                request,
                pk="C12345678"
            )
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.content.decode(), error)

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

    def test_f1_filings_from_test(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            settings.FEC_API_STAGE = "https://stage.not-real.api/"
            request = self.factory.get("/api/v1/openfec/query_filings/?query=C12345678")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_requests.get.return_value = mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"results": [
                    {"form_type": "F1"}
                ]}
                response = OpenfecViewSet.as_view({"get": "f1_filing"})(
                    request, pk="C12345678"
                )
                self.assertEqual(response.status_code, 200)
                called_with = mock_requests.get.call_args.args or [[]]
                self.assertIn(
                    "https://stage.not-real.api/efile/test-form1/",
                    called_with
                )

    def test_f1_filings_from_production(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            settings.FEC_API = "https://not-real.api/"
            request = self.factory.get("/api/v1/openfec/query_filings/?query=C12345678")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                called_with = []

                mock_response_first = Mock()
                mock_response_first.status_code = 200
                mock_response_first.json.return_value = {"results": []}
                mock_response_second = Mock()
                mock_response_second.status_code = 200
                mock_response_second.json.return_value = {"results": [
                    {"form_type": "F1"}
                ]}
                responses = [mock_response_first, mock_response_second]

                def get_mocked_responses(*args, **kwargs):
                    called_with.append(args)
                    return responses.pop(0)

                mock_requests.get = get_mocked_responses
                response = OpenfecViewSet.as_view({"get": "f1_filing"})(
                    request, pk="C12345678"
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    "https://not-real.api/efile/form1/",
                    called_with[0]
                )
                self.assertIn(
                    "https://not-real.api/committee/C12345678/",
                    called_with[1]
                )

    def test_f1_filings_from_redis(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "REDIS"
            request = self.factory.get(
                "/api/v1/openfec/query_filings/?query=C12345678"
            )
            request.user = self.user
            with patch("fecfiler.openfec.views.mock_committee") as mock_query:
                mock_query.return_value = {}
                response = OpenfecViewSet.as_view({"get": "f1_filing"})(
                    request, pk="C12345678"
                )
                self.assertEqual(response.status_code, 200)
                called_with = mock_query.call_args.args or [[]]
                self.assertIn("C12345678", called_with)

    def test_f1_filings_from_invalid(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "INVALID"
            request = self.factory.get(
                "/api/v1/openfec/query_filings/?query=C12345678"
            )
            request.user = self.user
            response = OpenfecViewSet.as_view({"get": "f1_filing"})(
                request, pk="C12345678"
            )
            error = "FLAG__COMMITTEE_DATA_SOURCE improperly configured: INVALID"
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.content.decode(), error)

    def test_query_filings_from_test(self):
        pages = [
            {
                "results": [
                    {
                        "committee_id": "C11111111",
                        "committee_name": "Miss 1"
                    },
                    {
                        "committee_id": "C11111112",
                        "committee_name": "Miss 2"
                    },
                    {
                        "committee_id": "C21111111",
                        "committee_name": "Match 1"
                    },
                ],
                "pagination": {
                    "pages": 3
                }
            },
            {
                "results": [
                    {
                        "committee_id": "C11111116",
                        "committee_name": "Miss 3"
                    },
                    {
                        "committee_id": "C21111112",
                        "committee_name": "Match 2"
                    },
                    {
                        "committee_id": "C11111119",
                        "committee_name": "Miss 4"
                    },
                ],
                "pagination": {
                    "pages": 3
                }
            },
            {
                "results": [
                    {
                        "committee_id": "C21111113",
                        "committee_name": "Match 3"
                    },
                    {
                        "committee_id": "C11111121",
                        "committee_name": "Miss 5"
                    },
                    {
                        "committee_id": "C21111113",
                        "committee_name": "Dupe 1"
                    },
                ],
                "pagination": {
                    "pages": 3
                }
            },
        ]

        def mock_filing_pages(*args, **kwargs):
            mock = Mock()
            page = {"results": []}
            if len(pages) > 0:
                page = pages.pop(0)

            mock.json.return_value = page

            return mock

        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            settings.FEC_API_STAGE = "https://stage.not-real.api/"
            request = self.factory.get("/api/v1/openfec/query_filings/?query=C2111")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_requests.get = mock_filing_pages
                response = OpenfecViewSet.as_view({"get": "query_filings"})(
                    request
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.data["results"]), 3)

                found_ids = []
                found_names = []
                for result in response.data["results"]:
                    found_ids.append(result["committee_id"])
                    found_names.append(result["committee_name"])

                self.assertEqual(found_names, ["Match 1", "Match 2", "Match 3"])
                self.assertEqual(found_ids, ["C21111111", "C21111112", "C21111113"])

    def test_query_filings_from_production(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            settings.FEC_API = "https://not-real.api/"
            request = self.factory.get("/api/v1/openfec/query_filings/?query=C12345678")
            request.user = self.user
            with patch("fecfiler.openfec.views.requests") as mock_requests:
                mock_requests.get.return_value = mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"results": [
                    {"committee_id": "C12345678", "committee_name": "TEST MATCH"}
                ]}
                response = OpenfecViewSet.as_view({"get": "query_filings"})(
                    request
                )
                self.assertEqual(response.status_code, 200)
                called_with = mock_requests.get.call_args.args or [[]]
                self.assertIn(
                    "https://not-real.api/filings/",
                    called_with
                )

    def test_query_filings_from_redis(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "REDIS"
            request = self.factory.get(
                "/api/v1/openfec/query_filings/?query=C12345678"
            )
            request.user = self.user
            with patch("fecfiler.openfec.views.mock_query_filings") as mock_query:
                mock_query.return_value = {}
                response = OpenfecViewSet.as_view({"get": "query_filings"})(
                    request
                )
                self.assertEqual(response.status_code, 200)
                called_with = mock_query.call_args.args or [[]]
                self.assertIn("C12345678", called_with)

    def test_query_filings_from_invalid(self):
        with patch("fecfiler.openfec.views.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "INVALID"
            request = self.factory.get(
                "/api/v1/openfec/query_filings/?query=C12345678"
            )
            request.user = self.user
            response = OpenfecViewSet.as_view({"get": "query_filings"})(
                request
            )
            error = "FLAG__COMMITTEE_DATA_SOURCE improperly configured: INVALID"
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.content.decode(), error)
