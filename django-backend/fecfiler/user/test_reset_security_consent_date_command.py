from django.test import TestCase
from fecfiler.user.models import User
from django.core.management import call_command
import datetime


class CommitteeAccountsViewsTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create(
            email="test@fec.gov",
            username="gov",
            security_consent_exp_date=datetime.datetime.today()
        )
        self.test_user.save()

    def test_create_committee_account(self):
        self.test_user.refresh_from_db()
        self.assertIsNotNone(self.test_user.security_consent_exp_date)
        call_command("reset_security_consent_date", "test@fec.gov")
        self.test_user.refresh_from_db()
        self.assertIsNone(self.test_user.security_consent_exp_date)
