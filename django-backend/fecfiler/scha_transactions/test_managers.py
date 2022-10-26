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
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("111.01"))
        self.assertFalse(scha_transaction.itemized)

    def test_aggregate_two(self):
        scha_transaction = SchATransaction.objects.get(transaction_id="2")
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("333.03"))
        self.assertTrue(scha_transaction.itemized)

    def test_aggregate_three(self):
        scha_transaction = SchATransaction.objects.get(transaction_id="3")
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("666.06"))
        self.assertTrue(scha_transaction.itemized)

    def test_aggregate_negative_offset(self):
        scha_transaction = SchATransaction.objects.get(transaction_id="5")
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("-111.11"))
        self.assertFalse(scha_transaction.itemized)

    def test_aggregate_itemize_jf_transfer(self):
        scha_transaction = SchATransaction.objects.get(transaction_id="6")
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("111.11"))
        self.assertTrue(scha_transaction.itemized)
    def test_aggregate_offset_to_opex_one(self):
        scha_transaction = SchATransaction.objects.get(transaction_id="OffsetToOpex-1")
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("105.25"))
        self.assertFalse(scha_transaction.itemized)

    def test_aggregate_offset_to_opex_two(self):
        scha_transaction = SchATransaction.objects.get(transaction_id="OffsetToOpex-2")
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("316.00"))
        self.assertTrue(scha_transaction.itemized)

    def test_aggregate_offset_to_opex_other(self):
        scha_transaction = SchATransaction.objects.get(
            transaction_id="OffsetToOpex-OtherYear"
        )
        self.assertEquals(scha_transaction.contribution_aggregate, Decimal("102.50"))
        self.assertFalse(scha_transaction.itemized)
