from datetime import datetime
from decimal import Decimal
from django.test import TestCase
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.tests.utils import create_test_individual_contact
from fecfiler.election_cycles.models import ElectionCycle
from fecfiler.reports.form_3.summary import (
    calculate_summary,
    calculate_summary_columns,
)
from fecfiler.reports.tests.utils import create_form3
from fecfiler.transactions.tests.utils import create_schedule_a, create_schedule_b


class F3ReportSummaryTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )
        self.election_cycle = ElectionCycle.objects.create(
            committee_account=self.committee,
            office=ElectionCycle.Office.HOUSE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2026",
            start_date=datetime.strptime("2024-11-06", "%Y-%m-%d").date(),
            end_date=datetime.strptime("2026-11-03", "%Y-%m-%d").date(),
        )

    def _create_f3_reports_and_transactions(self):
        prior_report = create_form3(
            self.committee,
            datetime.strptime("2025-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2025-03-31", "%Y-%m-%d").date(),
            data={"election_cycle": self.election_cycle},
            report_code="Q1",
        )
        current_report = create_form3(
            self.committee,
            datetime.strptime("2026-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2026-03-31", "%Y-%m-%d").date(),
            data={"election_cycle": self.election_cycle},
            report_code="Q1",
        )
        future_report = create_form3(
            self.committee,
            datetime.strptime("2026-04-01", "%Y-%m-%d").date(),
            datetime.strptime("2026-06-30", "%Y-%m-%d").date(),
            data={"election_cycle": self.election_cycle},
            report_code="Q2",
        )

        # Current report period SA14 transactions (non-memo)
        create_schedule_a(
            "OFFSET_TO_OPERATING_EXPENDITURES",
            self.committee,
            self.contact_1,
            "2026-02-01",
            "1234.56",
            "GENERAL",
            memo_code=False,
            itemized=False,
            report=current_report,
        )
        create_schedule_a(
            "OFFSET_TO_OPERATING_EXPENDITURES",
            self.committee,
            self.contact_1,
            "2026-02-15",
            "891.23",
            "GENERAL",
            memo_code=False,
            itemized=True,
            report=current_report,
        )
        # Current report period SA14 transaction with Memo Code checked (excluded)
        create_schedule_a(
            "OFFSET_TO_OPERATING_EXPENDITURES",
            self.committee,
            self.contact_1,
            "2026-02-10",
            "10000.23",
            "GENERAL",
            memo_code=True,
            itemized=False,
            report=current_report,
        )
        # Current report period non-SA14/SA15 transaction (excluded from Lines 14 & 15)
        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2026-02-01",
            "500.00",
            "GENERAL",
            memo_code=False,
            itemized=True,
            report=current_report,
        )

        # Current report period SA15 transactions (non-memo)
        create_schedule_a(
            "OTHER_RECEIPT",
            self.committee,
            self.contact_1,
            "2026-02-01",
            "200.50",
            "GENERAL",
            memo_code=False,
            itemized=False,
            report=current_report,
        )
        create_schedule_a(
            "INDIVIDUAL_RECOUNT_RECEIPT",
            self.committee,
            self.contact_1,
            "2026-02-15",
            "800.50",
            "GENERAL",
            memo_code=False,
            itemized=True,
            report=current_report,
        )
        # Current report period SA15 transaction with Memo Code checked (excluded)
        create_schedule_a(
            "OTHER_RECEIPT",
            self.committee,
            self.contact_1,
            "2026-02-10",
            "5000.00",
            "GENERAL",
            memo_code=True,
            itemized=False,
            report=current_report,
        )

        # Current report period SB17 transactions (non-memo)
        create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2026-02-01",
            "450.25",
            "GENERAL",
            memo_code=False,
            report=current_report,
        )
        create_schedule_b(
            "IN_KIND_OUT",
            self.committee,
            self.contact_1,
            "2026-02-15",
            "149.75",
            "GENERAL",
            memo_code=False,
            report=current_report,
        )
        # Current report period SB17 transaction with Memo Code checked (excluded)
        create_schedule_b(
            "OPERATING_EXPENDITURE_CREDIT_CARD_PAYMENT_MEMO",
            self.committee,
            self.contact_1,
            "2026-02-10",
            "3000.00",
            "GENERAL",
            memo_code=True,
            report=current_report,
        )
        # Current report period non-SB17 Schedule B transaction (excluded from Line 17)
        create_schedule_b(
            "OTHER_DISBURSEMENT",
            self.committee,
            self.contact_1,
            "2026-02-01",
            "200.00",
            "GENERAL",
            memo_code=False,
            report=current_report,
        )

        # Earlier in election cycle (prior year, within election cycle)
        create_schedule_a(
            "OFFSET_TO_OPERATING_EXPENDITURES",
            self.committee,
            self.contact_1,
            "2025-02-01",
            "100.00",
            "GENERAL",
            memo_code=False,
            itemized=True,
            report=prior_report,
        )
        create_schedule_a(
            "PARTY_RECOUNT_RECEIPT",
            self.committee,
            self.contact_1,
            "2025-02-01",
            "150.00",
            "GENERAL",
            memo_code=False,
            itemized=True,
            report=prior_report,
        )
        create_schedule_b(
            "OPERATING_EXPENDITURE_STAFF_REIMBURSEMENT",
            self.committee,
            self.contact_1,
            "2025-02-01",
            "125.50",
            "GENERAL",
            memo_code=False,
            report=prior_report,
        )
        # Earlier in election cycle with Memo Code checked (excluded)
        create_schedule_a(
            "OFFSET_TO_OPERATING_EXPENDITURES",
            self.committee,
            self.contact_1,
            "2025-02-15",
            "250.00",
            "GENERAL",
            memo_code=True,
            itemized=True,
            report=prior_report,
        )
        create_schedule_a(
            "PAC_RECOUNT_RECEIPT",
            self.committee,
            self.contact_1,
            "2025-02-15",
            "400.00",
            "GENERAL",
            memo_code=True,
            itemized=True,
            report=prior_report,
        )
        create_schedule_b(
            "OPERATING_EXPENDITURE_STAFF_REIMBURSEMENT_MEMO",
            self.committee,
            self.contact_1,
            "2025-02-15",
            "500.00",
            "GENERAL",
            memo_code=True,
            report=prior_report,
        )
        # Before election cycle start date (excluded from Column B)
        create_schedule_a(
            "OFFSET_TO_OPERATING_EXPENDITURES",
            self.committee,
            self.contact_1,
            "2024-11-05",
            "300.00",
            "GENERAL",
            memo_code=False,
            itemized=True,
            report=prior_report,
        )
        create_schedule_a(
            "OTHER_RECEIPT",
            self.committee,
            self.contact_1,
            "2024-11-05",
            "350.00",
            "GENERAL",
            memo_code=False,
            itemized=True,
            report=prior_report,
        )
        create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2024-11-05",
            "275.00",
            "GENERAL",
            memo_code=False,
            report=prior_report,
        )
        # After report coverage period end date (excluded from Column B)
        create_schedule_a(
            "OFFSET_TO_OPERATING_EXPENDITURES",
            self.committee,
            self.contact_1,
            "2026-04-01",
            "500.00",
            "GENERAL",
            memo_code=False,
            itemized=True,
            report=future_report,
        )
        create_schedule_a(
            "INDIVIDUAL_RECOUNT_RECEIPT",
            self.committee,
            self.contact_1,
            "2026-04-01",
            "600.00",
            "GENERAL",
            memo_code=False,
            itemized=True,
            report=future_report,
        )
        create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.contact_1,
            "2026-04-01",
            "800.00",
            "GENERAL",
            memo_code=False,
            report=future_report,
        )

        return current_report

    def test_calculate_summary_column_a(self):
        f3 = self._create_f3_reports_and_transactions()
        summary_a, _ = calculate_summary_columns(f3)

        self.assertEqual(summary_a["line_14"], Decimal("2125.79"))
        self.assertEqual(summary_a["line_7b"], Decimal("2125.79"))
        self.assertEqual(summary_a["line_15"], Decimal("1001.00"))
        self.assertEqual(summary_a["line_17"], Decimal("600.00"))
        self.assertEqual(summary_a["line_7a"], Decimal("600.00"))

    def test_calculate_summary_column_b(self):
        f3 = self._create_f3_reports_and_transactions()
        _, summary_b = calculate_summary_columns(f3)

        self.assertEqual(summary_b["line_14"], Decimal("2225.79"))
        self.assertEqual(summary_b["line_7b"], Decimal("2225.79"))
        self.assertEqual(summary_b["line_15"], Decimal("1151.00"))
        self.assertEqual(summary_b["line_17"], Decimal("725.50"))
        self.assertEqual(summary_b["line_7a"], Decimal("725.50"))

    def test_calculate_summary_saves_form_3_fields(self):
        f3 = self._create_f3_reports_and_transactions()
        calculate_summary(f3)
        f3.refresh_from_db()

        self.assertEqual(
            f3.form_3.L14_offsets_to_operating_expenditures_period,
            Decimal("2125.79"),
        )
        self.assertEqual(
            f3.form_3.L7b_total_offsets_to_operating_expenditures_period,
            Decimal("2125.79"),
        )
        self.assertEqual(
            f3.form_3.L14_offsets_to_operating_expenditures_ytd,
            Decimal("2225.79"),
        )
        self.assertEqual(
            f3.form_3.L7b_total_offsets_to_operating_expenditures_ytd,
            Decimal("2225.79"),
        )
        self.assertEqual(
            f3.form_3.L15_other_receipts_period,
            Decimal("1001.00"),
        )
        self.assertEqual(
            f3.form_3.L15_other_receipts_ytd,
            Decimal("1151.00"),
        )
        self.assertEqual(
            f3.form_3.L17_operating_expenditures_period,
            Decimal("600.00"),
        )
        self.assertEqual(
            f3.form_3.L7a_total_operating_expenditures_period,
            Decimal("600.00"),
        )
        self.assertEqual(
            f3.form_3.L17_operating_expenditures_ytd,
            Decimal("725.50"),
        )
        self.assertEqual(
            f3.form_3.L7a_total_operating_expenditures_ytd,
            Decimal("725.50"),
        )

    def test_report_with_no_transactions(self):
        f3 = create_form3(
            self.committee,
            datetime.strptime("2026-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2026-03-31", "%Y-%m-%d").date(),
            data={"election_cycle": self.election_cycle},
        )
        summary_a, summary_b = calculate_summary_columns(f3)

        self.assertEqual(summary_a["line_14"], Decimal("0"))
        self.assertEqual(summary_a["line_7b"], Decimal("0"))
        self.assertEqual(summary_a["line_15"], Decimal("0"))
        self.assertEqual(summary_a["line_17"], Decimal("0"))
        self.assertEqual(summary_a["line_7a"], Decimal("0"))
        self.assertEqual(summary_b["line_14"], Decimal("0"))
        self.assertEqual(summary_b["line_7b"], Decimal("0"))
        self.assertEqual(summary_b["line_15"], Decimal("0"))
        self.assertEqual(summary_b["line_17"], Decimal("0"))
        self.assertEqual(summary_b["line_7a"], Decimal("0"))
