from decimal import Decimal
from django.test import TestCase
from .tasks import CalculationState, calculate_summary
from fecfiler.f3x_summaries.models import F3XSummary


class F3XSerializerTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_summary_transactions",
    ]

    def test_summary_task(self):
        report_id = calculate_summary("not_an_existing_report")
        self.assertIsNone(report_id)

        report_id = calculate_summary("b6d60d2d-d926-4e89-ad4b-c47d152a66ae")
        report = F3XSummary.objects.get(id=report_id)
        self.assertEqual(
            report.L15_offsets_to_operating_expenditures_refunds_period,
            Decimal("2125.79"),
        )
        self.assertEqual(
            report.L37_offsets_to_operating_expenditures_period, Decimal("2125.79")
        )
        self.assertEqual(report.calculation_status, CalculationState.SUCCEEDED)

    def test_report_with_no_transactions(self):
        report_id = calculate_summary("a07c8c65-1b2d-4e6e-bcaa-fa8d39e50965")
        report = F3XSummary.objects.get(id=report_id)
        self.assertEqual(
            report.L15_offsets_to_operating_expenditures_refunds_period,
            Decimal("0"),
        )
        self.assertEqual(
            report.L37_offsets_to_operating_expenditures_period, Decimal("0")
        )
        self.assertEqual(report.calculation_status, CalculationState.SUCCEEDED)
