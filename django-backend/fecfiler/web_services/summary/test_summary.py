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

    def setUp(self):
        pass

    def test_calculate_summary(self):
        f3x = F3XSummary.objects.get(id=9999)
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()
        self.assertEqual(summary["line_15"], Decimal("2125.79"))

    def test_report_with_no_transactions(self):
        f3x = F3XSummary.objects.get(id=10000)
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()
        self.assertEqual(summary["line_15"], Decimal("0"))
