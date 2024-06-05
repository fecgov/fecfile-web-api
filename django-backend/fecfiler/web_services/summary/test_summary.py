from decimal import Decimal
from django.test import TestCase
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.views import create_committee_view
from .summary import SummaryService
from fecfiler.reports.tests.utils import create_form3x
from datetime import datetime
from fecfiler.transactions.tests.utils import (
    create_ie,
    create_schedule_b,
    create_schedule_a,
    create_loan,
    create_debt,
)
from fecfiler.contacts.tests.utils import create_test_individual_contact


class F3XReportTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )

    def test_calculate_summary_column_a(self):
        self.generate_data()
        summary_service = SummaryService(self.f3x)
        summary_a, _ = summary_service.calculate_summary()

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
            + Decimal("0")  # line_25
            + Decimal("44.00")  # line_26
            + Decimal("31.00")  # line_27
            + Decimal(101.50 + 201.50 + 301.50)  # line_28d
            + Decimal("201.50")  # line_29
            + Decimal("102.25"),  # line_30c
        )

    def test_calculate_summary_column_b(self):
        self.generate_data()
        summary_service = SummaryService(self.f3x)
        _, summary_b = summary_service.calculate_summary()

        self.assertEqual(self.debt.force_itemized, False)

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
            {},
        )
        summary_service = SummaryService(f3x)
        summary_a, _ = summary_service.calculate_summary()
        self.assertEqual(summary_a["line_15"], Decimal("0"))
        self.assertEqual(summary_a["line_17"], Decimal("0"))

    def test_report_with_zero_cash_on_hand(self):
        f3x = create_form3x(
            self.committee,
            datetime.strptime("2024-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2024-02-01", "%Y-%m-%d").date(),
            {"L6a_cash_on_hand_jan_1_ytd": 0},
        )
        summary_service = SummaryService(f3x)
        summary_a, _ = summary_service.calculate_summary()
        self.assertTrue("line_8" in summary_a)

    def test_report_with_none_cash_on_hand(self):
        f3x = create_form3x(
            self.committee,
            datetime.strptime("2024-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2024-02-01", "%Y-%m-%d").date(),
            {"L6a_cash_on_hand_jan_1_ytd": None},
        )
        summary_service = SummaryService(f3x)
        summary_a, _ = summary_service.calculate_summary()
        self.assertFalse("line_8" in summary_a)

    def generate_data(self):
        self.f3x = create_form3x(
            self.committee,
            datetime.strptime("2005-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2005-02-28", "%Y-%m-%d").date(),
            {"L6a_cash_on_hand_jan_1_ytd": 61},
            "12C",
        )

        sch_a_transactions = [
            {
                "date": "2005-02-01",
                "amount": "10000.23",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-02-08",
                "amount": "3.77",
                "group": "GENERAL",
                "form_type": "SA11AII",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "444.44",
                "group": "GENERAL",
                "form_type": "SA11B",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "555.55",
                "group": "OTHER",
                "form_type": "SA11C",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1212.12",
                "group": "GENERAL",
                "form_type": "SA12",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1313.13",
                "group": "GENERAL",
                "form_type": "SA13",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1414.14",
                "group": "GENERAL",
                "form_type": "SA14",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1234.56",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "OFFSET_TO_OPEX",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "891.23",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "OFFSET_TO_OPEX",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "10000.23",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "OFFSET_TO_OPEX",
                "memo": True,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "16",
                "group": "GENERAL",
                "form_type": "SA16",
                "tti": "REFUND_TO_FEDERAL_CANDIDATE",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "200.50",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "-1",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "800.50",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
        ]

        self.gen_schedule_a(sch_a_transactions, self.f3x)

        sch_b_transactions = [
            {
                "amount": 150,
                "date": "2005-02-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB21B",
            },
            {
                "amount": 22,
                "date": "2005-02-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB22",
            },
            {
                "amount": 14,
                "date": "2005-02-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB23",
            },
            {
                "amount": 44,
                "date": "2005-02-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB26",
            },
            {
                "amount": 31,
                "date": "2005-02-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB27",
            },
            {
                "amount": 101.50,
                "date": "2005-02-01",
                "type": "REFUND_INDIVIDUAL_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28A",
            },
            {
                "amount": 201.50,
                "date": "2005-02-01",
                "type": "REFUND_PARTY_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28B",
            },
            {
                "amount": 301.50,
                "date": "2005-02-01",
                "type": "REFUND_PAC_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28C",
            },
            {
                "amount": 201.50,
                "date": "2005-02-01",
                "type": "REFUND_PAC_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB29",
            },
            {
                "amount": 102.25,
                "date": "2005-02-01",
                "type": "FEDERAL_ELECTION_ACTIVITY_100PCT_PAYMENT",
                "group": "GENERAL",
                "form_type": "SB30B",
            },
        ]
        self.gen_schedule_b(sch_b_transactions, self.f3x)

        sch_c_transactions = [
            {
                "amount": 150,
                "date": "2005-02-01",
                "percent": "2.0",
                "form_type": "SC/9",
            },
            {
                "amount": 30,
                "date": "2005-02-01",
                "percent": "2.0",
                "form_type": "SC/10",
            },
        ]
        self.gen_schedule_c(sch_c_transactions, self.f3x)

        sch_d_transactions = [
            {
                "amount": 100,
                "date": "2005-02-01",
                "form_type": "SD9",
            },
            {
                "amount": 220,
                "date": "2005-02-01",
                "form_type": "SD10",
            },
        ]
        self.gen_schedule_d(sch_d_transactions, self.f3x)

        sch_e_transactions = [
            {
                "amount": 65,
                "disbursement_date": "2005-01-30",
                "dissemination_date": "2005-01-30",
                "memo_code": False,
            },
            {
                "amount": 76,
                "disbursement_date": "2005-01-30",
                "dissemination_date": "2005-01-30",
                "memo_code": False,
            },
            {
                "amount": 10,
                "disbursement_date": "2005-01-30",
                "dissemination_date": "2005-01-30",
                "memo_code": False,
            },
            {
                "amount": 57,
                "disbursement_date": "2005-01-30",
                "dissemination_date": "2005-01-30",
                "memo_code": True,
            },
        ]
        self.gen_schedule_e(sch_e_transactions, self.f3x)

        other_f3x = create_form3x(
            self.committee,
            datetime.strptime("2007-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2007-02-28", "%Y-%m-%d").date(),
            {"L6a_cash_on_hand_jan_1_ytd": 61},
        )

        sch_a_transactions = [
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2022-03-01",
                "amount": "8.23",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA11B",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA11B",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA11C",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA11C",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA12",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA12",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA13",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA13",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA14",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA14",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA16",
                "tti": "REFUND_TO_FEDERAL_CANDIDATE",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-05-01",
                "amount": "1000.00",
                "group": "GENERAL",
                "form_type": "SA16",
                "tti": "REFUND_TO_FEDERAL_CANDIDATE",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "300.00",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": True,
                "itemized": True,
            },
        ]
        sch_b_transactions = [
            {
                "amount": 100,
                "date": "2005-01-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB21B",
            },
            {
                "amount": 100,
                "date": "2004-12-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB21B",
            },
            {
                "amount": 100,
                "date": "2005-01-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB22",
            },
            {
                "amount": 1000,
                "date": "2005-05-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB22",
            },
            {
                "amount": 50,
                "date": "2005-01-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB23",
            },
            {
                "amount": 1000,
                "date": "2005-05-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB23",
            },
            {
                "amount": 17,
                "date": "2005-01-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB26",
            },
            {
                "amount": 1000,
                "date": "2005-05-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB26",
            },
            {
                "amount": 10,
                "date": "2005-01-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB27",
            },
            {
                "amount": 100,
                "date": "2005-05-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB27",
            },
            {
                "amount": 1000.00,
                "date": "2005-01-01",
                "type": "REFUND_INDIVIDUAL_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28A",
            },
            {
                "amount": 500,
                "date": "2005-03-01",
                "type": "REFUND_INDIVIDUAL_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28A",
            },
            {
                "amount": 2000.00,
                "date": "2005-01-01",
                "type": "REFUND_PARTY_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28B",
            },
            {
                "amount": 500,
                "date": "2005-03-01",
                "type": "REFUND_PARTY_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28B",
            },
            {
                "amount": 3000.00,
                "date": "2005-01-01",
                "type": "REFUND_PAC_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28C",
            },
            {
                "amount": 500,
                "date": "2005-03-01",
                "type": "REFUND_PAC_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28C",
            },
            {
                "amount": 1000.00,
                "date": "2005-01-01",
                "type": "OTHER_DISBURSEMENT",
                "group": "GENERAL",
                "form_type": "SB29",
            },
            {
                "amount": 500,
                "date": "2005-03-01",
                "type": "OTHER_DISBURSEMENT",
                "group": "GENERAL",
                "form_type": "SB29",
            },
            {
                "amount": 600.00,
                "date": "2005-03-01",
                "type": "FEDERAL_ELECTION_ACTIVITY_100PCT_PAYMENT",
                "group": "GENERAL",
                "form_type": "SB30B",
            },
            {
                "amount": 1000.00,
                "date": "2005-01-01",
                "type": "FEDERAL_ELECTION_ACTIVITY_100PCT_PAYMENT",
                "group": "GENERAL",
                "form_type": "SB30B",
            },
        ]
        sch_c_transactions = [
            {
                "amount": 100,
                "date": "2005-01-01",
                "percent": "2.0",
                "form_type": "SC/9",
            },
            {
                "amount": 100,
                "date": "2004-12-01",
                "percent": "2.0",
                "form_type": "SC/9",
            },
            {
                "amount": 100,
                "date": "2005-01-01",
                "percent": "2.0",
                "form_type": "SC/10",
            },
            {
                "amount": 100,
                "date": "2004-12-01",
                "percent": "2.0",
                "form_type": "SC/10",
            },
        ]
        sch_d_transactions = [
            {
                "amount": 100,
                "date": "2005-01-01",
                "form_type": "SD9",
            },
            {
                "amount": 100,
                "date": "2004-01-01",
                "form_type": "SD9",
            },
            {
                "amount": 220,
                "date": "2005-02-01",
                "form_type": "SD10",
            },
            {
                "amount": 220,
                "date": "2009-02-01",
                "form_type": "SD10",
            },
        ]
        sch_e_transactions = [
            {
                "amount": 145,
                "disbursement_date": "2005-01-01",
                "dissemination_date": "2005-01-01",
                "memo_code": False,
            },
            {
                "amount": 77,
                "disbursement_date": "1969-08-01",
                "dissemination_date": "1969-08-01",
                "memo_code": False,
            },
        ]

        self.gen_schedule_a(sch_a_transactions, other_f3x)
        self.gen_schedule_b(sch_b_transactions, other_f3x)
        self.gen_schedule_c(sch_c_transactions, other_f3x)
        self.gen_schedule_d(sch_d_transactions, other_f3x)
        self.gen_schedule_e(sch_e_transactions, other_f3x)

    def gen_schedule_a(self, transaction_data, f3x):
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
            scha.reports.add(f3x)
            scha.save()
            if data["form_type"] == "SA11AII":
                self.debt = scha

    def gen_schedule_b(self, transaction_data, f3x):
        for data in transaction_data:
            schb = create_schedule_b(
                data["type"],
                self.committee,
                self.contact_1,
                data["date"],
                data["amount"],
                data["group"],
                data["form_type"],
            )

            schb.reports.add(f3x)
            schb.save()

    def gen_schedule_c(self, transaction_data, f3x):
        for data in transaction_data:
            schc = create_loan(
                self.committee,
                self.contact_1,
                data["amount"],
                data["date"],
                data["percent"],
                False,
                "LOAN_RECEIVED_FROM_INDIVIDUAL",
                data["form_type"],
            )
            schc.reports.add(f3x)

    def gen_schedule_d(self, transaction_data, f3x):
        for data in transaction_data:
            schd = create_debt(
                self.committee,
                self.contact_1,
                data["amount"],
                data["form_type"],
            )
            schd.reports.add(f3x)

    def gen_schedule_e(self, transaction_data, f3x):
        for data in transaction_data:
            sche = create_ie(
                self.committee,
                self.contact_1,
                data["disbursement_date"],
                data["dissemination_date"],
                data["amount"],
                None,
                None,
                data["memo_code"],
            )
            sche.reports.add(f3x)
