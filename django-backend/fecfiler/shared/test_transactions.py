from django.test import TestCase
from fecfiler.scha_transactions.models import SchATransaction

from .transactions import get_from_sched_tables_by_uuid


class SchATransactionTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_contacts",
        "test_f3x_summaries",
        "test_individual_receipt",
        "test_memo_text",
        "test_scha_transactions",
    ]

    def test_retrieving_transaction_valid(self):
        transaction = SchATransaction.objects.all()[0]
        retrieved = get_from_sched_tables_by_uuid(transaction.id)
        self.assertIsNotNone(retrieved)
        self.assertIsInstance(retrieved, SchATransaction)

    def test_retrieving_transaction_invalid(self):
        nothing = get_from_sched_tables_by_uuid("01010101-0101-0101-0101-010101010101")
        self.assertIsNone(nothing)
