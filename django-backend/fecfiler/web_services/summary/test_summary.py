from decimal import Decimal
from django.test import TestCase
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.transactions.models import Transaction
from .summary import SummaryService


class F3XSummaryTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_schedulea_summary_transactions",
        "test_scheduleb_summary_transactions",
        "test_contacts",
    ]

    def test_calculate_summary_column_a(self):
        f3x = F3XSummary.objects.get(id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae")
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()
        self.assertEqual(summary["a"]["line_11ai"], Decimal("10000.23"))
        self.assertEqual(summary["a"]["line_11aii"], Decimal("3.77"))
        self.assertEqual(
            summary["a"]["line_11aiii"], round(Decimal(3.77 + 10000.23), 2)
        )
        self.assertEqual(summary["a"]["line_11b"], Decimal("444.44"))
        self.assertEqual(summary["a"]["line_11c"], Decimal("555.55"))
        self.assertEqual(
            summary["a"]["line_11d"],
            round(Decimal(3.77 + 10000.23 + 444.44 + 555.55), 2),
        )
        self.assertEqual(summary["a"]["line_12"], Decimal("1212.12"))
        self.assertEqual(summary["a"]["line_15"], Decimal("2125.79"))
        self.assertEqual(summary["a"]["line_15"], summary["a"]["line_37"])
        self.assertEqual(summary["a"]["line_16"], Decimal("16.00"))
        self.assertEqual(summary["a"]["line_17"], Decimal("1000.00"))
        self.assertEqual(summary["a"]["line_21b"], Decimal("150.00"))
        self.assertEqual(summary["a"]["line_22"], Decimal("22.00"))
        self.assertEqual(summary["a"]["line_28a"], Decimal("101.50"))
        self.assertEqual(summary["a"]["line_28b"], Decimal("201.50"))
        self.assertEqual(summary["a"]["line_28c"], Decimal("301.50"))
        self.assertEqual(
            summary["a"]["line_28d"], round(Decimal(101.50 + 201.50 + 301.50), 2)
        )
        self.assertEqual(
            summary["a"]["line_33"],
            round(Decimal(3.77 + 10000.23 + 444.44 + 555.55), 2),
        )
        self.assertEqual(
            summary["a"]["line_34"], round(Decimal(101.50 + 201.50 + 301.50), 2)
        )

    def test_calculate_summary_column_b(self):
        f3x = F3XSummary.objects.get(id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae")
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()

        t = Transaction.objects.get(id="aaaaaaaa-4d75-46f0-bce2-111000000001")
        self.assertEqual(t.itemized, False)

        self.assertEqual(summary["b"]["line_11ai"], Decimal("10000.23"))
        self.assertEqual(summary["b"]["line_11aii"], Decimal("103.77"))
        self.assertEqual(summary["b"]["line_11aiii"], Decimal(10104.00))
        self.assertEqual(summary["b"]["line_11b"], Decimal("544.44"))
        self.assertEqual(summary["b"]["line_11c"], Decimal("655.55"))
        self.assertEqual(
            summary["b"]["line_11d"], round(Decimal(10104.00 + 544.44 + 655.55), 2)
        )

        self.assertEqual(summary["b"]["line_12"], Decimal("1312.12"))
        self.assertEqual(summary["b"]["line_15"], Decimal("2225.79"))
        self.assertEqual(summary["b"]["line_16"], Decimal("116.00"))
        self.assertEqual(summary["b"]["line_17"], Decimal("1100.00"))
        self.assertEqual(summary["a"]["line_21b"], Decimal("250.00"))
        self.assertEqual(summary["b"]["line_28a"], Decimal("1101.50"))
        self.assertEqual(summary["b"]["line_28b"], Decimal("2201.50"))
        self.assertEqual(summary["b"]["line_28c"], Decimal("3301.50"))
        self.assertEqual(
            summary["b"]["line_28d"], round(Decimal(1101.50 + 2201.50 + 3301.50), 2)
        )
        self.assertEqual(
            summary["b"]["line_33"], round(Decimal(10104.00 + 544.44 + 655.55), 2)
        )
        self.assertEqual(
            summary["b"]["line_34"], round(Decimal(1101.50 + 2201.50 + 3301.50), 2)
        )

    def test_report_with_no_transactions(self):
        f3x = F3XSummary.objects.get(id="a07c8c65-1b2d-4e6e-bcaa-fa8d39e50965")
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()
        self.assertEqual(summary["a"]["line_15"], Decimal("0"))
        self.assertEqual(summary["a"]["line_17"], Decimal("0"))
