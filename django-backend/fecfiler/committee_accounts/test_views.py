from django.test import TestCase
from fecfiler.committee_accounts.views import register_committee
from fecfiler.user.models import User


class CommitteeAccountsViewsTest(TestCase):

    def setUp(self):
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
