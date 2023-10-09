from decimal import Decimal
from django.test import TestCase
from .tasks import CalculationState, calculate_summary
from fecfiler.reports.models import Report


class F3XSerializerTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_contacts",
        "test_f3x_reports",
        "test_schedulea_summary_transactions",
    ]

    def test_summary_task(self):
        report_id = calculate_summary("not_an_existing_report")
        self.assertIsNone(report_id)

        report_id = calculate_summary("b6d60d2d-d926-4e89-ad4b-c47d152a66ae")
        report = Report.objects.get(id=report_id)
        self.assertEqual(
            report.report_f3x.L15_offsets_to_operating_expenditures_refunds_period,
            Decimal("2125.79"),
        )
        self.assertEqual(
            report.report_f3x.L37_offsets_to_operating_expenditures_period,
            Decimal("2125.79"),
        )
        self.assertEqual(
            report.report_f3x.calculation_status, CalculationState.SUCCEEDED.value
        )

    def test_report_with_no_transactions(self):
        report_id = calculate_summary("a07c8c65-1b2d-4e6e-bcaa-fa8d39e50965")
        report = Report.objects.get(id=report_id)
        self.assertEqual(
            report.report_f3x.L15_offsets_to_operating_expenditures_refunds_period,
            Decimal("0"),
        )
        self.assertEqual(
            report.report_f3x.L37_offsets_to_operating_expenditures_period, Decimal("0")
        )
        self.assertEqual(
            report.report_f3x.calculation_status, CalculationState.SUCCEEDED.value
        )
