from django.test import TestCase
from django.db.models import QuerySet

from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact
from fecfiler.transactions.models import Transaction, Schedule
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.managers import TransactionManager
from fecfiler.transactions.tests.utils import (
    create_test_transaction,
    create_schedule_a,
    create_ie,
)
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


class TransactionViewTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.contact_1 = Contact.objects.create(committee_account_id=self.committee.id)

    def test_transaction_view(self):
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
