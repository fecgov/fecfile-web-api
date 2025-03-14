from decimal import Decimal
from django.test import TestCase
from fecfiler.committee_accounts.models import CommitteeAccount
from .summary import SummaryService
from fecfiler.reports.tests.utils import create_form3x
from datetime import datetime
from fecfiler.contacts.tests.utils import create_test_individual_contact
from .tests.utils import generate_data
from fecfiler.cash_on_hand.tests.utils import create_cash_on_hand_yearly


class F3XReportTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )

    def test_calculate_summary_column_a(self):
        create_cash_on_hand_yearly(
            committee_account=self.committee,
            year="2005",
            cash_on_hand=61,
        )
        f3x = create_form3x(
            self.committee,
            datetime.strptime("2005-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2005-02-28", "%Y-%m-%d").date(),
            report_code="12C",
        )
        self.debt = generate_data(
            self.committee, self.contact_1, f3x, ["a", "b", "c", "d", "e", "f"]
        )
        summary_service = SummaryService(f3x)
        summary_a, _ = summary_service.calculate_summary_columns()

        self.assertEqual(summary_a["line_6c"], Decimal("18085.17"))
        self.assertEqual(
            summary_a["line_6d"],
            Decimal("0") + +Decimal("18146.17"),  # line_6b  # line_6c
        )
        self.assertEqual(summary_a["line_8"], summary_a["line_6d"] - summary_a["line_7"])
        self.assertEqual(summary_a["line_9"], Decimal("250.00"))
        self.assertEqual(summary_a["line_10"], Decimal("250.00"))
        self.assertEqual(summary_a["line_11ai"], Decimal("10000.23"))
        self.assertEqual(summary_a["line_11aii"], Decimal("3.77"))
        self.assertEqual(
            summary_a["line_11aiii"],
            Decimal("10000.23") + Decimal("3.77"),  # line_11ai  # line_11aii
        )
        self.assertEqual(summary_a["line_11b"], Decimal("444.44"))
        self.assertEqual(summary_a["line_11c"], Decimal("555.55"))
        self.assertEqual(
            summary_a["line_11d"],
            Decimal("10000.23")  # line_11ai
            + Decimal("3.77")  # line_11aii
            + Decimal("444.44")  # line_11b
            + Decimal("555.55"),  # line_11c
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
        self.assertEqual(summary_a["line_24"], Decimal("151.00"))
        self.assertEqual(summary_a["line_25"], Decimal("153.00"))
        self.assertEqual(summary_a["line_26"], Decimal("44.00"))
        self.assertEqual(summary_a["line_27"], Decimal("31.00"))
        self.assertEqual(summary_a["line_28a"], Decimal("101.50"))
        self.assertEqual(summary_a["line_28b"], Decimal("201.50"))
        self.assertEqual(summary_a["line_28c"], Decimal("301.50"))
        self.assertEqual(
            summary_a["line_28d"],
            Decimal(101.50)  # line_28a
            + Decimal(201.50)  # line_28b
            + Decimal(301.50),  # line_28c
        )
        self.assertEqual(summary_a["line_29"], Decimal("201.50"))
        self.assertEqual(summary_a["line_30b"], Decimal("102.25"))
        self.assertEqual(summary_a["line_30c"], Decimal("102.25"))
        self.assertEqual(summary_a["line_31"], summary_a["line_7"])
        self.assertEqual(
            summary_a["line_32"],
            summary_a["line_31"]  # line_31
            - Decimal("0")  # line_21aii
            - Decimal("0"),  # line_30aii
        )
        self.assertEqual(summary_a["line_33"], summary_a["line_11d"])
        self.assertEqual(summary_a["line_34"], summary_a["line_28d"])
        self.assertEqual(
            summary_a["line_35"], summary_a["line_33"] - summary_a["line_34"]
        )
        self.assertEqual(summary_a["line_36"], Decimal("150.00"))
        self.assertEqual(summary_a["line_37"], Decimal("2125.79"))
        self.assertEqual(
            summary_a["line_38"],
            Decimal("150.00") - Decimal("2125.79"),  # line_36  # line_37
        )

        self.assertEqual(
            summary_a["line_7"],
            Decimal("150.00")  # line_21c
            + Decimal("22.00")  # line_22
            + Decimal("14.00")  # line_23
            + Decimal("151.00")  # line_24
            + Decimal("153.00")  # line_25
            + Decimal("44.00")  # line_26
            + Decimal("31.00")  # line_27
            + Decimal(101.50 + 201.50 + 301.50)  # line_28d
            + Decimal("201.50")  # line_29
            + Decimal("102.25"),  # line_30c
        )

    def test_calculate_summary_column_b(self):
        create_cash_on_hand_yearly(
            committee_account=self.committee,
            year="2005",
            cash_on_hand=61,
        )
        f3x = create_form3x(
            self.committee,
            datetime.strptime("2005-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2005-02-28", "%Y-%m-%d").date(),
            report_code="12C",
        )
        self.debt = generate_data(
            self.committee, self.contact_1, f3x, ["a", "b", "c", "d", "e"]
        )
        summary_service = SummaryService(f3x)
        _, summary_b = summary_service.calculate_summary_columns()

        self.assertIsNotNone(self.debt)
        if self.debt is not None:
            self.assertEqual(self.debt.force_itemized, False)

        self.assertEqual(summary_b["line_6a"], Decimal("61"))
        self.assertEqual(summary_b["line_6c"], Decimal("18985.17"))
        self.assertEqual(
            summary_b["line_6d"],
            Decimal("61") + Decimal("18985.17"),  # line_6a  # line_6c
        )
        self.assertEqual(
            summary_b["line_7"],
            Decimal("250.00")  # line_21c
            + Decimal("122.00")  # line_22
            + Decimal("64.00")  # line_23
            + Decimal("296.00")  # line_24
            + Decimal("0")  # line_25
            + Decimal("61.00")  # line_26
            + Decimal("41.00")  # line_27
            + Decimal(1101.50 + 2201.50 + 3301.50)  # line_28d
            + Decimal("1201.50")  # line_29
            + Decimal("1102.25"),  # line_30c
        )
        self.assertEqual(summary_b["line_8"], summary_b["line_6d"] - summary_b["line_7"])
        self.assertEqual(summary_b["line_11ai"], Decimal("10000.23"))
        self.assertEqual(summary_b["line_11aii"], Decimal("103.77"))
        self.assertEqual(summary_b["line_11aiii"], Decimal("10104.00"))
        self.assertEqual(summary_b["line_11b"], Decimal("544.44"))
        self.assertEqual(summary_b["line_11c"], Decimal("655.55"))
        self.assertEqual(
            summary_b["line_11d"],
            Decimal("10104.00")  # line_11aiii
            + Decimal("544.44")  # line_11b
            + Decimal("655.55"),  # line_11c
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
        self.assertEqual(summary_b["line_24"], Decimal("296.00"))
        self.assertEqual(summary_b["line_26"], Decimal("61.00"))
        self.assertEqual(summary_b["line_27"], Decimal("41.00"))
        self.assertEqual(summary_b["line_28a"], Decimal("1101.50"))
        self.assertEqual(summary_b["line_28b"], Decimal("2201.50"))
        self.assertEqual(summary_b["line_28c"], Decimal("3301.50"))
        self.assertEqual(
            summary_b["line_28d"],
            Decimal("1101.50")  # line_28a
            + Decimal("2201.50")  # line_28b
            + Decimal("3301.50"),  # line_28c
        )
        self.assertEqual(summary_b["line_29"], Decimal("1201.50"))
        self.assertEqual(summary_b["line_30b"], Decimal("1102.25"))
        self.assertEqual(summary_b["line_30c"], Decimal("1102.25"))
        self.assertEqual(summary_b["line_31"], summary_b["line_7"])
        self.assertEqual(
            summary_b["line_32"],
            summary_b["line_31"]  # line_31
            - Decimal("0")  # line_21aii
            - Decimal("0"),  # line_30aii
        )
        self.assertEqual(summary_b["line_33"], summary_b["line_11d"])
        self.assertEqual(summary_b["line_34"], summary_b["line_28d"])
        self.assertEqual(
            summary_b["line_35"],
            summary_b["line_33"] - summary_b["line_34"],
        )
        self.assertEqual(summary_b["line_36"], Decimal("250.00"))
        self.assertEqual(summary_b["line_37"], Decimal("2225.79"))
        self.assertEqual(
            summary_b["line_38"],
            Decimal("250.00") - Decimal("2225.79"),  # line_36  # line_37
        )

    def test_report_with_no_transactions(self):
        f3x = create_form3x(
            self.committee,
            datetime.strptime("2024-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2024-02-01", "%Y-%m-%d").date(),
        )
        summary_service = SummaryService(f3x)
        summary_a, _ = summary_service.calculate_summary_columns()
        self.assertEqual(summary_a["line_15"], Decimal("0"))
        self.assertEqual(summary_a["line_17"], Decimal("0"))

    def test_report_with_zero_cash_on_hand(self):
        f3x = create_form3x(
            self.committee,
            datetime.strptime("2024-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2024-02-01", "%Y-%m-%d").date(),
        )
        summary_service = SummaryService(f3x)
        summary_a, _ = summary_service.calculate_summary_columns()
        self.assertTrue("line_8" in summary_a)
