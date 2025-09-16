from uuid import UUID
from rest_framework.status import HTTP_400_BAD_REQUEST
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.committee_accounts.views import (
    CommitteeMembershipViewSet,
    CommitteeOwnedViewMixin,
    CommitteeViewSet,
)
from fecfiler.user.models import User
from unittest.mock import Mock, patch
from fecfiler.routers import get_all_routers
from fecfiler.shared.viewset_test import FecfilerViewSetTest

import structlog

logger = structlog.get_logger(__name__)


class CommitteeMemberViewSetTest(FecfilerViewSetTest):
    fixtures = ["C01234567_user_and_committee", "unaffiliated_users"]

    def setUp(self):
        super().setUp()
        self.committee = CommitteeAccount.objects.filter(
            id="11111111-2222-3333-4444-555555555555"
        ).first()

    def tearDown(self):
        Membership.objects.all().delete()
        User.objects.all().delete()
        CommitteeAccount.objects.all().delete()

    def test_remove_member(self):
        manager = User.objects.create_user(
            email="admin1@admin.com", user_id="5e3c145f-a813-46c7-af5a-5739304acc27"
        )
        manager_membership = Membership.objects.create(
            user=manager,
            role=Membership.CommitteeRole.MANAGER,
            committee_account=self.committee,
        )
        response = self.send_viewset_delete_request(
            f"/api/v1/committee-members/{manager_membership.id}/remove-member",
            CommitteeMembershipViewSet,
            "remove_member",
            pk=manager_membership.id,
        )
        self.assertEqual(response.status_code, 200)
        count = Membership.objects.filter(pk=manager_membership.id).count()
        self.assertEqual(count, 0)

    def test_cannot_delete_self(self):
        membership_uuid = UUID("136a21f2-66fe-4d56-89e9-0d1d4612741c")
        response = self.send_viewset_delete_request(
            f"/api/v1/committee-members/{membership_uuid}/remove-member",
            CommitteeMembershipViewSet,
            "remove_member",
            pk=membership_uuid,
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "You cannot remove yourself from the committee."
        )

    def test_non_committee_admin_cannot_delete(self):
        manager = User.objects.create_user(
            email="admin1@admin.com", user_id="5e3c145f-a813-46c7-af5a-5739304acc27"
        )
        manager_membership = Membership.objects.create(
            user=manager,
            role=Membership.CommitteeRole.MANAGER,
            committee_account=self.committee,
        )
        user = User.objects.get(id="fb20ffc3-285e-448e-9e56-9ca1fd43e7d3")
        response = self.send_viewset_delete_request(
            f"/api/v1/committee-members/{manager_membership.id}/remove-member",
            CommitteeMembershipViewSet,
            "remove_member",
            user=user,
            pk=manager_membership.id,
        )
        self.assertEqual(response.status_code, 403)
        count = Membership.objects.filter(pk=manager_membership.id).count()
        self.assertEqual(count, 1)

    def test_add_pending_membership(self):
        post_data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            "email": "this_email_doesnt_match_any_preexisting_user@test.com",
        }
        response = self.send_viewset_post_request(
            "/api/v1/committee-members/add-member",
            post_data,
            CommitteeMembershipViewSet,
            "add_member",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["email"],
            "this_email_doesnt_match_any_preexisting_user@test.com",
        )
        self.assertEqual(response.data["is_active"], False)

    def test_add_membership_for_preexisting_user(self):
        # This test covers a bug found by QA where adding a membership
        # for a pre-existing user was triggering a 500 server error
        post_data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            "email": "test_user_0001@fec.gov",
        }
        response = self.send_viewset_post_request(
            "/api/v1/committee-members/add-member",
            post_data,
            CommitteeMembershipViewSet,
            "add_member",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "test_user_0001@fec.gov")
        self.assertEqual(response.data["is_active"], True)

    def test_add_membership_for_preexisting_user_email_case_test(self):
        # This test covers a bug found where the email entered is treated
        # as case when determining membership when it should not be.
        post_data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            "email": "TEST_USER_0001@fec.gov",
        }
        response = self.send_viewset_post_request(
            "/api/v1/committee-members/add-member",
            post_data,
            CommitteeMembershipViewSet,
            "add_member",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "test_user_0001@fec.gov")
        self.assertEqual(response.data["is_active"], True)

    def test_add_membership_requires_correct_parameters(self):
        post_data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
        }
        response = self.send_viewset_post_request(
            "/api/v1/committee-members/add-member",
            post_data,
            CommitteeMembershipViewSet,
            "add_member",
        )
        self.assertEqual(response.status_code, 400)

        post_data = {"email": "an_email@fec.gov"}
        response = self.send_viewset_post_request(
            "/api/v1/committee-members/add-member",
            post_data,
            CommitteeMembershipViewSet,
            "add_member",
        )
        self.assertEqual(response.status_code, 400)

        post_data = {"email": "an_email@fec.gov", "role": "A Random String"}
        response = self.send_viewset_post_request(
            "/api/v1/committee-members/add-member",
            post_data,
            CommitteeMembershipViewSet,
            "add_member",
        )
        self.assertEqual(response.status_code, 400)

        post_data = {
            "email": "test@fec.gov",
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
        }
        response = self.send_viewset_post_request(
            "/api/v1/committee-members/add-member",
            post_data,
            CommitteeMembershipViewSet,
            "add_member",
        )
        self.assertEqual(response.status_code, 400)

    def test_update_membership_forbidden(self):
        user = User.objects.get(id="fb20ffc3-285e-448e-9e56-9ca1fd43e7d3")
        response = self.send_viewset_put_request(
            "/api/v1/committee-members/5e4ae4ff-60da-4522-a588-ccd97e124b01/",
            {
                "id": "5e4ae4ff-60da-4522-a588-ccd97e124b01",
                "email": "test2@fec.gov",
                "username": "",
                "first_name": "",
                "last_name": "",
                "role": "MANAGER",
                "is_active": "true",
                "committee_account": "11111111-2222-3333-4444-555555555555",
                "created": "2025-03-06T15:27:17.313246-05:00",
                "updated": "2025-03-06T15:27:17.313259-05:00",
                "name": "",
            },
            CommitteeMembershipViewSet,
            "update",
            user=user,
            pk="5e4ae4ff-60da-4522-a588-ccd97e124b01",
        )
        self.assertEqual(response.status_code, 403)

    def test_update_membership_happy_path(self):
        response = self.send_viewset_put_request(
            "/api/v1/committee-members/5e4ae4ff-60da-4522-a588-ccd97e124b01/",
            {
                "id": "5e4ae4ff-60da-4522-a588-ccd97e124b01",
                "email": "test2@fec.gov",
                "username": "",
                "first_name": "",
                "last_name": "",
                "role": "MANAGER",
                "is_active": "true",
                "committee_account": "11111111-2222-3333-4444-555555555555",
                "created": "2025-03-06T15:27:17.313246-05:00",
                "updated": "2025-03-06T15:27:17.313259-05:00",
                "name": "",
            },
            CommitteeMembershipViewSet,
            "update",
            pk="5e4ae4ff-60da-4522-a588-ccd97e124b01",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "test2@fec.gov")
        self.assertEqual(response.data["is_active"], True)
        self.assertEqual(response.data["role"], Membership.CommitteeRole.MANAGER)


class CommitteeViewSetTest(FecfilerViewSetTest):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        super().setUp()

    def test_get_committee_account_data_from_production(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"results": [{"email": "test@fec.gov"}]}
                mock_requests.get = Mock()
                mock_requests.get.return_value = mock_response
                response = self.send_viewset_get_request(
                    "/api/v1/committees/get-available-committee/?committee_id=C12345678",
                    CommitteeViewSet,
                    "get_available_committee",
                )
                self.assertEqual(response.status_code, 200)

    def test_get_committee_account_data_from_test(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            settings.STAGE_OPEN_FEC_API = "https://stage.not-real.api/"
            settings.STAGE_OPEN_FEC_API_KEY = "MOCK_KEY"
            with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"results": [{"email": "test@fec.gov"}]}
                mock_requests.get = Mock()
                mock_requests.get.return_value = mock_response
                response = self.send_viewset_get_request(
                    "/api/v1/committees/get-available-committee/?committee_id=C12345678",
                    CommitteeViewSet,
                    "get_available_committee",
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
            with patch(
                "fecfiler.committee_accounts.utils.get_mocked_committee_data"
            ) as mock_committee:
                mock_committee.return_value = {
                    "name": "TEST",
                    "email": "test@fec.gov",
                }
                response = self.send_viewset_get_request(
                    "/api/v1/committees/get-available-committee/?committee_id=C12345678",
                    CommitteeViewSet,
                    "get_available_committee",
                )
                was_called_with = mock_committee.call_args.args or []
                self.assertNotEqual(len(was_called_with), 0)
                self.assertIn("C12345678", was_called_with)
                self.assertEqual(response.data["name"], "TEST")

    def test_get_committee_account_data_from_redis_no_data(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            with patch(
                "fecfiler.committee_accounts.utils.get_mocked_committee_data"
            ) as mock_committee:
                mock_committee.return_value = None
                response = self.send_viewset_get_request(
                    "/api/v1/committees/get-available-committee/?committee_id=C12345678",
                    CommitteeViewSet,
                    "get_available_committee",
                )
                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    response.data["message"], "No available committee found."
                )

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
