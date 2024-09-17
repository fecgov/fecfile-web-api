from decimal import Decimal
from django.test import TestCase
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.transactions.models import Transaction
from fecfiler.contacts.tests.utils import (
    create_test_individual_contact,
    create_test_candidate_contact,
)
from .utils import create_schedule_a, create_schedule_b, create_debt, create_loan
from fecfiler.transactions.schedule_c.utils import carry_forward_loans
from fecfiler.web_services.models import (
    FECStatus,
    UploadSubmission,
)
import structlog

logger = structlog.get_logger(__name__)


class TransactionModelTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        self.q1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.m1_report = create_form3x(self.committee, "2024-01-01", "2024-01-31", {})
        self.m2_report = create_form3x(self.committee, "2024-02-01", "2024-02-28", {})
        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )
        self.contact_2 = create_test_candidate_contact(
            "last name", "First name", self.committee.id, "H8MA03131", "S", "AK", "01"
        )
        self.contact_3 = create_test_individual_contact("Test", "Test", self.committee.id)

        self.partnership_receipt = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="100.00",
        )

        self.loan = create_loan(
            self.committee,
            self.contact_1,
            "5000.00",
            "2024-07-01",
            "7%",
            loan_incurred_date="2024-01-01",
            report=self.m1_report,
        )
        self.loan_made = create_schedule_b(
            "LOAN_RECEIVED_FROM_INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-02",
            "1000.00",
            loan_id=self.loan.id,
            report=self.m1_report,
        )
        self.payment_1 = create_schedule_b(
            "LOAN_REPAYMENT_MADE",
            self.committee,
            self.contact_1,
            "2024-01-02",
            "1000.00",
            loan_id=self.loan.id,
            report=self.m1_report,
        )

        carry_forward_loans(self.m2_report)
        self.carried_forward_loan = (
            Transaction.objects.transaction_view()
            .filter(committee_account_id=self.committee.id)
            .order_by("created")
            .last()
        )
        self.payment_2 = create_schedule_b(
            "LOAN_REPAYMENT_MADE",
            self.committee,
            self.contact_1,
            "2024-02-05",
            "600.00",
            loan_id=self.carried_forward_loan.id,
            report=self.m2_report,
        )

        self.earmark_receipt = create_schedule_a(
            "EARMARK_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="100.00",
        )
        self.earmark_memo = create_schedule_a(
            "EARMARK_MEMO",
            self.committee,
            self.contact_2,
            "2024-01-01",
            amount="100.00",
        )
        self.earmark_memo.parent_transaction = self.earmark_receipt
        self.earmark_memo.save()

    def test_delete_transaction(self):
        # Test that a transaction can be deleted
        self.partnership_receipt.delete()
        self.assertIsNotNone(self.partnership_receipt.deleted)

    def test_delete_earmark_receipt(self):
        # Test that earmark transactions are correctly deleted
        self.earmark_memo.parent_transaction = self.earmark_receipt
        self.earmark_memo.save()
        self.earmark_receipt.delete()
        self.earmark_receipt.refresh_from_db()
        self.earmark_memo.refresh_from_db()
        self.assertIsNotNone(self.earmark_receipt.deleted)
        self.assertIsNotNone(self.earmark_memo.deleted)

    def test_delete_earmark_memo(self):
        # Test that earmark transactions are correctly deleted
        self.earmark_memo.parent_transaction = self.earmark_receipt
        self.earmark_memo.save()
        self.earmark_memo.delete()
        self.earmark_memo.refresh_from_db()
        self.earmark_receipt.refresh_from_db()
        self.assertIsNotNone(self.earmark_receipt.deleted)
        self.assertIsNotNone(self.earmark_memo.deleted)

    def test_delete_debt_transactions(self):
        original_debt = create_debt(self.committee, self.contact_1, Decimal("123.00"))
        original_debt.save()
        original_debt.reports.add(self.q1_report)
        first_repayment = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-01-02",
            Decimal("1.23"),
            "GENERAL_DISBURSEMENT",
        )
        first_repayment.debt = original_debt
        first_repayment.save()
        second_repayment = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-01-02",
            Decimal("2.27"),
            "GENERAL_DISBURSEMENT",
        )
        second_repayment.debt = original_debt
        second_repayment.save()

        original_debt.delete()
        original_debt.refresh_from_db()
        first_repayment.refresh_from_db()
        second_repayment.refresh_from_db()
        self.assertIsNotNone(original_debt.deleted)
        self.assertIsNotNone(first_repayment.deleted)
        self.assertIsNotNone(second_repayment.deleted)

    def test_delete_loan_transactions(self):
        self.carried_forward_loan.delete()
        self.carried_forward_loan.refresh_from_db()
        self.payment_2.refresh_from_db()
        self.payment_1.refresh_from_db()
        self.loan.refresh_from_db()
        self.loan_made.refresh_from_db()
        self.assertIsNotNone(self.loan.deleted)
        self.assertIsNotNone(self.loan_made.deleted)
        self.assertIsNotNone(self.carried_forward_loan.deleted)
        self.assertIsNotNone(self.payment_1.deleted)
        self.assertIsNotNone(self.payment_2.deleted)

    def test_delete_reattribution_full(self):
        reatt_1 = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="-10.00",
        )
        reatt_1.reatt_redes = self.partnership_receipt
        reatt_1.save()
        reatt_2 = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_3,
            "2024-01-01",
            amount="10.00",
        )
        reatt_2.reatt_redes = self.partnership_receipt
        reatt_2.save()

        self.partnership_receipt.delete()
        self.partnership_receipt.refresh_from_db()
        reatt_1.refresh_from_db()
        reatt_2.refresh_from_db()
        self.assertIsNotNone(self.partnership_receipt.deleted)
        self.assertIsNotNone(reatt_1.deleted)
        self.assertIsNotNone(reatt_2.deleted)

    def test_delete_reattribution_partial(self):
        # Test that a transaction can be deleted
        reatt_1 = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="-10.00",
        )
        reatt_1.reatt_redes = self.partnership_receipt
        reatt_1.save()
        reatt_2 = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_3,
            "2024-01-01",
            amount="10.00",
        )
        reatt_2.reatt_redes = self.partnership_receipt
        reatt_2.save()

        reatt_1.delete()
        self.partnership_receipt.refresh_from_db()
        reatt_1.refresh_from_db()
        reatt_2.refresh_from_db()
        self.assertIsNone(self.partnership_receipt.deleted)
        self.assertIsNotNone(reatt_1.deleted)
        self.assertIsNotNone(reatt_2.deleted)

    def test_delete_reattribution_earmark(self):
        reatt_1 = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="-10.00",
        )
        reatt_1.reatt_redes = self.earmark_receipt
        reatt_1.save()
        reatt_2 = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_3,
            "2024-01-01",
            amount="10.00",
        )
        reatt_2.reatt_redes = self.earmark_receipt
        reatt_2.save()

        self.earmark_receipt.delete()
        self.earmark_receipt.refresh_from_db()
        self.earmark_memo.refresh_from_db()
        reatt_1.refresh_from_db()
        reatt_2.refresh_from_db()
        self.assertIsNotNone(self.earmark_receipt.deleted)
        self.assertIsNotNone(self.earmark_memo.deleted)
        self.assertIsNotNone(reatt_1.deleted)
        self.assertIsNotNone(reatt_2.deleted)

    def test_delete_reattribution_jf_transfer(self):
        # Setup JF Transfer
        jf_transfer = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="500.00",
            itemized=True,
            report=self.m1_report,
        )
        jf_transfer.save()

        parnership_jf_transfer_memo = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2024-01-02",
            amount="50.00",
            itemized=True,
            report=self.m1_report,
        )
        parnership_jf_transfer_memo.parent_transaction = jf_transfer
        parnership_jf_transfer_memo.save()

        parnership_attribution_jf_transfer_memo = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2024-01-03",
            amount="5.00",
            itemized=True,
            report=self.m1_report,
        )
        parnership_attribution_jf_transfer_memo.parent_transaction = (
            parnership_jf_transfer_memo
        )
        parnership_attribution_jf_transfer_memo.save()

        # Reattribute to future report
        reatt_pull_forward = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="500.00",
            report=self.m2_report,
        )
        reatt_pull_forward.reatt_redes = jf_transfer
        reatt_pull_forward.save()

        reatt_1 = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="-10.00",
            report=self.m2_report,
        )
        reatt_1.reatt_redes = reatt_pull_forward
        reatt_1.save()

        reatt_2 = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_3,
            "2024-01-01",
            amount="10.00",
            report=self.m2_report,
        )
        reatt_2.reatt_redes = reatt_pull_forward
        reatt_2.save()

        jf_transfer.delete()
        jf_transfer.refresh_from_db()
        parnership_jf_transfer_memo.refresh_from_db()
        parnership_attribution_jf_transfer_memo.refresh_from_db()
        reatt_pull_forward.refresh_from_db()
        reatt_1.refresh_from_db()
        reatt_2.refresh_from_db()
        self.assertIsNotNone(jf_transfer.deleted)
        self.assertIsNotNone(parnership_jf_transfer_memo.deleted)
        self.assertIsNotNone(parnership_attribution_jf_transfer_memo.deleted)
        self.assertIsNotNone(reatt_pull_forward.deleted)
        self.assertIsNotNone(reatt_1.deleted)
        self.assertIsNotNone(reatt_2.deleted)

    def test_can_delete_submitted_report(self):
        self.loan.refresh_from_db()
        self.loan_made.refresh_from_db()
        self.carried_forward_loan.refresh_from_db()
        self.payment_1.refresh_from_db()
        self.payment_2.refresh_from_db()
        self.assertTrue(self.loan.can_delete)
        self.assertTrue(self.loan_made.can_delete)
        self.assertTrue(self.carried_forward_loan.can_delete)
        self.assertTrue(self.payment_1.can_delete)
        self.assertTrue(self.payment_2.can_delete)

        self.m1_report.upload_submission = UploadSubmission.objects.initiate_submission(
            self.m1_report.id
        )
        self.m1_report.refresh_from_db()
        self.m1_report.upload_submission.fec_status = FECStatus.ACCEPTED
        self.m1_report.upload_submission.save()
        self.m1_report.refresh_from_db()
        self.loan.refresh_from_db()
        self.loan_made.refresh_from_db()
        self.payment_1.refresh_from_db()
        self.payment_2.refresh_from_db()
        self.carried_forward_loan.refresh_from_db()
        self.assertFalse(self.loan.can_delete)
        self.assertFalse(self.loan_made.can_delete)
        self.assertFalse(self.carried_forward_loan.can_delete)
        self.assertFalse(self.payment_1.can_delete)
        # Payment 2 can still be deleted because
        # it is a repayment on the loan in an active report
        self.assertTrue(self.payment_2.can_delete)

        self.m1_report.amend()
        self.m1_report.refresh_from_db()
        self.loan.refresh_from_db()
        self.loan_made.refresh_from_db()
        self.carried_forward_loan.refresh_from_db()
        self.payment_1.refresh_from_db()
        self.payment_2.refresh_from_db()
        self.assertTrue(self.loan.can_delete)
        self.assertTrue(self.loan_made.can_delete)
        self.assertTrue(self.carried_forward_loan.can_delete)
        self.assertTrue(self.payment_1.can_delete)
        self.assertTrue(self.payment_2.can_delete)
