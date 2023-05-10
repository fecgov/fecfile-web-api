from django.test import TestCase

from fecfiler.transactions.models import Transaction, Schedule
import uuid


class TransactionManagerTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_transaction_manager_transactions",
    ]

    def test_order_of_transactions(self):
        transactions = Transaction.objects.filter(
            report="1406535e-f99f-42c4-97a8-247904b7d297"
        )
        transaction_one = transactions[0]
        self.assertEqual(transaction_one.schedule, Schedule.A.value.value)
        self.assertEqual(transaction_one.form_type, "SA11AI")
        transaction_two = transactions[1]
        self.assertEqual(transaction_two.schedule, Schedule.A.value.value)
        self.assertEqual(
            transaction_two.parent_transaction_id,
            uuid.UUID("6fedede3-8727-495f-8106-3f971408bc94"),
        )
        transaction_three = transactions[2]
        self.assertEqual(transaction_three.schedule, Schedule.A.value.value)
        self.assertEqual(transaction_three.form_type, "SA11AI")
        self.assertLess(transaction_one.created, transaction_three.created)
        transaction_four = transactions[3]
        self.assertEqual(transaction_four.schedule, Schedule.A.value.value)
        self.assertEqual(transaction_four.form_type, "SA17")
        transaction_five = transactions[4]
        self.assertEqual(transaction_five.schedule, Schedule.B.value.value)
        self.assertEqual(transaction_five.form_type, "SB21b")

    def test_refund_aggregation(self):
        refund = Transaction.objects.get(id="bbbbbbbb-3274-47d8-9388-7294a3fd4321")
        self.assertEqual(refund.aggregate, 4444)
