from unittest.mock import patch
from django.test import TestCase
from fecfiler.committee_accounts.utils import create_committee_account
from fecfiler.contacts.models import Contact
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.user.models import User
from django.core.management import call_command


class CommitteeAccountsViewsTest(TestCase):

    def setUp(self):
        with patch("fecfiler.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            call_command("load_committee_data")
        self.test_user = User.objects.create(email="test@fec.gov", username="gov")

    def test_delete_committee_account(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            account = create_committee_account("C12345678", self.test_user)
            self.assertEqual(account.committee_id, "C12345678")
            report = account.report_set.create()
            transaction = report.transactions.create(committee_account=account)
            transaction.contact_1 = Contact.objects.create(committee_account=account)
            transaction.save()
            self.assertEqual(Report.objects.filter(committee_account=account).count(), 1)
            self.assertEqual(
                Transaction.objects.filter(committee_account=account).count(), 1
            )
            self.assertEqual(Contact.objects.filter(committee_account=account).count(), 1)
            call_command("delete_committee_account", "C12345678")
            self.assertEqual(Report.objects.filter(committee_account=account).count(), 0)
            self.assertEqual(
                Transaction.objects.filter(committee_account=account).count(), 0
            )
            self.assertEqual(Contact.objects.filter(committee_account=account).count(), 0)
