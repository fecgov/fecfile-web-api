from datetime import datetime
from decimal import Decimal
from django.test import TestCase
from .tasks import CalculationState, calculate_summary
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.reports.models import Report
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.contacts.tests.utils import create_test_individual_contact
from fecfiler.transactions.tests.utils import create_schedule_a
from .tests.utils import generate_data
from fecfiler.f3x_line6a_overrides.models import F3xLine6aOverride


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
        F3xLine6aOverride.objects.create(
            year="2005",
            cash_on_hand=61,
        )

    def test_summary_task(self):
        generate_data(self.committee, self.contact_1, self.q1_report, ["a"])
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
        generate_data(self.committee, self.contact_1, self.q1_report, ["a"])
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

    def test_report_group_recalculation_year_to_year(self):
        next_year_report = create_form3x(
            self.committee,
            datetime.strptime("2006-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2006-03-31", "%Y-%m-%d").date(),
            report_code="Q1",
        )

        self.q1_report.calculation_status = None
        self.q1_report.save()
        self.q2_report.calculation_status = None
        self.q2_report.save()

        transaction_data = [
            {
                "date": "2005-02-01",
                "amount": "10000.23",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
                "report": self.q1_report
            },
            {
                "date": "2005-05-01",
                "amount": "2000.05",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
                "report": self.q2_report
            },
            {
                "date": "2005-07-01",
                "amount": "500.25",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
                "report": self.q3_report
            },
            {
                "date": "2006-02-01",
                "amount": "100.00",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
                "report": next_year_report
            },
        ]
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
            scha.reports.add(data["report"])
            scha.save()

        calculate_summary(next_year_report.id)
        next_year_report.refresh_from_db()
        self.q2_report.refresh_from_db()
        self.q3_report.refresh_from_db()

        self.assertEqual(
            self.q2_report.form_3x.L8_cash_on_hand_close_ytd,
            Decimal("12061.28"),
        )
        self.assertEqual(
            self.q3_report.form_3x.L8_cash_on_hand_close_ytd,
            Decimal("12561.53"),
        )
        self.assertEqual(
            next_year_report.form_3x.L6b_cash_on_hand_beginning_period,
            Decimal("12561.53"),
        )
        self.assertEqual(
            next_year_report.form_3x.L6a_cash_on_hand_jan_1_ytd, Decimal("12561.53")
        )
        self.assertEqual(
            next_year_report.form_3x.L8_cash_on_hand_at_close_period,  # noqa: E501
            Decimal("12661.53"),
        )
