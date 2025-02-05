from django.test import TestCase
from .models import User
from fecfiler.committee_accounts.models import CommitteeAccount, Membership


class UserModelTestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def test_redeem_pending_membership(self):
        committee_account = CommitteeAccount.objects.create(
            committee_id="C87654321",
        )

        pending_membership = Membership.objects.create(
            committee_account=committee_account,
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            pending_email="test_1234@test.com",
        )

        self.assertEquals(
            Membership.objects.get(pending_email="test_1234@test.com").user, None
        )

        new_user = User.objects.create_user(
            email="test_1234@test.com", user_id="5e3c145f-a813-46c7-af5a-5739304acc27"
        )

        pending_membership.refresh_from_db()
        self.assertEquals(pending_membership.user, new_user)
        self.assertEquals(pending_membership.pending_email, None)
