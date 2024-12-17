from decimal import Decimal
from django.test import TestCase
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.transactions.models import Transaction
from fecfiler.contacts.tests.utils import (
    create_test_committee_contact,
    create_test_individual_contact,
    create_test_candidate_contact,
    create_test_organization_contact,
)
from .utils import (
    create_schedule_a,
    create_schedule_b,
    create_debt,
    create_loan,
    create_loan_from_bank,
)
from fecfiler.transactions.schedule_c.utils import carry_forward_loans
from fecfiler.transactions.schedule_d.utils import carry_forward_debt
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

        self.test_com_contact_for_itemization = create_test_committee_contact(
            "test-com-name1",
            "C00000000",
            self.committee.id,
            {
                "street_1": "test_sa1",
                "street_2": "test_sa2",
                "city": "test_c1",
                "state": "AL",
                "zip": "12345",
                "telephone": "555-555-5555",
                "country": "USA",
            },
        )
        self.test_org_contact_for_itemization = create_test_organization_contact(
            "test-org-name1",
            self.committee.id,
            {
                "street_1": "test_sa1",
                "street_2": "test_sa2",
                "city": "test_c1",
                "state": "AL",
                "zip": "12345",
                "telephone": "555-555-5555",
                "country": "USA",
            },
        )
        self.test_ind_contact_for_itemization = create_test_individual_contact(
            "test_ln1",
            "test_fn1",
            self.committee.id,
        )

    def test_delete_transaction(self):
        partnership_receipt = Transaction.objects.filter(
            id=self.partnership_receipt.id
        ).first()
        self.assertIsNotNone(partnership_receipt)
        # Test that a transaction can be deleted
        partnership_receipt.delete()
        self.assertIsNotNone(partnership_receipt.deleted)
        # Test that the transaction does not appear in the queryset
        self.assertIsNone(
            Transaction.objects.filter(id=self.partnership_receipt.id).first()
        )

    def test_delete_transaction_with_children(self):
        """Test the deletion of transactions within a 3 tier hierarchy
        deleting the parent deletes all 3
        deleting the tier 2 deletes the tier 2 and 3
        deleting the tier 3 deletes only the tier 3"""
        (
            jf_transfer,
            partnership_jf_transfer_memo,
            partnership_attribution_jf_transfer_memo,
        ) = self.set_up_jf_transfer()

        """Delete the parent transaction"""
        jf_transfer.delete()
        # assert that parent and children transactions are deleted
        self.assertIsNone(Transaction.objects.filter(id=jf_transfer.id).first())
        self.assertIsNone(
            Transaction.objects.filter(id=partnership_jf_transfer_memo.id).first()
        )
        self.assertIsNone(
            Transaction.objects.filter(
                id=partnership_attribution_jf_transfer_memo.id
            ).first()
        )

        # 'un-delete' the transactions
        undelete(jf_transfer)
        undelete(partnership_jf_transfer_memo)
        undelete(partnership_attribution_jf_transfer_memo)

        """Delete the tier 2"""
        partnership_jf_transfer_memo.delete()
        # assert the jf_transfer is not deleted
        self.assertIsNotNone(Transaction.objects.filter(id=jf_transfer.id).first())
        # assert that the children transactions are deleted
        self.assertIsNone(
            Transaction.objects.filter(id=partnership_jf_transfer_memo.id).first()
        )
        self.assertIsNone(
            Transaction.objects.filter(
                id=partnership_attribution_jf_transfer_memo.id
            ).first()
        )

        # 'un-delete' the transactions
        undelete(partnership_jf_transfer_memo)
        undelete(partnership_attribution_jf_transfer_memo)

        """Delete the tier 3"""
        partnership_attribution_jf_transfer_memo.delete()
        # assert the jf_transfer and partnership_jf_transfer_memo are not deleted
        self.assertIsNotNone(Transaction.objects.filter(id=jf_transfer.id).first())
        self.assertIsNotNone(
            Transaction.objects.filter(id=partnership_jf_transfer_memo.id).first()
        )
        # assert that the partnership_attribution_jf_transfer_memo is deleted
        self.assertIsNone(
            Transaction.objects.filter(
                id=partnership_attribution_jf_transfer_memo.id
            ).first()
        )

    def test_delete_coupled_transactions(self):
        """Transactions where 2 or 3 transactions are filled out on the same
        form need to be deleted together even if the child the one deleted.
        For example, an earmark memo is deleted, even though it is the child
        the earmark receipt is also deleted."""

        earmark_receipt = Transaction.objects.filter(id=self.earmark_receipt.id).first()
        earmark_memo = Transaction.objects.filter(id=self.earmark_memo.id).first()
        self.assertIsNotNone(earmark_receipt)
        self.assertIsNotNone(earmark_memo)

        earmark_memo.delete()
        self.assertIsNone(Transaction.objects.filter(id=self.earmark_memo.id).first())
        self.assertIsNone(Transaction.objects.filter(id=self.earmark_receipt.id).first())

    def test_delete_debt_transactions(self):
        """Deleting a debt must delete any payments made towards the debt and
        carried forward copies of it (along with repayments to them)"""
        original_debt = create_debt(self.committee, self.contact_1, Decimal("123.00"))
        original_debt.save()
        original_debt.reports.add(self.q1_report)
        carried_forward_debt = carry_forward_debt(original_debt, self.m1_report)
        first_repayment = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-01-02",
            Decimal("1.23"),
            "GENERAL_DISBURSEMENT",
        )
        first_repayment.debt = carried_forward_debt
        first_repayment.save()
        second_repayment = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-01-02",
            Decimal("2.27"),
            "GENERAL_DISBURSEMENT",
        )
        second_repayment.debt = carried_forward_debt
        second_repayment.save()

        original_debt.delete()
        original_debt.refresh_from_db()
        carried_forward_debt.refresh_from_db()
        first_repayment.refresh_from_db()
        second_repayment.refresh_from_db()
        self.assertIsNotNone(original_debt.deleted)
        self.assertIsNotNone(carried_forward_debt.deleted)
        self.assertIsNotNone(first_repayment.deleted)
        self.assertIsNotNone(second_repayment.deleted)

        undelete(original_debt)
        undelete(carried_forward_debt)
        undelete(first_repayment)
        undelete(second_repayment)

    def test_delete_loan_by_committee(self):
        self.assertIsNone(self.loan.deleted)
        self.assertIsNone(self.loan_made.deleted)
        self.assertIsNone(self.carried_forward_loan.deleted)
        self.assertIsNone(self.payment_1.deleted)
        self.assertIsNone(self.payment_2.deleted)

        self.loan.delete()
        self.loan.refresh_from_db()
        self.loan_made.refresh_from_db()
        self.carried_forward_loan.refresh_from_db()
        self.payment_1.refresh_from_db()
        self.payment_2.refresh_from_db()

        self.assertIsNotNone(self.loan.deleted)
        self.assertIsNotNone(self.loan_made.deleted)
        self.assertIsNotNone(self.carried_forward_loan.deleted)
        self.assertIsNotNone(self.payment_1.deleted)
        self.assertIsNotNone(self.payment_2.deleted)

        undelete(self.loan)
        undelete(self.loan_made)
        undelete(self.carried_forward_loan)
        undelete(self.payment_1)
        undelete(self.payment_2)

    def test_delete_loan_received_from_bank(self):
        loan, loan_receipt, loan_aggreement, guarantor = create_loan_from_bank(
            self.committee,
            self.contact_1,
            "5000.00",
            "2024-07-01",
            "7%",
            False,
            "2024-01-01",
            report=self.q1_report,
        )
        # deleting guarantor does not delete loan
        guarantor.delete()
        guarantor.refresh_from_db()
        loan_aggreement.refresh_from_db()
        loan_receipt.refresh_from_db()
        loan.refresh_from_db()
        self.assertIsNotNone(guarantor.deleted)
        self.assertIsNone(loan_aggreement.deleted)
        self.assertIsNone(loan_receipt.deleted)
        self.assertIsNone(loan.deleted)

        undelete(guarantor)

        # deleting loan_aggreement does delete loan
        loan_aggreement.delete()
        loan_aggreement.refresh_from_db()
        loan_receipt.refresh_from_db()
        loan.refresh_from_db()
        guarantor.refresh_from_db()
        self.assertIsNotNone(loan_aggreement.deleted)
        self.assertIsNotNone(loan_receipt.deleted)
        self.assertIsNotNone(loan.deleted)
        self.assertIsNotNone(guarantor.deleted)

        undelete(loan_aggreement)
        undelete(loan_receipt)
        undelete(loan)
        undelete(guarantor)

        # deleting loan_receipt does delete loan
        loan_receipt.delete()
        loan_receipt.refresh_from_db()
        loan.refresh_from_db()
        loan_aggreement.refresh_from_db()
        guarantor.refresh_from_db()
        self.assertIsNotNone(loan_receipt.deleted)
        self.assertIsNotNone(loan.deleted)
        self.assertIsNotNone(loan_aggreement.deleted)
        self.assertIsNotNone(guarantor.deleted)

        undelete(loan_receipt)
        undelete(loan)
        undelete(loan_aggreement)
        undelete(guarantor)

        # deleting loan deletes all
        loan.delete()
        loan.refresh_from_db()
        loan_receipt.refresh_from_db()
        loan_aggreement.refresh_from_db()
        guarantor.refresh_from_db()
        self.assertIsNotNone(loan_receipt.deleted)
        self.assertIsNotNone(loan.deleted)
        self.assertIsNotNone(loan_aggreement.deleted)
        self.assertIsNotNone(guarantor.deleted)

    def test_delete_reattribution(self):
        reattribution_to = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_3,
            "2024-01-01",
            amount="10.00",
        )
        reattribution_to.schedule_a.reattribution_redesignation_tag = "REATTRIBUTED_TO"
        reattribution_to.schedule_a.save()
        reattribution_to.reatt_redes = self.partnership_receipt
        reattribution_to.save()
        reattribution_from = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="-10.00",
            parent_id=reattribution_to.id,
        )
        reattribution_from.schedule_a.reattribution_redesignation_tag = (
            "REATTRIBUTED_FROM"
        )
        reattribution_from.schedule_a.save()
        reattribution_from.reatt_redes = self.partnership_receipt
        reattribution_from.save()

        self.partnership_receipt.delete()
        self.partnership_receipt.refresh_from_db()
        reattribution_from.refresh_from_db()
        reattribution_to.refresh_from_db()
        # should delete all 3 transactions
        self.assertIsNotNone(self.partnership_receipt.deleted)
        self.assertIsNotNone(reattribution_from.deleted)
        self.assertIsNotNone(reattribution_to.deleted)

        undelete(self.partnership_receipt)
        undelete(reattribution_from)
        undelete(reattribution_to)

        reattribution_to.delete()
        self.partnership_receipt.refresh_from_db()
        reattribution_from.refresh_from_db()
        reattribution_to.refresh_from_db()
        # should just delete the reattributions
        self.assertIsNone(self.partnership_receipt.deleted)
        self.assertIsNotNone(reattribution_from.deleted)
        self.assertIsNotNone(reattribution_to.deleted)

        undelete(self.partnership_receipt)
        undelete(reattribution_from)
        undelete(reattribution_to)

        reattribution_from.delete()
        self.partnership_receipt.refresh_from_db()
        reattribution_from.refresh_from_db()
        reattribution_to.refresh_from_db()
        # should just delete the reattributions
        self.assertIsNone(self.partnership_receipt.deleted)
        self.assertIsNotNone(reattribution_from.deleted)
        self.assertIsNotNone(reattribution_to.deleted)

    def test_delete_reattribution_with_copy(self):
        self.assertIsNone(self.partnership_receipt.deleted)

        copy_of_receipt_for_reattribution = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="100.00",
            report=self.m1_report,
        )
        copy_of_receipt_for_reattribution.reatt_redes = self.partnership_receipt
        copy_of_receipt_for_reattribution.schedule_a.reattribution_redesignation_tag = (
            "REATTRIBUTED"
        )
        copy_of_receipt_for_reattribution.schedule_a.save()
        copy_of_receipt_for_reattribution.save()
        reattribution_to = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_3,
            "2024-01-01",
            amount="10.00",
            report=self.m1_report,
        )
        reattribution_to.reatt_redes = copy_of_receipt_for_reattribution
        reattribution_to.schedule_a.reattribution_redesignation_tag = "REATTRIBUTED_TO"
        reattribution_to.schedule_a.save()
        reattribution_to.save()
        reattribution_from = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="-10.00",
            report=self.m1_report,
            parent_id=reattribution_to.id,
        )
        reattribution_from.reatt_redes = copy_of_receipt_for_reattribution
        reattribution_from.schedule_a.reattribution_redesignation_tag = (
            "REATTRIBUTED_FROM"
        )
        reattribution_from.schedule_a.save()
        reattribution_from.save()

        # Deleting the original deletes all transactions
        self.partnership_receipt.delete()
        self.partnership_receipt.refresh_from_db()
        copy_of_receipt_for_reattribution.refresh_from_db()
        reattribution_to.refresh_from_db()
        reattribution_from.refresh_from_db()
        self.assertIsNotNone(self.partnership_receipt.deleted)
        self.assertIsNotNone(copy_of_receipt_for_reattribution.deleted)
        self.assertIsNotNone(reattribution_to.deleted)
        self.assertIsNotNone(reattribution_from.deleted)

        undelete(self.partnership_receipt)
        undelete(copy_of_receipt_for_reattribution)
        undelete(reattribution_to)
        undelete(reattribution_from)

        # Deleting the copy deletes the reattributions
        copy_of_receipt_for_reattribution.delete()
        self.partnership_receipt.refresh_from_db()
        copy_of_receipt_for_reattribution.refresh_from_db()
        reattribution_to.refresh_from_db()
        reattribution_from.refresh_from_db()
        self.assertIsNone(self.partnership_receipt.deleted)
        self.assertIsNotNone(copy_of_receipt_for_reattribution.deleted)
        self.assertIsNotNone(reattribution_to.deleted)
        self.assertIsNotNone(reattribution_from.deleted)

        undelete(copy_of_receipt_for_reattribution)
        undelete(reattribution_to)
        undelete(reattribution_from)

        # Deleting either reattribution deletes the copy
        reattribution_to.delete()
        self.partnership_receipt.refresh_from_db()
        copy_of_receipt_for_reattribution.refresh_from_db()
        reattribution_to.refresh_from_db()
        reattribution_from.refresh_from_db()
        self.assertIsNone(self.partnership_receipt.deleted)
        self.assertIsNotNone(copy_of_receipt_for_reattribution.deleted)
        self.assertIsNotNone(reattribution_to.deleted)
        self.assertIsNotNone(reattribution_from.deleted)

        undelete(copy_of_receipt_for_reattribution)
        undelete(reattribution_to)
        undelete(reattribution_from)

        reattribution_from.delete()
        self.partnership_receipt.refresh_from_db()
        copy_of_receipt_for_reattribution.refresh_from_db()
        reattribution_to.refresh_from_db()
        reattribution_from.refresh_from_db()
        self.assertIsNone(self.partnership_receipt.deleted)
        self.assertIsNotNone(copy_of_receipt_for_reattribution.deleted)
        self.assertIsNotNone(reattribution_to.deleted)
        self.assertIsNotNone(reattribution_from.deleted)

    def test_delete_reattribution_earmark(self):
        self.assertIsNone(self.earmark_receipt.deleted)
        self.assertIsNone(self.earmark_memo.deleted)
        reattribution_to = create_schedule_a(
            "EARMARK_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="10.00",
        )
        reattribution_to.reatt_redes = self.earmark_receipt
        reattribution_to.schedule_a.reattribution_redesignation_tag = "REATTRIBUTED_TO"
        reattribution_to.schedule_a.save()
        reattribution_to.save()
        reattribution_from = create_schedule_a(
            "EARMARK_RECEIPT",
            self.committee,
            self.contact_3,
            "2024-01-01",
            amount="-10.00",
            parent_id=reattribution_to.id,
        )
        reattribution_from.reatt_redes = self.earmark_receipt
        reattribution_from.schedule_a.reattribution_redesignation_tag = (
            "REATTRIBUTED_FROM"
        )
        reattribution_from.schedule_a.save()
        reattribution_from.save()

        self.earmark_receipt.delete()
        self.earmark_receipt.refresh_from_db()
        self.earmark_memo.refresh_from_db()
        reattribution_to.refresh_from_db()
        reattribution_from.refresh_from_db()
        self.assertIsNotNone(self.earmark_receipt.deleted)
        self.assertIsNotNone(self.earmark_memo.deleted)
        self.assertIsNotNone(reattribution_to.deleted)
        self.assertIsNotNone(reattribution_from.deleted)

    def test_delete_reattribution_jf_transfer(self):
        (
            jf_transfer,
            partnership_jf_transfer_memo,
            partnership_attribution_jf_transfer_memo,
        ) = self.set_up_jf_transfer()

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
        reatt_pull_forward.schedule_a.reattribution_redesignation_tag = "REATTRIBUTED"
        reatt_pull_forward.schedule_a.save()
        reatt_pull_forward.save()

        reattribution_to = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="10.00",
            report=self.m2_report,
        )
        reattribution_to.reatt_redes = reatt_pull_forward
        reattribution_to.schedule_a.reattribution_redesignation_tag = "REATTRIBUTED_TO"
        reattribution_to.schedule_a.save()
        reattribution_to.save()

        reattribution_from = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_3,
            "2024-01-01",
            amount="-10.00",
            report=self.m2_report,
            parent_id=reattribution_to.id,
        )
        reattribution_from.reatt_redes = reatt_pull_forward
        reattribution_from.schedule_a.reattribution_redesignation_tag = (
            "REATTRIBUTED_FROM"
        )
        reattribution_from.schedule_a.save()
        reattribution_from.save()

        # Deleting the original deletes all transactions
        jf_transfer.delete()
        jf_transfer.refresh_from_db()
        partnership_jf_transfer_memo.refresh_from_db()
        partnership_attribution_jf_transfer_memo.refresh_from_db()
        reatt_pull_forward.refresh_from_db()
        reattribution_to.refresh_from_db()
        reattribution_from.refresh_from_db()
        self.assertIsNotNone(jf_transfer.deleted)
        self.assertIsNotNone(partnership_jf_transfer_memo.deleted)
        self.assertIsNotNone(partnership_attribution_jf_transfer_memo.deleted)
        self.assertIsNotNone(reatt_pull_forward.deleted)
        self.assertIsNotNone(reattribution_to.deleted)
        self.assertIsNotNone(reattribution_from.deleted)

        undelete(jf_transfer)
        undelete(partnership_jf_transfer_memo)
        undelete(partnership_attribution_jf_transfer_memo)
        undelete(reatt_pull_forward)
        undelete(reattribution_to)
        undelete(reattribution_from)

        # Deleting the copy deletes the reattributions
        reatt_pull_forward.delete()
        jf_transfer.refresh_from_db()
        partnership_jf_transfer_memo.refresh_from_db()
        partnership_attribution_jf_transfer_memo.refresh_from_db()
        reatt_pull_forward.refresh_from_db()
        reattribution_to.refresh_from_db()
        reattribution_from.refresh_from_db()
        self.assertIsNone(jf_transfer.deleted)
        self.assertIsNotNone(reatt_pull_forward.deleted)
        self.assertIsNotNone(reattribution_to.deleted)
        self.assertIsNotNone(reattribution_from.deleted)

        undelete(reatt_pull_forward)
        undelete(reattribution_to)
        undelete(reattribution_from)

        # Deleting either reattribution deletes the copy
        reattribution_from.delete()
        jf_transfer.refresh_from_db()
        partnership_jf_transfer_memo.refresh_from_db()
        partnership_attribution_jf_transfer_memo.refresh_from_db()
        reatt_pull_forward.refresh_from_db()
        reattribution_to.refresh_from_db()
        reattribution_from.refresh_from_db()
        self.assertIsNone(jf_transfer.deleted)
        self.assertIsNotNone(reatt_pull_forward.deleted)
        self.assertIsNotNone(reattribution_to.deleted)
        self.assertIsNotNone(reattribution_from.deleted)

    def test_can_delete_loan(self):
        self.loan.refresh_from_db()
        self.loan_made.refresh_from_db()
        self.carried_forward_loan.refresh_from_db()
        self.payment_1.refresh_from_db()
        self.payment_2.refresh_from_db()
        self.assertTrue(self.loan.can_delete)
        self.assertTrue(self.loan_made.can_delete)
        # Can delete carried forward debt, but the UI won't let you
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
        self.assertFalse(self.payment_1.can_delete)
        # Can delete carried forward loan, but the UI won't let you
        self.assertTrue(self.carried_forward_loan.can_delete)
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
        # Can delete carried forward loan, but the UI won't let you
        self.assertTrue(self.carried_forward_loan.can_delete)
        self.assertTrue(self.payment_1.can_delete)
        self.assertTrue(self.payment_2.can_delete)

    def test_can_delete_reattributed_transaction(self):
        # Can delete a reattribution on a future report (copy/to/from)
        # Can NOT delete original or reattributions if future report is submitted
        m1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        m2_report = create_form3x(self.committee, "2024-02-01", "2024-03-01", {})
        transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            "100.00",
            report=m1_report,
        )
        copy_of_transaction_for_reattribution = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            "100.00",
            report=m2_report,
        )
        copy_of_transaction_for_reattribution.reatt_redes = transaction
        copy_of_transaction_for_reattribution.schedule_a.reattribution_redesignation_tag = (  # noqa: E501
            "REATTRIBUTED"
        )
        copy_of_transaction_for_reattribution.schedule_a.save()
        copy_of_transaction_for_reattribution.save()
        reattribution_to = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-02-01",
            "10.00",
            report=m2_report,
        )
        reattribution_to.reatt_redes = copy_of_transaction_for_reattribution
        reattribution_to.schedule_a.reattribution_redesignation_tag = "REATTRIBUTED_TO"
        reattribution_to.schedule_a.save()
        reattribution_to.save()
        reattribution_from = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-02-01",
            "-10.00",
            report=m2_report,
            parent_id=reattribution_to.id,
        )
        reattribution_from.reatt_redes = copy_of_transaction_for_reattribution
        reattribution_from.schedule_a.reattribution_redesignation_tag = (
            "REATTRIBUTED_FROM"
        )
        reattribution_from.schedule_a.save()
        reattribution_from.save()
        transaction.refresh_from_db()
        copy_of_transaction_for_reattribution.refresh_from_db()
        reattribution_to.refresh_from_db()
        reattribution_from.refresh_from_db()

        self.assertTrue(transaction.can_delete)
        self.assertTrue(copy_of_transaction_for_reattribution.can_delete)
        self.assertTrue(reattribution_to.can_delete)
        self.assertTrue(reattribution_from.can_delete)

        m2_report.upload_submission = UploadSubmission.objects.initiate_submission(
            self.m2_report.id
        )
        m2_report.save()
        transaction.refresh_from_db()
        copy_of_transaction_for_reattribution.refresh_from_db()
        reattribution_to.refresh_from_db()
        reattribution_from.refresh_from_db()

        self.assertFalse(transaction.can_delete)
        self.assertFalse(copy_of_transaction_for_reattribution.can_delete)
        self.assertFalse(reattribution_to.can_delete)
        self.assertFalse(reattribution_from.can_delete)

    def test_can_delete_debt(self):

        m1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        m2_report = create_form3x(self.committee, "2024-02-01", "2024-03-01", {})
        original_debt = create_debt(
            self.committee, self.contact_1, Decimal("123.00"), report=m1_report
        )
        m1_repayment = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-01-02",
            Decimal("1.23"),
            "GENERAL_DISBURSEMENT",
            report=m1_report,
        )
        m1_repayment.debt = original_debt
        m1_repayment.save()
        carried_forward_debt = carry_forward_debt(original_debt, m2_report)
        m2_repayment = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-02-02",
            Decimal("1.23"),
            "GENERAL_DISBURSEMENT",
            report=m2_report,
        )
        m2_repayment.debt = carried_forward_debt
        m2_repayment.save()

        self.assertTrue(original_debt.can_delete)
        self.assertTrue(m1_repayment.can_delete)
        # Can delete carried forward debt, but the UI won't let you
        self.assertTrue(carried_forward_debt.can_delete)
        self.assertTrue(m2_repayment.can_delete)

        m2_report.upload_submission = UploadSubmission.objects.initiate_submission(
            m2_report.id
        )
        m2_report.upload_submission.save()
        m2_report.save()
        original_debt.refresh_from_db()
        m1_repayment.refresh_from_db()
        carried_forward_debt.refresh_from_db()
        m2_repayment.refresh_from_db()
        self.assertFalse(original_debt.can_delete)
        self.assertFalse(m1_repayment.can_delete)
        self.assertFalse(carried_forward_debt.can_delete)
        self.assertFalse(m2_repayment.can_delete)

        m2_report.upload_submission = None
        m2_report.save()
        m1_report.upload_submission = UploadSubmission.objects.initiate_submission(
            m1_report.id
        )
        m1_report.save()
        original_debt.refresh_from_db()
        m1_repayment.refresh_from_db()
        carried_forward_debt.refresh_from_db()
        m2_repayment.refresh_from_db()
        self.assertFalse(original_debt.can_delete)
        self.assertFalse(m1_repayment.can_delete)
        # Can delete carried forward debt, but the UI won't let you
        self.assertTrue(carried_forward_debt.can_delete)
        self.assertTrue(m2_repayment.can_delete)

        m1_report.upload_submission = None
        m1_report.save()

        m3_report = create_form3x(self.committee, "2024-03-01", "2024-04-01", {})
        carry_forward_debt(original_debt, m3_report)
        # m2_report.upload_submission = UploadSubmission.objects.initiate_submission(
        #     m2_report.id
        # )
        # m2_report.save()
        m3_report.upload_submission = UploadSubmission.objects.initiate_submission(
            m3_report.id
        )
        m3_report.save()
        original_debt.refresh_from_db()
        # self.assertFalse(original_debt.can_delete)
        m2_report.upload_submission = None
        m2_report.save()
        original_debt.refresh_from_db()
        self.assertFalse(original_debt.can_delete)
        m3_report.upload_submission = None
        m3_report.save()
        original_debt.refresh_from_db()
        self.assertTrue(original_debt.can_delete)

    def set_up_jf_transfer(self):
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

        partnership_jf_transfer_memo = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2024-01-02",
            amount="50.00",
            itemized=True,
            report=self.m1_report,
        )
        partnership_jf_transfer_memo.parent_transaction = jf_transfer
        partnership_jf_transfer_memo.save()

        partnership_attribution_jf_transfer_memo = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2024-01-03",
            amount="5.00",
            itemized=True,
            report=self.m1_report,
        )
        partnership_attribution_jf_transfer_memo.parent_transaction = (
            partnership_jf_transfer_memo
        )
        partnership_attribution_jf_transfer_memo.save()

        return (
            jf_transfer,
            partnership_jf_transfer_memo,
            partnership_attribution_jf_transfer_memo,
        )

    def test_get_transaction_family(self):
        a, b, c = self.set_up_jf_transfer()
        b2 = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2024-01-02",
            amount="50.00",
            itemized=True,
            report=self.m1_report,
        )
        b2.parent_transaction = a
        b2.save()

        a_family = a.get_transaction_family()
        self.assertIn(a, a_family)
        self.assertIn(b, a_family)
        self.assertIn(c, a_family)
        self.assertIn(b2, a_family)

        b_family = b.get_transaction_family()
        self.assertIn(a, b_family)
        self.assertIn(b, b_family)
        self.assertIn(c, b_family)
        self.assertNotIn(b2, b_family)

        c_family = c.get_transaction_family()
        self.assertIn(a, c_family)
        self.assertIn(b, c_family)
        self.assertIn(c, c_family)
        self.assertNotIn(b2, c_family)

    def test_get_children(self):
        a, b, c = self.set_up_jf_transfer()
        self.assertNotIn(c, a.children)
        self.assertIn(b, a.children)

    def test_tier3_itemization(self):
        # CREATE JF TRANSFER FAMILY
        (
            jf_transfer_100,
            partnership_jf_transfer_memo_90,
            partnership_attribution_jf_transfer_memo_80,
            partnership_attribution_jf_transfer_memo_70,
        ) = self.set_up_jf_transfer_for_itemization_tests()
        self.assertEqual(
            partnership_jf_transfer_memo_90.parent_transaction, jf_transfer_100
        )
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_80.parent_transaction,
            partnership_jf_transfer_memo_90,
        )
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_70.parent_transaction,
            partnership_jf_transfer_memo_90,
        )

        jf_transfer_100.refresh_from_db()
        partnership_jf_transfer_memo_90.refresh_from_db()
        partnership_attribution_jf_transfer_memo_80.refresh_from_db()
        partnership_attribution_jf_transfer_memo_70.refresh_from_db()

        self.assertEqual(jf_transfer_100.itemized, True)
        self.assertEqual(partnership_jf_transfer_memo_90.itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_80.itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_70.itemized, False)

        # ADD ITEMIZED CHILD TO TRIGGER PARENT ITEMIZATION
        partnership_attribution_jf_transfer_memo_60 = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.test_ind_contact_for_itemization,
            "2024-01-05",
            amount="60.00",
            report=self.q1_report,
            parent_id=partnership_jf_transfer_memo_90.id,
        )

        jf_transfer_100.refresh_from_db()
        partnership_jf_transfer_memo_90.refresh_from_db()
        partnership_attribution_jf_transfer_memo_80.refresh_from_db()
        partnership_attribution_jf_transfer_memo_70.refresh_from_db()
        partnership_attribution_jf_transfer_memo_60.refresh_from_db()

        self.assertEqual(jf_transfer_100.itemized, True)
        self.assertEqual(partnership_jf_transfer_memo_90.itemized, True)
        self.assertEqual(partnership_attribution_jf_transfer_memo_80.itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_70.itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_60.itemized, True)

        # FORCE UNITEMIZE PARENT TO TRIGGER UNITEMIZATION OF CHILDREN

        jf_transfer_100.force_itemized = False
        jf_transfer_100.save()

        jf_transfer_100.refresh_from_db()
        partnership_jf_transfer_memo_90.refresh_from_db()
        partnership_attribution_jf_transfer_memo_80.refresh_from_db()
        partnership_attribution_jf_transfer_memo_70.refresh_from_db()
        partnership_attribution_jf_transfer_memo_60.refresh_from_db()

        self.assertEqual(jf_transfer_100.itemized, False)
        self.assertEqual(partnership_jf_transfer_memo_90.itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_80.itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_70.itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_60.itemized, False)

        # UPDATE ITEMIZED CHILD TO ITEMIZE PARENT CHAIN ONCE MORE
        partnership_attribution_jf_transfer_memo_60.schedule_a.contribution_amount = 65.00
        partnership_attribution_jf_transfer_memo_60.schedule_a.save()
        partnership_attribution_jf_transfer_memo_60.save()

        jf_transfer_100.refresh_from_db()
        partnership_jf_transfer_memo_90.refresh_from_db()
        partnership_attribution_jf_transfer_memo_80.refresh_from_db()
        partnership_attribution_jf_transfer_memo_70.refresh_from_db()
        partnership_attribution_jf_transfer_memo_60.refresh_from_db()

        self.assertEqual(jf_transfer_100.itemized, True)
        self.assertEqual(partnership_jf_transfer_memo_90.itemized, True)
        self.assertEqual(partnership_attribution_jf_transfer_memo_80.itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_70.itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_60.itemized, True)

    def set_up_jf_transfer(self):
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

        partnership_jf_transfer_memo = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2024-01-02",
            amount="50.00",
            itemized=True,
            report=self.m1_report,
        )
        partnership_jf_transfer_memo.parent_transaction = jf_transfer
        partnership_jf_transfer_memo.save()

        partnership_attribution_jf_transfer_memo = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2024-01-03",
            amount="5.00",
            itemized=True,
            report=self.m1_report,
        )
        partnership_attribution_jf_transfer_memo.parent_transaction = (
            partnership_jf_transfer_memo
        )
        partnership_attribution_jf_transfer_memo.save()

        return (
            jf_transfer,
            partnership_jf_transfer_memo,
            partnership_attribution_jf_transfer_memo,
        )

    def set_up_jf_transfer_for_itemization_tests(self):
        jf_transfer_100 = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.test_com_contact_for_itemization,
            "2024-01-01",
            amount="100.00",
            report=self.q1_report,
        )

        partnership_jf_transfer_memo_90 = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.test_org_contact_for_itemization,
            "2024-01-02",
            amount="90.00",
            report=self.q1_report,
            parent_id=jf_transfer_100.id,
        )

        partnership_attribution_jf_transfer_memo_80 = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.test_ind_contact_for_itemization,
            "2024-01-03",
            amount="80.00",
            report=self.q1_report,
            parent_id=partnership_jf_transfer_memo_90.id,
        )

        partnership_attribution_jf_transfer_memo_70 = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.test_ind_contact_for_itemization,
            "2024-01-04",
            amount="70.00",
            report=self.q1_report,
            parent_id=partnership_jf_transfer_memo_90.id,
        )

        return (
            jf_transfer_100,
            partnership_jf_transfer_memo_90,
            partnership_attribution_jf_transfer_memo_80,
            partnership_attribution_jf_transfer_memo_70,
        )


def undelete(transaction):
    transaction.deleted = None
    transaction.save()
