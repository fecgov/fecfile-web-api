from uuid import UUID
from django.test import RequestFactory, TestCase
from fecfiler.committee_accounts.models import Membership
from fecfiler.committee_accounts.views import (
    CommitteeMembershipViewSet,
    CommitteeOwnedViewMixin,
    CommitteeViewSet,
)
from fecfiler.user.models import User
from unittest.mock import Mock, patch
from fecfiler.routers import get_all_routers
import structlog

logger = structlog.get_logger(__name__)


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

    def test_get_committee_account_data_from_production(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            request = self.factory.get(
                "/api/v1/committees/get-available-committee/?committee_id=C12345678"
            )
            request.user = self.user
            request.query_params = {"committee_id": "C12345678"}

            with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"results": [{"email": "test@fec.gov"}]}
                mock_requests.get = Mock()
                mock_requests.get.return_value = mock_response

                response = CommitteeViewSet.as_view({"get": "get_available_committee"})(
                    request
                )
                self.assertEqual(response.status_code, 200)

    def test_get_committee_account_data_from_test(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            settings.STAGE_OPEN_FEC_API = "https://stage.not-real.api/"
            settings.STAGE_OPEN_FEC_API_KEY = "MOCK_KEY"
            request = self.factory.get(
                "/api/v1/committees/get-available-committee/?committee_id=C12345678"
            )
            request.user = self.user
            request.query_params = {"committee_id": "C12345678"}
            with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"results": [{"email": "test@fec.gov"}]}
                mock_requests.get = Mock()
                mock_requests.get.return_value = mock_response

                response = CommitteeViewSet.as_view({"get": "get_available_committee"})(
                    request
                )
                was_called_with = mock_requests.get.call_args.args
                self.assertEqual(response.status_code, 200)
                self.assertNotEqual(len(was_called_with), 0)
                self.assertIn(
                    "https://stage.not-real.api/efile/test-form1/", was_called_with
                )

    def test_get_committee_account_data_from_redis(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            request = self.factory.get(
                "/api/v1/committees/get-available-committee/?committee_id=C12345678"
            )
            request.user = self.user
            request.query_params = {"committee_id": "C12345678"}
            with patch(
                "fecfiler.committee_accounts.utils.get_committee_account_data_from_redis"
            ) as mock_committee:
                mock_committee.return_value = {
                    "name": "TEST",
                    "email": "test@fec.gov",
                }
                response = CommitteeViewSet.as_view({"get": "get_available_committee"})(
                    request
                )
                was_called_with = mock_committee.call_args.args or []
                self.assertNotEqual(len(was_called_with), 0)
                self.assertIn("C12345678", was_called_with)
                self.assertEqual(response.data["name"], "TEST")

    def test_viewsets_have_committee_owned_mixin(self):
        exclude_list = [
            "CommitteeViewSet",
            "UserViewSet",
            "SystemStatusViewSet",
            "SummaryViewSet",
            "FeedbackViewSet",
            "WebServicesViewSet",
        ]
        routers = get_all_routers()
        missing_mixin = []

        for router in routers:
            for prefix, viewset, basename in router.registry:
                if (
                    not issubclass(viewset, CommitteeOwnedViewMixin)
                    and viewset.__name__ not in exclude_list
                ):
                    missing_mixin.append(
                        {
                            "viewset": viewset.__name__,
                            "prefix": prefix,
                            "basename": basename,
                        }
                    )

        if missing_mixin:
            error_message = "\n".join(
                [
                    f"ViewSet '{entry['viewset']}' "
                    f"does not inherit from CommitteeOwnedViewMixin."
                    for entry in missing_mixin
                ]
            )
            self.fail(
                f"The following ViewSets are missing CommitteeOwnedViewMixin:\n"
                f"{error_message}"
            )
