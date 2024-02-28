from uuid import UUID
from django.test import RequestFactory, TestCase
from fecfiler.committee_accounts.models import Membership
from fecfiler.committee_accounts.views import register_committee, \
    CommitteeMembershipViewSet
from fecfiler.user.models import User
from django.core.management import call_command
import structlog

logger = structlog.get_logger(__name__)


class CommitteeAccountsViewsTest(TestCase):

    def setUp(self):
        call_command("load_committee_data")
        self.test_user = User.objects.create(
            email="test@fec.gov", username="gov")
        self.other_user = User.objects.create(
            email="test@fec.com", username="com")

    def test_register_committee(self):
        account = register_committee("C12345678", self.test_user)
        self.assertEquals(account.committee_id, "C12345678")

    def test_register_committee_existing(self):
        account = register_committee("C12345678", self.test_user)
        self.assertEquals(account.committee_id, "C12345678")
        self.assertRaises(
            Exception, register_committee, committee_id="C12345678", user=self.test_user
        )

    def test_register_committee_mismatch_email(self):
        self.assertRaises(
            Exception,
            register_committee,
            committee_id="C12345678",
            user=self.other_user,
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
            "/api/v1/committee-members/{membership_uuid}/remove-member"
        )
        request.user = self.user
        request.session = {
            "committee_uuid": UUID('11111111-2222-3333-4444-555555555555')}
        request.method = "DELETE"
        request.query_params = dict()
        view.kwargs = {"pk": membership_uuid}
        view.request = request
        response = view.remove_member(
            request, membership_uuid)
        self.assertEqual(response.status_code, 200)

    def test_add_pending_membership(self):
        view = CommitteeMembershipViewSet()
        request = self.factory.get("/api/v1/committee-members/add-member")
        request.user = self.user
        request.session = {
            "committee_uuid": UUID('11111111-2222-3333-4444-555555555555')
        }
        request.method = "POST"
        request.data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            "email": "this_email_doesnt_match_any_preexisting_user@test.com"
        }
        view.request = request
        response = view.add_member(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['email'],
            'this_email_doesnt_match_any_preexisting_user@test.com'
        )
        self.assertEqual(response.data['is_active'], False)

    def test_add_membership_for_preexisting_user(self):
        view = CommitteeMembershipViewSet()
        request = self.factory.get("/api/v1/committee-members/add-member")
        request.user = self.user
        request.session = {
            "committee_uuid": UUID('11111111-2222-3333-4444-555555555555')
        }
        request.method = "POST"
        request.data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            "email": 'test_user_0001@fec.gov'
        }
        view.request = request
        response = view.add_member(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'test_user_0001@fec.gov')
        self.assertEqual(response.data['is_active'], True)

    def test_add_membership_requires_correct_parameters(self):
        view = CommitteeMembershipViewSet()
        request = self.factory.get("/api/v1/committee-members/add-member")
        request.user = self.user
        request.session = {
            "committee_uuid": UUID('11111111-2222-3333-4444-555555555555')
        }
        request.method = "POST"


        request.data = {
            "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
        }
        view.request = request
        response = view.add_member(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Missing fields: email')

        request.data = {
            "email": "an_email@fec.gov"
        }
        view.request = request
        response = view.add_member(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Missing fields: role')

        request.data = {
            "email": "an_email@fec.gov",
            "role": "A Random String"
        }
        view.request = request
        response = view.add_member(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Invalid role')
