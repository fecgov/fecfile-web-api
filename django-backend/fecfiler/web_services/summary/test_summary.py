from decimal import Decimal
from django.test import TestCase
from fecfiler.f3x_summaries.models import F3XSummary
from .summary import SummaryService


class F3XSerializerTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_summary_transactions",
    ]

    def test_calculate_summary(self):
        f3x = F3XSummary.objects.get(id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae")
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()
        self.assertEqual(summary["a"]["line_12"], Decimal("1212.12"))
        self.assertEqual(summary["a"]["line_17"], Decimal("1000.00"))
        self.assertEqual(summary["a"]["line_15"], Decimal("2125.79"))
        self.assertEqual(summary["a"]["line_15"], summary["a"]["line_37"])

    def test_report_with_no_transactions(self):
        f3x = F3XSummary.objects.get(id="a07c8c65-1b2d-4e6e-bcaa-fa8d39e50965")
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()
        self.assertEqual(summary["a"]["line_15"], Decimal("0"))
