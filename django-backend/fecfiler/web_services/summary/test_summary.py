from decimal import Decimal
from django.test import TestCase
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from .summary import SummaryService


class F3XReportTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_reports",
        "test_schedulea_summary_transactions",
        "test_scheduleb_summary_transactions",
        "test_schedulec_summary_transactions",
        "test_scheduled_summary_transactions",
        "test_schedulee_summary_transactions",
        "test_contacts",
    ]

    def test_calculate_summary_column_a(self):
        f3x = Report.objects.get(id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae")
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()

        summary_a = summary["a"]

        self.assertEqual(summary_a["line_6c"], Decimal("18085.17"))
        self.assertEqual(
            summary_a["line_6d"],
            Decimal("0") +  # line_6b
            + Decimal("18146.17")  # line_6c
        )
        self.assertEqual(
            summary_a["line_7"],
            Decimal("150.00")  # line_21c
            + Decimal("22.00")  # line_22
            + Decimal("14.00")  # line_23
            + Decimal("141.00")  # line_24
            + Decimal("0")  # line_25
            + Decimal("44.00")  # line_26
            + Decimal("31.00")  # line_27
            + Decimal(101.50 + 201.50 + 301.50)  # line_28d
            + Decimal("201.50")  # line_29
            + Decimal("102.25")  # line_30c
        )
        self.assertEqual(
            summary_a["line_8"],
            summary_a["line_6d"]
            - summary_a["line_7"]
        )
        self.assertEqual(summary_a["line_9"], Decimal("225.00"))
        self.assertEqual(summary_a["line_10"], Decimal("250.00"))
        self.assertEqual(summary_a["line_11ai"], Decimal("10000.23"))
        self.assertEqual(summary_a["line_11aii"], Decimal("3.77"))
        self.assertEqual(
            summary_a["line_11aiii"],
            Decimal("10000.23")  # line_11ai
            + Decimal("3.77")  # line_11aii
        )
        self.assertEqual(summary_a["line_11b"], Decimal("444.44"))
        self.assertEqual(summary_a["line_11c"], Decimal("555.55"))
        self.assertEqual(
            summary_a["line_11d"],
            Decimal("10000.23")  # line_11ai
            + Decimal("3.77")  # line_11aii
            + Decimal("444.44")  # line_11b
            + Decimal("555.55")  # line_11c
        )
        self.assertEqual(summary_a["line_12"], Decimal("1212.12"))
        self.assertEqual(summary_a["line_13"], Decimal("1313.13"))
        self.assertEqual(summary_a["line_14"], Decimal("1414.14"))
        self.assertEqual(summary_a["line_15"], Decimal("2125.79"))
        self.assertEqual(summary_a["line_16"], Decimal("16.00"))
        self.assertEqual(summary_a["line_17"], Decimal("1000.00"))
        self.assertEqual(summary_a["line_19"], Decimal("18085.17"))
        self.assertEqual(summary_a["line_20"], Decimal("18085.17"))
        self.assertEqual(summary_a["line_21b"], Decimal("150.00"))
        self.assertEqual(summary_a["line_21c"], Decimal("150.00"))
        self.assertEqual(summary_a["line_22"], Decimal("22.00"))
        self.assertEqual(summary_a["line_23"], Decimal("14.00"))
        self.assertEqual(summary_a["line_24"], Decimal("141.00"))
        self.assertEqual(summary_a["line_26"], Decimal("44.00"))
        self.assertEqual(summary_a["line_27"], Decimal("31.00"))
        self.assertEqual(summary_a["line_28a"], Decimal("101.50"))
        self.assertEqual(summary_a["line_28b"], Decimal("201.50"))
        self.assertEqual(summary_a["line_28c"], Decimal("301.50"))
        self.assertEqual(
            summary_a["line_28d"],
            Decimal(101.50)  # line_28a
            + Decimal(201.50)  # line_28b
            + Decimal(301.50)  # line_28c
        )
        self.assertEqual(summary_a["line_29"], Decimal("201.50"))
        self.assertEqual(summary_a["line_30b"], Decimal("102.25"))
        self.assertEqual(summary_a["line_30c"], Decimal("102.25"))
        self.assertEqual(summary_a["line_31"], summary_a["line_7"])
        self.assertEqual(
            summary_a["line_32"],
            summary_a["line_31"]  # line_31
            - Decimal("0")  # line_21aii
            - Decimal("0")  # line_30aii
        )
        self.assertEqual(summary_a["line_33"], summary_a["line_11d"])
        self.assertEqual(summary_a["line_34"], summary_a["line_28d"])
        self.assertEqual(
            summary_a["line_35"],
            summary_a["line_33"]
            - summary_a["line_34"]
        )
        self.assertEqual(summary_a["line_36"], Decimal("150.00"))
        self.assertEqual(summary_a["line_37"], Decimal("2125.79"))
        self.assertEqual(
            summary_a["line_38"],
            Decimal("150.00")  # line_36
            - Decimal("2125.79")  # line_37
        )

    def test_calculate_summary_column_b(self):
        f3x = Report.objects.get(id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae")
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()

        summary_b = summary["b"]

        t = Transaction.objects.get(id="aaaaaaaa-4d75-46f0-bce2-111000000001")
        self.assertEqual(t.itemized, False)

        self.assertEqual(summary_b["line_6c"], Decimal("18985.17"))
        self.assertEqual(
            summary_b["line_6d"],
            Decimal("0")  # line_6a
            + Decimal("19046.17")  # line_6c
        )
        self.assertEqual(
            summary_b["line_7"],
            Decimal("250.00")  # line_21c
            + Decimal("122.00")  # line_22
            + Decimal("64.00")  # line_23
            + Decimal("286.00")  # line_24
            + Decimal("0")  # line_25
            + Decimal("61.00")  # line_26
            + Decimal("41.00")  # line_27
            + Decimal(1101.50 + 2201.50 + 3301.50)  # line_28d
            + Decimal("1201.50")  # line_29
            + Decimal("1102.25")  # line_30c
        )
        self.assertEqual(
            summary_b["line_8"],
            summary_b["line_6d"]
            - summary_b["line_7"]
        )
        self.assertEqual(summary_b["line_11ai"], Decimal("10000.23"))
        self.assertEqual(summary_b["line_11aii"], Decimal("103.77"))
        self.assertEqual(summary_b["line_11aiii"], Decimal("10104.00"))
        self.assertEqual(summary_b["line_11b"], Decimal("544.44"))
        self.assertEqual(summary_b["line_11c"], Decimal("655.55"))
        self.assertEqual(
            summary_b["line_11d"],
            Decimal("10104.00")  # line_11aiii
            + Decimal("544.44")  # line_11b
            + Decimal("655.55")  # line_11c
        )

        self.assertEqual(summary_b["line_12"], Decimal("1312.12"))
        self.assertEqual(summary_b["line_13"], Decimal("1413.13"))
        self.assertEqual(summary_b["line_14"], Decimal("1514.14"))
        self.assertEqual(summary_b["line_15"], Decimal("2225.79"))
        self.assertEqual(summary_b["line_16"], Decimal("116.00"))
        self.assertEqual(summary_b["line_17"], Decimal("1100.00"))
        self.assertEqual(summary_b["line_19"], Decimal("18985.17"))
        self.assertEqual(summary_b["line_20"], Decimal("18985.17"))
        self.assertEqual(summary_b["line_21b"], Decimal("250.00"))
        self.assertEqual(summary_b["line_21c"], Decimal("250.00"))
        self.assertEqual(summary_b["line_22"], Decimal("122.00"))
        self.assertEqual(summary_b["line_23"], Decimal("64.00"))
        self.assertEqual(summary_b["line_24"], Decimal("286.00"))
        self.assertEqual(summary_b["line_26"], Decimal("61.00"))
        self.assertEqual(summary_b["line_27"], Decimal("41.00"))
        self.assertEqual(summary_b["line_28a"], Decimal("1101.50"))
        self.assertEqual(summary_b["line_28b"], Decimal("2201.50"))
        self.assertEqual(summary_b["line_28c"], Decimal("3301.50"))
        self.assertEqual(
            summary_b["line_28d"],
            Decimal("1101.50")  # line_28a
            + Decimal("2201.50")  # line_28b
            + Decimal("3301.50")  # line_28c
        )
        self.assertEqual(summary_b["line_29"], Decimal("1201.50"))
        self.assertEqual(summary_b["line_30b"], Decimal("1102.25"))
        self.assertEqual(summary_b["line_30c"], Decimal("1102.25"))
        self.assertEqual(summary_b["line_31"], summary_b["line_7"])
        self.assertEqual(
            summary_b["line_32"],
            summary_b["line_31"]  # line_31
            - Decimal("0")  # line_21aii
            - Decimal("0")  # line_30aii
        )
        self.assertEqual(summary_b["line_33"], summary_b["line_11d"])
        self.assertEqual(summary_b["line_34"], summary_b["line_28d"])
        self.assertEqual(
            summary_b["line_35"],
            summary_b["line_33"]
            - summary_b["line_34"],
        )
        self.assertEqual(summary_b["line_36"], Decimal("250.00"))
        self.assertEqual(summary_b["line_37"], Decimal("2225.79"))
        self.assertEqual(
            summary_b["line_38"],
            Decimal("250.00")  # line_36
            - Decimal("2225.79")  # line_37
        )

    def test_report_with_no_transactions(self):
        f3x = Report.objects.get(id="a07c8c65-1b2d-4e6e-bcaa-fa8d39e50965")
        summary_service = SummaryService(f3x)
        summary = summary_service.calculate_summary()
        self.assertEqual(summary["a"]["line_15"], Decimal("0"))
        self.assertEqual(summary["a"]["line_17"], Decimal("0"))
