from unittest.mock import patch
from uuid import UUID
from django.test import RequestFactory, TestCase
from fecfiler.committee_accounts.models import Membership
from fecfiler.committee_accounts.views import (
    register_committee,
    CommitteeMembershipViewSet,
    check_email_match,
)
from fecfiler.user.models import User
from django.core.management import call_command


class CommitteeAccountsViewsTest(TestCase):

    def setUp(self):
        with patch("fecfiler.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "REDIS"
            call_command("load_committee_data")

        self.test_user = User.objects.create(email="test@fec.gov", username="gov")
        self.other_user = User.objects.create(email="test@fec.com", username="com")
        self.register_error_message = "could not register committee"

    def test_register_committee(self):
        with patch("fecfiler.committee_accounts.views.FLAG__COMMITTEE_DATA_SOURCE", "REDIS"):
            account = register_committee("C12345678", self.test_user)
            self.assertEquals(account.committee_id, "C12345678")

    def test_register_committee_existing(self):
        with patch("fecfiler.committee_accounts.views.FLAG__COMMITTEE_DATA_SOURCE", "REDIS"):
            account = register_committee("C12345678", self.test_user)
            self.assertEquals(account.committee_id, "C12345678")
            self.assertRaisesMessage(
                Exception,
                self.register_error_message,
                register_committee,
                committee_id="C12345678",
                user=self.test_user,
            )

    def test_register_committee_mismatch_email(self):
        with patch("fecfiler.committee_accounts.views.FLAG__COMMITTEE_DATA_SOURCE", "REDIS"):
            self.assertRaisesMessage(
                Exception,
                self.register_error_message,
                register_committee,
                committee_id="C12345678",
                user=self.other_user,
            )

    def test_register_committee_case_insensitive(self):
        with patch("fecfiler.committee_accounts.views.FLAG__COMMITTEE_DATA_SOURCE", "REDIS"):
            self.test_user.email = self.test_user.email.upper()
            account = register_committee("C12345678", self.test_user)
            self.assertEquals(account.committee_id, "C12345678")
            self.assertRaisesMessage(
                Exception,
                self.register_error_message,
                register_committee,
                committee_id="C12345678",
                user=self.test_user,
            )


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


class CheckEmailMatchTestCase(TestCase):
    def test_no_f1_email(self):
        result = check_email_match("email3@example.com", None)
        self.assertEqual(result, "No email provided in F1")

    def test_no_match(self):
        f1_emails = "email1@example.com;email2@example.com"
        result = check_email_match("email3@example.com", f1_emails)
        self.assertEqual(
            result, "Email email3@example.com does not match committee email"
        )

    def test_match_semicolon(self):
        f1_emails = "email1@example.com;email2@example.com"
        result = check_email_match("email1@example.com", f1_emails)
        self.assertIsNone(result)
        result = check_email_match("email2@example.com", f1_emails)
        self.assertIsNone(result)

    def test_match_comma(self):
        f1_emails = "email1@example.com,email2@example.com"
        result = check_email_match("email2@example.com", f1_emails)
        self.assertIsNone(result)

    def test_email_matching_case_insensitive(self):
        f1_emails = "email1@example.com;email2@example.com"
        result = check_email_match("EMAIL1@example.com", f1_emails)
        self.assertIsNone(result)
