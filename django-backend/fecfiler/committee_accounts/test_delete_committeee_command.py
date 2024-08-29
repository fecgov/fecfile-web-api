from django.test import TestCase
from fecfiler.committee_accounts.views import register_committee
from fecfiler.contacts.models import Contact
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.user.models import User
from django.core.management import call_command


class CommitteeAccountsViewsTest(TestCase):

    def setUp(self):
        call_command("load_committee_data")
        self.test_user = User.objects.create(email="test@fec.gov", username="gov")

    def test_register_committee(self):
        account = register_committee("C12345678", self.test_user)
        self.assertEquals(account.committee_id, "C12345678")
        report = account.report_set.create()
        transaction = report.transactions.create(committee_account=account)
        transaction.contact_1 = Contact.objects.create(committee_account=account)
        transaction.save()
        self.assertEquals(1, Report.objects.filter(committee_account=account).count())
        self.assertEquals(
            1, Transaction.objects.filter(committee_account=account).count()
        )
        self.assertEquals(1, Contact.objects.filter(committee_account=account).count())
        call_command("delete_committee_account", "C12345678")
        self.assertEquals(0, Report.objects.filter(committee_account=account).count())
        self.assertEquals(
            0, Transaction.objects.filter(committee_account=account).count()
        )
        self.assertEquals(0, Contact.objects.filter(committee_account=account).count())
