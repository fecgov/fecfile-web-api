from datetime import datetime
from decimal import Decimal
from django.test import TestCase
from .tasks import CalculationState, calculate_summary
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.reports.models import Report
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_schedule_a
from fecfiler.contacts.tests.utils import create_test_individual_contact


class F3XSerializerTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )
        self.q1_report = create_form3x(
            self.committee,
            datetime.strptime("2005-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2005-02-28", "%Y-%m-%d").date(),
            {"L6a_cash_on_hand_jan_1_ytd": 61},
        )
        self.q2_report = create_form3x(
            self.committee,
            datetime.strptime("2005-03-01", "%Y-%m-%d").date(),
            datetime.strptime("2005-05-01", "%Y-%m-%d").date(),
            {},
            "Q2",
        )
        self.q3_report = create_form3x(
            self.committee,
            datetime.strptime("2005-09-01", "%Y-%m-%d").date(),
            datetime.strptime("2005-10-01", "%Y-%m-%d").date(),
            {},
            "Q3",
        )

    def test_summary_task(self):
        self.generate_data()
        report_id = calculate_summary("not_an_existing_report")
        self.assertIsNone(report_id)

        report_id = calculate_summary(self.q1_report.id)
        report = Report.objects.get(id=report_id)
        self.assertEqual(
            report.form_3x.L15_offsets_to_operating_expenditures_refunds_period,
            Decimal("2125.79"),
        )
        self.assertEqual(
            report.form_3x.L37_offsets_to_operating_expenditures_period,
            Decimal("2125.79"),
        )
        self.assertEqual(report.calculation_status, CalculationState.SUCCEEDED.value)

    def test_report_with_no_transactions(self):
        report_id = calculate_summary(self.q2_report.id)
        report = Report.objects.get(id=report_id)
        self.assertEqual(
            report.form_3x.L15_offsets_to_operating_expenditures_refunds_period,
            Decimal("0"),
        )
        self.assertEqual(
            report.form_3x.L37_offsets_to_operating_expenditures_period, Decimal("0")
        )
        self.assertEqual(report.calculation_status, CalculationState.SUCCEEDED.value)

    def test_report_group_recalculation(self):
        self.generate_data()
        previous_report = self.q1_report
        previous_report.calculation_status = None
        previous_report.save()

        self.q2_report.calculation_status = None
        self.q2_report.save()

        calculate_summary(self.q2_report.id)
        calculated_report = Report.objects.get(id=self.q2_report.id)
        calculated_prev_report = Report.objects.get(id=self.q1_report.id)

        self.assertEqual(
            calculated_report.form_3x.L6b_cash_on_hand_beginning_period,
            Decimal("18146.17"),
        )
        self.assertEqual(
            calculated_report.form_3x.L6a_cash_on_hand_jan_1_ytd, Decimal("61.00")
        )
        self.assertEqual(
            calculated_prev_report.form_3x.L15_offsets_to_operating_expenditures_refunds_period,  # noqa: E501
            Decimal("2125.79"),
        )

    def generate_data(self):
        sch_a_transactions = [
            {
                "date": "2005-02-01",
                "amount": "10000.23",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-02-08",
                "amount": "3.77",
                "group": "GENERAL",
                "form_type": "SA11AII",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "444.44",
                "group": "GENERAL",
                "form_type": "SA11B",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "555.55",
                "group": "OTHER",
                "form_type": "SA11C",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1212.12",
                "group": "GENERAL",
                "form_type": "SA12",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1313.13",
                "group": "GENERAL",
                "form_type": "SA13",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1414.14",
                "group": "GENERAL",
                "form_type": "SA14",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1234.56",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "OFFSET_TO_OPEX",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "891.23",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "OFFSET_TO_OPEX",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "10000.23",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "OFFSET_TO_OPEX",
                "memo": True,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "16",
                "group": "GENERAL",
                "form_type": "SA16",
                "tti": "REFUND_TO_FEDERAL_CANDIDATE",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "200.50",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "-1",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "800.50",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
        ]

        self.gen_schedule_a(sch_a_transactions, self.q1_report)

        other_f3x = create_form3x(
            self.committee,
            datetime.strptime("2007-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2007-02-28", "%Y-%m-%d").date(),
            {"L6a_cash_on_hand_jan_1_ytd": 61},
        )

        sch_a_transactions = [
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2022-03-01",
                "amount": "8.23",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA11B",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA11B",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA11C",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA11C",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA12",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA12",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA13",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA13",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA14",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA14",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA16",
                "tti": "REFUND_TO_FEDERAL_CANDIDATE",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-05-01",
                "amount": "1000.00",
                "group": "GENERAL",
                "form_type": "SA16",
                "tti": "REFUND_TO_FEDERAL_CANDIDATE",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "300.00",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": True,
                "itemized": True,
            },
        ]

        self.gen_schedule_a(sch_a_transactions, other_f3x)

    def gen_schedule_a(self, transaction_data, f3x):
        for data in transaction_data:
            scha = create_schedule_a(
                data["tti"],
                self.committee,
                self.contact_1,
                data["date"],
                data["amount"],
                data["group"],
                data["form_type"],
                data["memo"],
                data["itemized"],
            )
            scha.reports.add(f3x)
            scha.save()
            if data["form_type"] == "SA11AII":
                self.debt = scha
