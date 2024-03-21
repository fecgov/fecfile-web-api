from django.test import TestCase
from django.db.models import QuerySet

from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact
from fecfiler.transactions.models import Transaction, Schedule, get_read_model
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.managers import TransactionManager
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.views import create_committee_view

from fecfiler.transactions.tests.utils import (
    create_test_transaction,
    create_schedule_b,
    create_schedule_a,
    create_ie,
    create_debt,
)
import time
from decimal import Decimal


class TransactionViewTestCase(TestCase):
    def setUp(self):
        print("SETUP")
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        self.contact_1 = Contact.objects.create(committee_account_id=self.committee.id)

    def test_transaction_view(self):
        print(f"AHOY{self.committee.id}")
        indiviual_reciepts = [
            {"date": "2023-01-01", "amount": "123.45", "group": "GENERAL"},
            {"date": "2024-01-01", "amount": "100.00", "group": "GENERAL"},
            {"date": "2024-01-01", "amount": "200.00", "group": "GENERAL"},
            {"date": "2024-01-01", "amount": "100.00", "group": "OTHER"},
        ]
        for receipt_data in indiviual_reciepts:
            create_schedule_a(
                "IDIVIDUAL_RECEIPT",
                self.committee,
                self.contact_1,
                receipt_data["date"],
                receipt_data["amount"],
                receipt_data["group"],
            )

        view: QuerySet = Transaction.objects.transaction_view()
        view = view.filter(committee_account_id=self.committee.id)
        self.assertEqual(view[0].aggregate, Decimal("123.45"))
        self.assertEqual(view[2].aggregate, Decimal("300"))
        self.assertEqual(view[3].aggregate, Decimal("100"))

    def test_force_unaggregated(self):
        print(f"AHOY{self.committee.id}")

        unaggregated = create_test_transaction(
            "IDIVIDUAL_RECEIPT",
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
            "IDIVIDUAL_RECEIPT",
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
        view = view.filter(committee_account_id=self.committee.id)
        self.assertEqual(view[0].aggregate, Decimal("0"))
        self.assertEqual(view[0].force_unaggregated, True)
        self.assertEqual(view[1].aggregate, Decimal("200"))

    def test_transaction_view_parent(self):
        print(f"AHOY{self.committee.id}")
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

    def test_refund_aggregate(self):
        print(f"AHOY{self.committee.id}")
        create_schedule_a(
            "IDIVIDUAL_RECEIPT",
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
            "2024-01-01",
            "100.00",
            "NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
        )
        view: QuerySet = Transaction.objects.transaction_view()
        view = view.filter(committee_account_id=self.committee.id)
        self.assertEqual(view[0].aggregate, Decimal("123.00"))
        self.assertEqual(view[1].aggregate, Decimal("23.00"))

    def test_election_aggregate(self):
        print(f"AHOY{self.committee.id}")
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
                "date": "2023-01-01",
                "amount": "123.45",
                "contact": candidate_a,
                "code": "H2024",
            },
            {  # same election same year
                "date": "2024-01-01",
                "amount": "1.00",
                "contact": candidate_a,
                "code": "H2024",
            },
            {  # same election same year
                "date": "2024-01-02",
                "amount": "1.00",
                "contact": candidate_a,
                "code": "H2024",
            },
            {  # same election same year
                "date": "2024-01-02",
                "amount": "2.00",
                "contact": candidate_b,
                "code": "H2024",
            },
            {  # different election same year
                "date": "2024-01-03",
                "amount": "3.00",
                "contact": candidate_c,
                "code": "H2024",
            },
            {  # different election same year
                "date": "2024-01-04",
                "amount": "4.00",
                "contact": candidate_a,
                "code": "Z2024",
            },
        ]

        for ie in ies:
            create_ie(
                self.committee, ie["contact"], ie["date"], ie["amount"], ie["code"]
            )

        view: QuerySet = Transaction.objects.transaction_view()
        view = view.filter(committee_account_id=self.committee.id)
        self.assertEqual(view[0]._calendar_ytd_per_election_office, Decimal("123.45"))
        self.assertEqual(view[1]._calendar_ytd_per_election_office, Decimal("1.00"))
        self.assertEqual(view[2]._calendar_ytd_per_election_office, Decimal("2.00"))
        self.assertEqual(view[3]._calendar_ytd_per_election_office, Decimal("4.00"))
        self.assertEqual(view[4]._calendar_ytd_per_election_office, Decimal("3.00"))
        self.assertEqual(view[5]._calendar_ytd_per_election_office, Decimal("4.00"))

    def test_debts(self):
        print(f"AHOY{self.committee.id}")
        q1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        original_debt = create_debt(self.committee, self.contact_1, Decimal("123.00"))
        original_debt.report = q1_report
        original_debt.save()
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
        first_schedule_a = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-01",
            "1.00",
            "GENERAL",
            "SA11II",
        )
        first_schedule_a.force_itemized = True
        first_schedule_a.save()
        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-02",
            "2.00",
            "GENERAl",
            "SA11II",
        )
        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-01-03",
            "1000.00",
            "GENERAL" "SA11I",
        )
        create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-01-01",
            "100.00",
            "GENERAL_DISBURSEMENT",
            "SB21B",
        )

        print(f"AHOY line_label {self.committee.id}")
        view = get_read_model(self.committee.id).objects.all()
        self.assertEqual(getattr(view[0], "line_label"), "11(a)i")
        self.assertEqual(getattr(view[1], "line_label"), "11(a)ii")
        self.assertEqual(getattr(view[2], "line_label"), "11(a)i")
        self.assertEqual(getattr(view[3], "line_label"), "21(b)")
