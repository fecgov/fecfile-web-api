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
        self.assertEqual(summary["line_11ai"], Decimal("10000.23"))
        self.assertEqual(summary["line_11aii"], Decimal("333.33"))
        self.assertEqual(summary["line_11aiii"], round(Decimal(333.33 + 10000.23), 2))
        self.assertEqual(summary["line_11b"], Decimal("444.44"))
        self.assertEqual(summary["line_11c"], Decimal("555.55"))
        self.assertEqual(summary["line_11d"], round(
            Decimal(333.33 + 10000.23 + 444.44 + 555.55), 2)
        )
        self.assertEqual(summary["line_12"], Decimal("1212.12"))
        self.assertEqual(summary["line_15"], Decimal("2125.79"))
        self.assertEqual(summary["line_33"], round(
            Decimal(333.33 + 10000.23 + 444.44 + 555.55), 2)
        )

    def test_report_with_no_transactions(self):
        f3x = F3XSummary.objects.get(id="a07c8c65-1b2d-4e6e-bcaa-fa8d39e50965")
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()
        self.assertEqual(summary["line_15"], Decimal("0"))
