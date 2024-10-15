from uuid import UUID
from django.test import RequestFactory, TestCase
from fecfiler.committee_accounts.models import Membership
from fecfiler.committee_accounts.views import (
    CommitteeMembershipViewSet,
    CommitteeViewSet
)

from fecfiler.user.models import User
from unittest.mock import Mock, patch


class CommitteeMemberViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee", "unaffiliated_users"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_remove_member(self):
        membership_uuid = UUID("136a21f2-66fe-4d56-89e9-0d1d4612741c")
        view = CommitteeMembershipViewSet()
        request = self.factory.get(
            f"/api/v1/committee-members/{membership_uuid}/remove-member"
        )
        request.user = self.user
        request.session = {
            "committee_uuid": UUID("11111111-2222-3333-4444-555555555555"),
            "committee_id": "C01234567",
        }
        request.method = "DELETE"
        request.query_params = dict()
        view.kwargs = {"pk": membership_uuid}
        view.request = request
        response = view.remove_member(request, membership_uuid)
        self.assertEqual(response.status_code, 200)

    def test_add_pending_membership(self):
        view = CommitteeMembershipViewSet()
        request = self.factory.get("/api/v1/committee-members/add-member")
        request.user = self.user
        request.session = {
            "committee_uuid": UUID("11111111-2222-3333-4444-555555555555"),
            "committee_id": "C01234567",
        }
        request.method = "POST"
        request.data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            "email": "this_email_doesnt_match_any_preexisting_user@test.com",
        }
        view.request = request
        response = view.add_member(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["email"],
            "this_email_doesnt_match_any_preexisting_user@test.com",
        )
        self.assertEqual(response.data["is_active"], False)

    def test_add_membership_for_preexisting_user(self):
        # This test covers a bug found by QA where adding a membership
        # for a pre-existing user was triggering a 500 server error

        view = CommitteeMembershipViewSet()
        request = self.factory.get("/api/v1/committee-members/add-member")
        request.user = self.user
        request.session = {
            "committee_uuid": UUID("11111111-2222-3333-4444-555555555555"),
            "committee_id": "C01234567",
        }
        request.method = "POST"
        request.data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            "email": "test_user_0001@fec.gov",
        }
        view.request = request
        response = view.add_member(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "test_user_0001@fec.gov")
        self.assertEqual(response.data["is_active"], True)

    def test_add_membership_for_preexisting_user_email_case_test(self):
        # This test covers a bug found where the email entered is treated
        # as case when determining membership when it should not be.

        view = CommitteeMembershipViewSet()
        request = self.factory.get("/api/v1/committee-members/add-member")
        request.user = self.user
        request.session = {
            "committee_uuid": UUID("11111111-2222-3333-4444-555555555555"),
            "committee_id": "C01234567",
        }
        request.method = "POST"
        request.data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            "email": "TEST_USER_0001@fec.gov",
        }
        view.request = request
        response = view.add_member(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "test_user_0001@fec.gov")
        self.assertEqual(response.data["is_active"], True)

    def test_add_membership_requires_correct_parameters(self):
        view = CommitteeMembershipViewSet()
        request = self.factory.get("/api/v1/committee-members/add-member")
        request.user = self.user
        request.session = {
            "committee_uuid": UUID("11111111-2222-3333-4444-555555555555"),
            "committee_id": "C01234567",
        }
        request.method = "POST"

        request.data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
        }
        view.request = request
        response = view.add_member(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, "Missing fields: email")

        request.data = {"email": "an_email@fec.gov"}
        view.request = request
        response = view.add_member(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, "Missing fields: role")

        request.data = {"email": "an_email@fec.gov", "role": "A Random String"}
        view.request = request
        response = view.add_member(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, "Invalid role")

        request.data = {
            "email": "test@fec.gov",
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
        }
        view.request = request
        response = view.add_member(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            "This email is taken by an existing membership to this committee",
        )

class CommitteeViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_get_committee_from_production(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            settings.FEC_API = "https://not-real.api/"
            settings.FEC_API_KEY = "MOCK_KEY"
            request = self.factory.get("/api/v1/committee_accounts/C12345678/committee/")
            request.user = self.user
            with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}
                mock_requests.get = Mock()
                mock_requests.get.return_value = mock_response

                response = CommitteeViewSet.as_view({"get": "committee"})(
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
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            settings.FEC_API_STAGE = "https://stage.not-real.api/"
            settings.FEC_API_KEY = "MOCK_KEY"
            request = self.factory.get("/api/v1/committee_accounts/C12345678/committee/")
            request.user = self.user
            with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}
                mock_requests.get = Mock()
                mock_requests.get.return_value = mock_response

                response = CommitteeViewSet.as_view({"get": "committee"})(
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
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "REDIS"
            request = self.factory.get("/api/v1/committee_accounts/C12345678/committee/")
            request.user = self.user
            with patch("fecfiler.committee_accounts.utils.get_committee_from_redis") as mock_committee:
                mock_committee.return_value = {
                    "name": "TEST"
                }
                response = CommitteeViewSet.as_view({"get": "committee"})(
                    request, pk="C12345678"
                )
                was_called_with = mock_committee.call_args.args or []
                self.assertNotEqual(len(was_called_with), 0)
                self.assertIn(
                    "C12345678",
                    was_called_with
                )
                self.assertEqual(response.data["name"], "TEST")

    def test_get_committee_from_invalid(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "INVALID"
            request = self.factory.get("/api/v1/committee_accounts/C12345678/committee/")
            request.user = self.user

            error = "FLAG__COMMITTEE_DATA_SOURCE improperly configured: INVALID"
            response = CommitteeViewSet.as_view({"get": "committee"})(
                request,
                pk="C12345678"
            )
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

        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            settings.FEC_API_STAGE = "https://stage.not-real.api/"
            request = self.factory.get("/api/v1/committee_accounts/query_filings/?query=C2111")
            request.user = self.user
            with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
                mock_requests.get = mock_filing_pages
                response = CommitteeViewSet.as_view({"get": "query_filings"})(
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
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            settings.FEC_API = "https://not-real.api/"
            request = self.factory.get("/api/v1/committee_accounts/query_filings/?query=C12345678")
            request.user = self.user
            with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
                mock_requests.get.return_value = mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"results": [
                    {"committee_id": "C12345678", "committee_name": "TEST MATCH"}
                ]}
                response = CommitteeViewSet.as_view({"get": "query_filings"})(
                    request
                )
                self.assertEqual(response.status_code, 200)
                called_with = mock_requests.get.call_args.args or [[]]
                self.assertIn(
                    "https://not-real.api/filings/",
                    called_with
                )

    def test_query_filings_from_redis(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "REDIS"
            request = self.factory.get(
                "/api/v1/committee_accounts/query_filings/?query=C12345678"
            )
            request.user = self.user
            with patch("fecfiler.committee_accounts.utils.get_filings_from_redis") as mock_query:
                mock_query.return_value = {}
                response = CommitteeViewSet.as_view({"get": "query_filings"})(
                    request
                )
                self.assertEqual(response.status_code, 200)
                called_with = mock_query.call_args.args or [[]]
                self.assertIn("C12345678", called_with)

    def test_query_filings_from_invalid(self):
        print("TEST-O")
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "INVALID"
            request = self.factory.get(
                "/api/v1/committee_accounts/query_filings/?query=C12345678"
            )
            request.user = self.user
            response = CommitteeViewSet.as_view({"get": "query_filings"})(
                request
            )
            error = "FLAG__COMMITTEE_DATA_SOURCE improperly configured: INVALID"
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.content.decode(), error)