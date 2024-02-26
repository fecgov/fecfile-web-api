from django.test import RequestFactory, TestCase
from fecfiler.committee_accounts.views import register_committee, CommitteeMembershipViewSet
from fecfiler.user.models import User
from django.core.management import call_command

class CommitteeAccountsViewsTest(TestCase):

    def setUp(self):
        call_command("load_committee_data")
        self.test_user = User.objects.create(email="test@fec.gov", username="gov")
        self.other_user = User.objects.create(email="test@fec.com", username="com")

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
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def xtest_remove_member(self):
        request = self.factory.get(
            "/api/v1/committee-members/12345678-aaaa-bbbb-cccc-111122223333/remove-member"
        )
        request.user = self.user
        request.session = {
            "committee_uuid": "11111111-2222-3333-4444-555555555555"}
        request.method = "DELETE"
        response = CommitteeMembershipViewSet.remove_member(
            self, request, "12345678-aaaa-bbbb-cccc-111122223333")
        self.assertEqual(response.status_code, 200)
