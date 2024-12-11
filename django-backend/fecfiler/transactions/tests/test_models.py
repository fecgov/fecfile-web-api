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
    create_tier123_transactions,
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

    def test_tier3_itemization(self):
        ### CREATE ###
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

        self.assertEqual(jf_transfer_100._itemized, True)
        self.assertEqual(jf_transfer_100.itemized, True)
        self.assertEqual(jf_transfer_100.relationally_itemized_count, 0)
        self.assertEqual(jf_transfer_100.relationally_unitemized_count, 0)

        self.assertEqual(partnership_jf_transfer_memo_90._itemized, False)
        self.assertEqual(partnership_jf_transfer_memo_90.itemized, False)
        self.assertEqual(partnership_jf_transfer_memo_90.relationally_itemized_count, 0)
        self.assertEqual(partnership_jf_transfer_memo_90.relationally_unitemized_count, 0)

        self.assertEqual(partnership_attribution_jf_transfer_memo_80._itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_80.itemized, False)
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_80.relationally_itemized_count, 0
        )
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_80.relationally_unitemized_count, 1
        )

        self.assertEqual(partnership_attribution_jf_transfer_memo_70._itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_70.itemized, False)
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_70.relationally_itemized_count, 0
        )
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_70.relationally_unitemized_count, 1
        )

        ### ITEMIZE PARENTS ###
        partnership_attribution_jf_transfer_memo_60 = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.test_ind_contact_for_itemization,
            "2024-01-05",
            amount="60.00",
            report=self.q1_report,
            parent_id=partnership_jf_transfer_memo_90.id,
        )
        partnership_attribution_jf_transfer_memo_60.refresh_from_db()
        partnership_attribution_jf_transfer_memo_70.refresh_from_db()
        partnership_attribution_jf_transfer_memo_80.refresh_from_db()
        partnership_jf_transfer_memo_90.refresh_from_db()
        jf_transfer_100.refresh_from_db()

        self.assertEqual(jf_transfer_100._itemized, True)
        self.assertEqual(jf_transfer_100.itemized, True)
        self.assertEqual(jf_transfer_100.relationally_itemized_count, 1)
        self.assertEqual(jf_transfer_100.relationally_unitemized_count, 0)

        self.assertEqual(partnership_jf_transfer_memo_90._itemized, False)
        self.assertEqual(partnership_jf_transfer_memo_90.itemized, True)
        self.assertEqual(partnership_jf_transfer_memo_90.relationally_itemized_count, 1)
        self.assertEqual(partnership_jf_transfer_memo_90.relationally_unitemized_count, 0)

        self.assertEqual(partnership_attribution_jf_transfer_memo_80._itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_80.itemized, False)
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_80.relationally_itemized_count, 0
        )
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_80.relationally_unitemized_count, 0
        )

        self.assertEqual(partnership_attribution_jf_transfer_memo_70._itemized, False)
        self.assertEqual(partnership_attribution_jf_transfer_memo_70.itemized, False)
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_70.relationally_itemized_count, 0
        )
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_70.relationally_unitemized_count, 0
        )

        self.assertEqual(partnership_attribution_jf_transfer_memo_60._itemized, True)
        self.assertEqual(partnership_attribution_jf_transfer_memo_60.itemized, False)
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_60.relationally_itemized_count, 0
        )
        self.assertEqual(
            partnership_attribution_jf_transfer_memo_60.relationally_unitemized_count, 0
        )

    def xtest_tier3_itemization_add_new_itemized_grandchild(self):
        self.test_new_tier3_transaction = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.test_ind_contact,
            "2024-01-04",
            amount="250.00",
            parent_id=self.test_tier2_transaction.id,
        )

        transactions = list(
            Transaction.objects.filter(
                id__in=[
                    self.test_tier1_transaction.id,
                    self.test_tier2_transaction.id,
                    self.test_tier3_transaction.id,
                    self.test_new_tier3_transaction.id,
                ]
            ).order_by("created")
        )

        self.assertEqual(
            transactions[1].transaction_type_identifier,
            "PARTNERSHIP_JF_TRANSFER_MEMO",
        )
        # self.assertEqual(transactions[1].itemized, True)

        self.assertEqual(
            transactions[3].transaction_type_identifier,
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
        )
        self.assertEqual(transactions[3]._itemized, True)
        self.assertEqual(transactions[3].itemized, True)
        self.assertEqual(transactions[3].relationally_unitemized_count, 0)

    def xtest_tier3_itemization_update_new_itemized_grandchild(self):
        Transaction.objects.filter(
            pk=self.test_new_tier3_transaction.id,
        ).update(amount="2")

        transactions = list(
            Transaction.objects.filter(
                id__in=[
                    self.test_tier1_transaction.id,
                    self.test_tier2_transaction.id,
                    self.test_tier3_transaction.id,
                    self.test_new_tier3_transaction.id,
                ]
            ).order_by("created")
        )

        self.assertEqual(
            transactions[1].transaction_type_identifier,
            "PARTNERSHIP_JF_TRANSFER_MEMO",
        )
        self.assertEqual(transactions[1].itemized, False)

        self.assertEqual(
            transactions[3].transaction_type_identifier,
            "PARTNERSHIP_JF_TRANSFER_MEMO",
        )
        self.assertEqual(transactions[3].itemized, False)
        self.assertEqual(transactions[3].relationally_unitemized_count, 1)

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
