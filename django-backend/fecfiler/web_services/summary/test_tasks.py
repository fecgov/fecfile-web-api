from datetime import datetime
from decimal import Decimal
from django.test import TestCase
from .tasks import CalculationState, calculate_summary
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.reports.models import Report
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.contacts.tests.utils import create_test_individual_contact
from .tests.utils import generate_data


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
