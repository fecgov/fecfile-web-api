from django.test import TestCase
from django.db.models import QuerySet
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact
from fecfiler.transactions.models import Transaction, get_read_model
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.transactions.tests.utils import (
    create_test_transaction,
    create_schedule_b,
    create_schedule_a,
    create_ie,
    create_debt,
    create_loan,
)
from fecfiler.transactions.schedule_c.utils import carry_forward_loans
from decimal import Decimal
from django.db import transaction
import structlog

logger = structlog.get_logger(__name__)


class TransactionViewTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        self.contact_1 = Contact.objects.create(committee_account_id=self.committee.id)

    def test_transaction_view(self):
        indiviual_reciepts = [
            {"date": "2023-01-01", "amount": "123.45", "group": "GENERAL"},
            {"date": "2024-01-01", "amount": "100.00", "group": "GENERAL"},
            {"date": "2024-01-02", "amount": "200.00", "group": "GENERAL"},
            {"date": "2024-01-03", "amount": "100.00", "group": "OTHER"},
        ]
        for receipt_data in indiviual_reciepts:
            create_schedule_a(
                "INDIVIDUAL_RECEIPT",
                self.committee,
                self.contact_1,
                receipt_data["date"],
                receipt_data["amount"],
                receipt_data["group"],
            )

        view: QuerySet = Transaction.objects.transaction_view()
        transactions = (
            view.filter(committee_account_id=self.committee.id).all().order_by("date")
        )
        for t in transactions:
            t.refresh_from_db()
        self.assertEqual(transactions[0].aggregate, Decimal("123.45"))
        self.assertEqual(transactions[2].aggregate, Decimal("300"))
        self.assertEqual(transactions[3].aggregate, Decimal("100"))

    def test_force_unaggregated(self):

        create_test_transaction(  # noqa: F841
            "INDIVIDUAL_RECEIPT",
            ScheduleA,
            self.committee,
            self.contact_1,
            None,
            "GENERAL",
            {
                "contribution_date": "2024-01-01",
                "contribution_amount": "100.00",
            },
            {"force_unaggregated": True},
        )
        create_test_transaction(
            "INDIVIDUAL_RECEIPT",
            ScheduleA,
            self.committee,
            self.contact_1,
            None,
            "GENERAL",
            {
                "contribution_date": "2024-01-02",
                "contribution_amount": "200.00",
            },
        )

        view: QuerySet = Transaction.objects.transaction_view()
        transactions = view.filter(committee_account_id=self.committee.id).order_by(
            "date"
        )
        for t in transactions:
            t.refresh_from_db()
        self.assertEqual(transactions[0].aggregate, None)
        self.assertEqual(transactions[0].force_unaggregated, True)
        self.assertEqual(transactions[1].aggregate, Decimal("200"))

    def test_transaction_view_parent(self):
        partnership_receipt = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="100.00",
        )
        parnership_attribution = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="100.00",
        )
        # set parent
        parnership_attribution.parent_transaction = partnership_receipt
        parnership_attribution.save()

        view: QuerySet = Transaction.objects.transaction_view()
        view = view.filter(
            committee_account_id=self.committee.id,
            transaction_type_identifier="PARTNERSHIP_ATTRIBUTION",
        )
        self.assertEqual(
            view[0].back_reference_tran_id_number, partnership_receipt.transaction_id
        )

    def test_transaction_view_list_with_grandparent(self):
        with transaction.atomic():
            jf_transfer = create_schedule_a(
                "JOINT_FUNDRAISING_TRANSFER",
                self.committee,
                self.contact_1,
                "2024-01-01",
                amount="500.00",
                itemized=True,
            )
            jf_transfer.save()

            parnership_jf_transfer_memo = create_schedule_a(
                "PARTNERSHIP_JF_TRANSFER_MEMO",
                self.committee,
                self.contact_1,
                "2024-01-02",
                amount="50.00",
                itemized=True,
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
            )
            parnership_attribution_jf_transfer_memo.parent_transaction = (
                parnership_jf_transfer_memo
            )
            parnership_attribution_jf_transfer_memo.save()

        view = get_read_model(self.committee.id).objects.all().order_by("date")

        self.assertEqual(view[0].itemized, True)
        self.assertEqual(view[0].aggregate, 500)
        self.assertEqual(view[1].itemized, True)
        self.assertEqual(view[1].aggregate, 550)
        self.assertEqual(view[2].itemized, True)
        self.assertEqual(view[2].aggregate, 555)

    def test_refund_aggregate(self):
        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            "123.00",
            "NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
        )
        create_schedule_b(
            "INDIVIDUAL_REFUND_NP_HEADQUARTERS_ACCOUNT",
            self.committee,
            self.contact_1,
            "2024-01-02",
            "100.00",
            "NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
        )
        view: QuerySet = Transaction.objects.transaction_view()
        transactions = view.filter(committee_account_id=self.committee.id).order_by(
            "date"
        )
        self.assertEqual(transactions[0].aggregate, Decimal("123.00"))
        self.assertEqual(transactions[1].aggregate, Decimal("23.00"))

    def test_election_aggregate(self):
        candidate_a = Contact.objects.create(
            committee_account_id=self.committee.id,
            candidate_office="H",
            candidate_state="MD",
            candidate_district="99",
        )
        candidate_b = Contact.objects.create(
            committee_account_id=self.committee.id,
            candidate_office="H",
            candidate_state="MD",
            candidate_district="99",
        )
        candidate_c = Contact.objects.create(
            committee_account_id=self.committee.id,
            candidate_office="P",
        )
        ies = [
            {  # same election previous year
                "disbursement_date": "2023-01-01",
                "dissemination_date": "2023-01-01",
                "date_signed": "2023-01-01",
                "amount": "123.45",
                "contact": candidate_a,
                "code": "H2024",
            },
            {  # same election same year
                "disbursement_date": "2024-01-01",
                "dissemination_date": "2024-01-01",
                "date_signed": "2024-01-01",
                "amount": "1.00",
                "contact": candidate_a,
                "code": "H2024",
            },
            {  # same election same year
                "disbursement_date": "2024-01-02",
                "dissemination_date": "2024-01-02",
                "date_signed": "2024-01-02",
                "amount": "1.00",
                "contact": candidate_a,
                "code": "H2024",
            },
            {  # same election same year
                "disbursement_date": "2024-01-03",
                "dissemination_date": "2024-01-03",
                "date_signed": "2024-01-03",
                "amount": "2.00",
                "contact": candidate_b,
                "code": "H2024",
            },
            {  # different election same year
                "disbursement_date": "2024-01-04",
                "dissemination_date": "2024-01-04",
                "date_signed": "2024-01-04",
                "amount": "3.00",
                "contact": candidate_c,
                "code": "H2024",
            },
            {  # different election same year
                "disbursement_date": "2024-01-05",
                "dissemination_date": "2024-01-05",
                "date_signed": "2024-01-05",
                "amount": "4.00",
                "contact": candidate_a,
                "code": "Z2024",
            },
        ]

        for ie in ies:
            create_ie(
                self.committee,
                ie["contact"],
                ie["disbursement_date"],
                ie["dissemination_date"],
                ie["date_signed"],
                ie["amount"],
                ie["code"],
                ie["contact"],
            )

        view = get_read_model(self.committee.id).objects.all()

        self.assertEqual(view[0]._calendar_ytd_per_election_office, Decimal("123.45"))
        self.assertEqual(view[1]._calendar_ytd_per_election_office, Decimal("1.00"))
        self.assertEqual(view[2]._calendar_ytd_per_election_office, Decimal("2.00"))
        self.assertEqual(view[3]._calendar_ytd_per_election_office, Decimal("4.00"))
        self.assertEqual(view[4]._calendar_ytd_per_election_office, Decimal("3.00"))
        self.assertEqual(view[5]._calendar_ytd_per_election_office, Decimal("4.00"))

    def test_debts(self):
        q1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        original_debt = create_debt(self.committee, self.contact_1, Decimal("123.00"))
        original_debt.save()
        original_debt.reports.add(q1_report)
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

        view = get_read_model(self.committee.id).objects.all()
        original_debt_view = view.filter(id=original_debt.id).first()
        self.assertEqual(original_debt_view.incurred_prior, Decimal("0"))
        self.assertEqual(original_debt_view.payment_prior, Decimal("0"))
        self.assertEqual(original_debt_view.payment_amount, Decimal("3.50"))

    def test_line_label(self):
        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            "1.00",
            "GENERAL",
            "SA11AI",
            False,
            True,
        )
        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-02",
            "2.00",
            "GENERAl",
            "SA11AI",
        )
        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-03",
            "1000.00",
            "GENERAL",
            "SA11AII",
        )
        create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-01-04",
            "100.00",
            "GENERAL_DISBURSEMENT",
            "SB21B",
        )

        view = get_read_model(self.committee.id).objects.all().order_by("date")
        self.assertEqual(view[0].line_label, "11(a)(i)")
        self.assertEqual(view[1].line_label, "11(a)(ii)")
        self.assertEqual(view[2].line_label, "11(a)(ii)")
        self.assertEqual(view[3].line_label, "21(b)")

    def test_loan_payment_to_date(self):
        m1_report = create_form3x(self.committee, "2024-01-01", "2024-01-31", {})
        loan = create_loan(
            self.committee,
            self.contact_1,
            "5000.00",
            "2024-07-01",
            "7%",
            loan_incurred_date="2024-01-01",
            report=m1_report,
        )
        create_schedule_b(
            "LOAN_REPAYMENT_MADE",
            self.committee,
            self.contact_1,
            "2024-01-02",
            "1000.00",
            loan_id=loan.id,
            report=m1_report,
        )
        create_schedule_b(
            "LOAN_REPAYMENT_MADE",
            self.committee,
            self.contact_1,
            "2024-01-03",
            "500.00",
            loan_id=loan.id,
            report=m1_report,
        )
        view: QuerySet = Transaction.objects.transaction_view()
        transactions = view.filter(committee_account_id=self.committee.id).order_by(
            "date"
        )
        self.assertEqual(transactions[0].amount, Decimal("5000.00"))
        self.assertEqual(transactions[0].loan_payment_to_date, Decimal("1500.00"))
        self.assertEqual(transactions[1].amount, Decimal("1000.00"))
        self.assertEqual(transactions[2].amount, Decimal("500.00"))

        # Pull loan forward and make sure payments are still correct

        m2_report = create_form3x(self.committee, "2024-02-01", "2024-02-28", {})
        carry_forward_loans(m2_report)
        carried_forward_loan = (
            view.filter(committee_account_id=self.committee.id).order_by("created").last()
        )
        create_schedule_b(
            "LOAN_REPAYMENT_MADE",
            self.committee,
            self.contact_1,
            "2024-02-05",
            "600.00",
            loan_id=carried_forward_loan.id,
            report=m2_report,
        )
        transactions = view.filter(committee_account_id=self.committee.id).order_by(
            "created"
        )
        self.assertEqual(transactions[0].amount, Decimal("5000.00"))
        self.assertEqual(transactions[0].loan_payment_to_date, Decimal("1500.00"))
        self.assertEqual(transactions[1].amount, Decimal("1000.00"))
        self.assertEqual(transactions[2].amount, Decimal("500.00"))
        self.assertEqual(transactions[4].amount, Decimal("5000.00"))
        self.assertEqual(transactions[4].loan_payment_to_date, Decimal("2100.00"))
        self.assertEqual(transactions[5].amount, Decimal("600.00"))

    def test_itemization(self):
        scha = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            "20.00",
            "GENERAL",
            "SA11AI",
            False,
            None,
        )
        obs = Transaction.objects.transaction_view().filter(id=scha.id)
        self.assertFalse(obs[0]._itemized)

        schb = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-01-04",
            "20.00",
            "GENERAL_DISBURSEMENT",
            "SB21B",
        )
        obs = Transaction.objects.transaction_view().filter(id=schb.id)
        self.assertFalse(obs[0]._itemized)

        scha = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            "250.00",
            "GENERAL",
            "SA11AI",
            False,
            None,
        )
        obs = Transaction.objects.transaction_view().filter(id=scha.id)
        self.assertTrue(obs[0]._itemized)

        schb = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-01-04",
            "250.00",
            "GENERAL_DISBURSEMENT",
            "SB21B",
        )
        obs = Transaction.objects.transaction_view().filter(id=schb.id)
        self.assertTrue(obs[0]._itemized)

        candidate_a = Contact.objects.create(
            committee_account_id=self.committee.id,
            candidate_office="H",
            candidate_state="MD",
            candidate_district="99",
        )
        ie = create_ie(
            self.committee,
            candidate_a,
            "2023-01-01",
            "2023-01-01",
            "2023-01-01",
            "123.45",
            "H2024",
            candidate_a,
        )
        obs = Transaction.objects.transaction_view().filter(id=ie.id)
        self.assertTrue(obs[0]._itemized)

        ie = create_ie(
            self.committee,
            candidate_a,
            "2023-01-01",
            "2023-01-01",
            "2023-01-01",
            "250.45",
            "H2024",
            candidate_a,
        )
        obs = Transaction.objects.transaction_view().filter(id=ie.id)
        self.assertTrue(obs[0]._itemized)
