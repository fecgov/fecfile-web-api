from django.test import TestCase
from decimal import Decimal
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.aggregation import process_aggregation_for_debts
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact

class ScheduleDAggregationTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000001")
        self.contact = Contact.objects.create(committee_account=self.committee)

    def create_debt_transaction(self, incurred_amount=100, payment_amount=None):
        schedule_d = ScheduleD.objects.create(
            incurred_amount=incurred_amount,
            payment_amount=payment_amount,
            beginning_balance=None,
            payment_prior=None,
            report_coverage_from_date=None,
        )
        txn = Transaction.objects.create(
            committee_account=self.committee,
            contact_1=self.contact,
            schedule_d=schedule_d,
        )
        return txn

    def test_aggregation_sets_balances(self):
        txn = self.create_debt_transaction(incurred_amount=200)
        process_aggregation_for_debts(txn)
        txn.refresh_from_db()
        schedule_d = txn.schedule_d
        self.assertIsNotNone(schedule_d)
        self.assertIsInstance(schedule_d.beginning_balance, Decimal)
        self.assertIsInstance(schedule_d.payment_amount, Decimal)
        self.assertIsInstance(schedule_d.payment_prior, Decimal)

    def test_aggregation_handles_nulls(self):
        txn = self.create_debt_transaction(incurred_amount=None, payment_amount=None)
        process_aggregation_for_debts(txn)
        txn.refresh_from_db()
        schedule_d = txn.schedule_d
        self.assertIsNotNone(schedule_d)
        # Should not raise, should default to Decimal(0) or None depending on logic
        _ = schedule_d.beginning_balance
        _ = schedule_d.payment_amount
        _ = schedule_d.payment_prior

    def test_multiple_debts_chain(self):
        # Create a chain of debts for the same committee and transaction_id, with sequential report periods
        import uuid
        transaction_id = str(uuid.uuid4())
        txn1 = self.create_debt_transaction(incurred_amount=100)
        txn2 = self.create_debt_transaction(incurred_amount=200)
        txn1.transaction_id = transaction_id
        txn2.transaction_id = transaction_id
        txn1.schedule_d.report_coverage_from_date = "2024-01-01"
        txn2.schedule_d.report_coverage_from_date = "2024-06-01"
        txn1.schedule_d.save()
        txn2.schedule_d.save()
        txn1.save()
        txn2.save()
        process_aggregation_for_debts(txn1)
        process_aggregation_for_debts(txn2)
        txn1.refresh_from_db()
        txn2.refresh_from_db()
        self.assertNotEqual(txn1.schedule_d.balance_at_close, txn2.schedule_d.balance_at_close)
