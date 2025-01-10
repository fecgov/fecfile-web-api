from django.test import TestCase
from .models import User
from fecfiler.committee_accounts.models import CommitteeAccount, Membership


class UserModelTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C87654321")

    def test_redeem_pending_membership(self):
        new_membership = Membership(
            committee_account=self.committee,
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            pending_email="test_1234@test.com",
        )
        new_membership.committee_account_id = self.committee.id
        new_membership.save()

        self.assertEquals(
            Membership.objects.get(pending_email="test_1234@test.com").user, None
        )

        new_user = User.objects.create_user(
            email="test_1234@test.com", user_id="5e3c145f-a813-46c7-af5a-5739304acc27"
        )

        self.assertEquals(
            Membership.objects.get(pending_email="test_1234@test.com").user, new_user
        )
