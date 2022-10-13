from decimal import Decimal
from django.test import TestCase
from .models import SchATransaction


class SchATransactionTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_contacts",
        "test_manager_data",
        "test_f3x_summaries",
    ]

    def test_aggregate_one(self):
        scha_transaction = SchATransaction.objects.get(transaction_id="1")
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("1.01"))

    def test_aggregate_two(self):
        scha_transaction = SchATransaction.objects.get(transaction_id="2")
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("3.03"))

    def test_aggregate_three(self):
        scha_transaction = SchATransaction.objects.get(transaction_id="3")
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("6.06"))
