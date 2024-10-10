from unittest.mock import patch
from django.test import TestCase
from fecfiler.committee_accounts.views import create_committee_account
from fecfiler.contacts.models import Contact
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.user.models import User
from django.core.management import call_command


class CommitteeAccountsViewsTest(TestCase):

    def setUp(self):
        with patch("fecfiler.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "REDIS"
            call_command("load_committee_data")
        self.test_user = User.objects.create(email="test@fec.gov", username="gov")

    def test_create_committee_account(self):
        with patch(
            "fecfiler.committee_accounts.views.FLAG__COMMITTEE_DATA_SOURCE",
            "REDIS"
        ):
            account = create_committee_account("C12345678", self.test_user)
            self.assertEquals(account.committee_id, "C12345678")
            report = account.report_set.create()
            transaction = report.transactions.create(committee_account=account)
            transaction.contact_1 = Contact.objects.create(committee_account=account)
            transaction.save()
            self.assertEquals(
                Report.objects.filter(committee_account=account).count(),
                1
            )
            self.assertEquals(
                Transaction.objects.filter(committee_account=account).count(),
                1
            )
            self.assertEquals(
                Contact.objects.filter(committee_account=account).count(),
                1
            )
            call_command("delete_committee_account", "C12345678")
            self.assertEquals(
                Report.objects.filter(committee_account=account).count(),
                0
            )
            self.assertEquals(
                Transaction.objects.filter(committee_account=account).count(),
                0
            )
            self.assertEquals(
                Contact.objects.filter(committee_account=account).count(),
                0
            )
