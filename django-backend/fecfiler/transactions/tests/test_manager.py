from django.test import TestCase

from fecfiler.transactions.models import Transaction, Schedule
import uuid
from decimal import Decimal


class TransactionManagerTestCase(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
        "test_f3x_reports",
        "test_transaction_manager_transactions",
        "test_election_aggregation_data",
    ]

    def test_order_of_transactions(self):
        transactions = Transaction.objects.filter(
            reports__id="1406535e-f99f-42c4-97a8-247904b7d297"
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

    def test_election_aggregation(self):
        transaction = Transaction.objects.get(id="c4ba684a-607f-4f5d-bfb4-0fa1776d4e35")
        self.assertEqual(
            transaction.calendar_ytd_per_election_office, Decimal("578.00")
        )

    def test_debt_repayment(self):
        repayment = Transaction.objects.get(id="dbdbdbdb-62f7-4a11-ac8e-27ea2afa9491")
        debt = Transaction.objects.get(id="dddddddd-3274-47d8-9388-7294a3fd4321")
        self.assertEqual(repayment.debt.id, debt.id)
        self.assertEqual(debt.payment_amount, 123)
        self.assertEqual(debt.balance_at_close, 210)

    def test_force_unaggregated(self):
        txn = Transaction.objects.get(id="12345678-1596-4ef1-a1aa-c4386b8d1234")
        self.assertEqual(txn.aggregate, 3333)

    def test_line_label(self):
        refund = Transaction.objects.get(id="bbbbbbbb-3274-47d8-9388-7294a3fd4321")
        self.assertEqual(refund.line_label, "21(b)")
