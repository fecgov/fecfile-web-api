from django.test import TestCase
from .models import SchATransaction
from ..f3x_summaries.models import F3XSummary
from ..committee_accounts.models import CommitteeAccount

class SchATransactionTestCase(TestCase):
    fixtures = ["test_committee_accounts", "test_scha_transactions"]

    def setUp(self):
        self.sa_trans = SchATransaction(
            form_type="SA11AI",
            filer_committee_id_number="C00123456",
            transaction_id="A56123456789-1234",
            entity_type="IND",
            contributor_organization_name="John Smith & Co.",
            contributor_first_name="First",
            contributor_last_name="Last",
            committee_account_id=self.committee,
        )

    def test_get_scha_transaction(self):
        scha_transaction = SchATransaction.objects.get(contributor_last_name="Smith")
        self.assertEquals(scha_transaction.contributor_first_name, "John")

    def test_get_scha_transaction_in_f3x_summary(self):
        committee = CommitteeAccount()
        f3x = F3XSummary(
            committee_account=committee
        )
        trans = SchATransaction(
            committee_account=committee,
            f3x_summary=f3x
        )

    def test_save_and_delete(self):
        self.sa_trans.save()
        transaction_from_db = SchATransaction.objects.get(contributor_last_name="Last")
        self.assertIsInstance(transaction_from_db, SchATransaction)
        self.assertEquals(transaction_from_db.contributor_first_name, "First")
        transaction_from_db.delete()
        self.assertRaises(
            SchATransaction.DoesNotExist,
            SchATransaction.objects.get,
            contributor_first_name="First",
        )

        soft_deleted_transaction = SchATransaction.all_objects.get(
            contributor_last_name="Last"
        )
        self.assertEquals(soft_deleted_transaction.contributor_first_name, "First")
        self.assertIsNotNone(soft_deleted_transaction.deleted)
        soft_deleted_transaction.hard_delete()
        self.assertRaises(
            SchATransaction.DoesNotExist,
            SchATransaction.all_objects.get,
            contributor_last_name="Last",
        )
