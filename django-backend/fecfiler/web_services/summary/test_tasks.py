from datetime import datetime
from decimal import Decimal
from django.test import TestCase
from .tasks import CalculationState, calculate_summary
from fecfiler.reports.models import Report
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.contacts.tests.utils import create_test_individual_contact
from fecfiler.transactions.tests.utils import create_schedule_a
from .tests.utils import generate_data
from fecfiler.cash_on_hand.tests.utils import create_cash_on_hand_yearly


class F3XSerializerTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )
        self.q1_report = create_form3x(
            self.committee,
            datetime.strptime("2005-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2005-02-28", "%Y-%m-%d").date(),
            {"L6a_cash_on_hand_jan_1_ytd": 61},
        )
        self.q2_report = create_form3x(
            self.committee,
            datetime.strptime("2005-03-01", "%Y-%m-%d").date(),
            datetime.strptime("2005-05-01", "%Y-%m-%d").date(),
            {},
            "Q2",
        )
        self.q3_report = create_form3x(
            self.committee,
            datetime.strptime("2005-09-01", "%Y-%m-%d").date(),
            datetime.strptime("2005-10-01", "%Y-%m-%d").date(),
            {},
            "Q3",
        )
        create_cash_on_hand_yearly(
            committee_account=self.committee,
            year="2005",
            cash_on_hand=61,
        )

    def test_summary_task(self):
        generate_data(self.committee, self.contact_1, self.q1_report, ["a"])
        report_id = calculate_summary("not_an_existing_report")
        self.assertIsNone(report_id)

        report_id = calculate_summary(self.q1_report.id)
        report = Report.objects.get(id=report_id)
        self.assertEqual(
            report.form_3x.L15_offsets_to_operating_expenditures_refunds_period,
            Decimal("2125.79"),
        )
        self.assertEqual(
            report.form_3x.L37_offsets_to_operating_expenditures_period,
            Decimal("2125.79"),
        )
        self.assertEqual(report.calculation_status, CalculationState.SUCCEEDED.value)

    def test_report_with_no_transactions(self):
        report_id = calculate_summary(self.q2_report.id)
        report = Report.objects.get(id=report_id)
        self.assertEqual(
            report.form_3x.L15_offsets_to_operating_expenditures_refunds_period,
            Decimal("0"),
        )
        self.assertEqual(
            report.form_3x.L37_offsets_to_operating_expenditures_period, Decimal("0")
        )
        self.assertEqual(report.calculation_status, CalculationState.SUCCEEDED.value)

    def test_report_group_recalculation(self):
        generate_data(self.committee, self.contact_1, self.q1_report, ["a"])
        previous_report = self.q1_report
        previous_report.calculation_status = None
        previous_report.save()

        self.q2_report.calculation_status = None
        self.q2_report.save()

        calculate_summary(self.q2_report.id)
        calculated_report = Report.objects.get(id=self.q2_report.id)
        calculated_prev_report = Report.objects.get(id=self.q1_report.id)

        self.assertEqual(
            calculated_report.form_3x.L6b_cash_on_hand_beginning_period,
            Decimal("18146.17"),
        )
        self.assertEqual(
            calculated_report.form_3x.L6a_cash_on_hand_jan_1_ytd, Decimal("61.00")
        )
        self.assertEqual(
            calculated_prev_report.form_3x.L15_offsets_to_operating_expenditures_refunds_period,  # noqa: E501
            Decimal("2125.79"),
        )

    def test_report_group_recalculation_year_to_year(self):
        next_year_report = create_form3x(
            self.committee,
            datetime.strptime("2006-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2006-03-31", "%Y-%m-%d").date(),
            report_code="Q1",
        )

        self.q1_report.calculation_status = None
        self.q1_report.save()
        self.q2_report.calculation_status = None
        self.q2_report.save()

        transaction_data = [
            {
                "date": "2005-02-01",
                "amount": "10000.23",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
                "report": self.q1_report,
            },
            {
                "date": "2005-05-01",
                "amount": "2000.05",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
                "report": self.q2_report,
            },
            {
                "date": "2005-07-01",
                "amount": "500.25",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
                "report": self.q3_report,
            },
            {
                "date": "2006-02-01",
                "amount": "100.00",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
                "report": next_year_report,
            },
        ]
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
            scha.reports.add(data["report"])
            scha.save()

        calculate_summary(next_year_report.id)
        next_year_report.refresh_from_db()
        self.q2_report.refresh_from_db()
        self.q3_report.refresh_from_db()

        self.assertEqual(
            self.q2_report.form_3x.L8_cash_on_hand_close_ytd,
            Decimal("12061.28"),
        )
        self.assertEqual(
            self.q3_report.form_3x.L8_cash_on_hand_close_ytd,
            Decimal("12561.53"),
        )
        self.assertEqual(
            next_year_report.form_3x.L6b_cash_on_hand_beginning_period,
            Decimal("12561.53"),
        )
        self.assertEqual(
            next_year_report.form_3x.L6a_cash_on_hand_jan_1_ytd, Decimal("12561.53")
        )
        self.assertEqual(
            next_year_report.form_3x.L8_cash_on_hand_at_close_period,  # noqa: E501
            Decimal("12661.53"),
        )

    def test_only_update_committees_reports(self):
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        other_committees_f3x = create_form3x(
            other_committee,
            datetime.strptime("2024-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2024-02-01", "%Y-%m-%d").date(),
        )
        f3x = create_form3x(
            self.committee,
            datetime.strptime("2024-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2024-02-01", "%Y-%m-%d").date(),
        )
        other_f3x = create_form3x(
            self.committee,
            datetime.strptime("2023-01-01", "%Y-%m-%d").date(),
            datetime.strptime("2023-02-01", "%Y-%m-%d").date(),
        )
        calculate_summary(f3x.id)
        f3x.refresh_from_db()
        other_committees_f3x.refresh_from_db()
        other_f3x.refresh_from_db()
        self.assertIsNone(other_committees_f3x.calculation_status)
        self.assertEqual(f3x.calculation_status, CalculationState.SUCCEEDED.value)
        self.assertEqual(other_f3x.calculation_status, CalculationState.SUCCEEDED.value)

    def test_cash_on_hand_carries_over_gap_years(self):
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        create_cash_on_hand_yearly(
            committee_account=other_committee,
            year="2005",
            cash_on_hand=4010,
        )
        first_report = create_form3x(
            other_committee,
            datetime.strptime("2005-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2005-02-28", "%Y-%m-%d").date(),
            report_code="12C",
        )
        first_report.save()

        years_later_report = create_form3x(
            other_committee,
            datetime.strptime("2010-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2010-02-28", "%Y-%m-%d").date(),
            report_code="Q1",
        )
        years_later_report.save()

        calculate_summary(years_later_report.id)
        first_report.refresh_from_db()
        years_later_report.refresh_from_db()

        self.assertEqual(first_report.form_3x.L8_cash_on_hand_close_ytd, 4010)
        self.assertEqual(years_later_report.form_3x.L6a_cash_on_hand_jan_1_ytd, 4010)

    def test_cash_on_hand_override_between_reports(self):
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        create_cash_on_hand_yearly(
            committee_account=other_committee,
            year="2007",
            cash_on_hand=4010,
        )
        first_report = create_form3x(
            other_committee,
            datetime.strptime("2005-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2005-02-28", "%Y-%m-%d").date(),
            report_code="12C",
        )
        first_report.save()

        transaction_data = [
            {
                "date": "2005-02-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
                "report": first_report,
            },
            {
                "date": "2005-02-02",
                "amount": "200",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
                "report": first_report,
            },
        ]
        for data in transaction_data:
            scha = create_schedule_a(
                data["tti"],
                other_committee,
                self.contact_1,
                data["date"],
                data["amount"],
                data["group"],
                data["form_type"],
                data["memo"],
                data["itemized"],
            )
            scha.reports.add(data["report"])
            scha.save()

        years_later_report = create_form3x(
            other_committee,
            datetime.strptime("2010-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2010-02-28", "%Y-%m-%d").date(),
            report_code="Q1",
        )
        years_later_report.save()

        calculate_summary(years_later_report.id)
        first_report.refresh_from_db()
        years_later_report.refresh_from_db()

        self.assertEqual(first_report.form_3x.L8_cash_on_hand_close_ytd, 300)
        self.assertEqual(years_later_report.form_3x.L6a_cash_on_hand_jan_1_ytd, 4010)

    def test_cash_on_hand_override_for_last_year(self):
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        create_cash_on_hand_yearly(
            committee_account=other_committee,
            year="2005",
            cash_on_hand=4010,
        )
        first_report = create_form3x(
            other_committee,
            datetime.strptime("2005-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2005-02-28", "%Y-%m-%d").date(),
            report_code="12C",
        )
        first_report.save()

        schedule_a = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            other_committee,
            self.contact_1,
            "2005-02-01",
            "100",
            "GENERAL",
            "SA11AI",
            False,
            True,
        )
        schedule_a.reports.add(first_report)
        schedule_a.save()

        next_year_report = create_form3x(
            other_committee,
            datetime.strptime("2006-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2006-02-28", "%Y-%m-%d").date(),
            report_code="Q1",
        )

        calculate_summary(next_year_report.id)
        first_report.refresh_from_db()
        next_year_report.refresh_from_db()

        self.assertEqual(first_report.form_3x.L8_cash_on_hand_close_ytd, 4110)
        # Cash on hand should be the L8 of the previous year's final
        # report and not the override for the previous year
        self.assertEqual(next_year_report.form_3x.L6a_cash_on_hand_jan_1_ytd, 4110)

    def test_cash_on_hand_override_for_last_year_with_no_prior_report(self):
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        # confirm order of override years
        create_cash_on_hand_yearly(
            committee_account=other_committee,
            year="2004",
            cash_on_hand=2004,
        )
        create_cash_on_hand_yearly(
            committee_account=other_committee,
            year="2005",
            cash_on_hand=2005,
        )
        report = create_form3x(
            other_committee,
            datetime.strptime("2006-01-30", "%Y-%m-%d").date(),
            datetime.strptime("2006-02-28", "%Y-%m-%d").date(),
            report_code="12C",
        )

        calculate_summary(report.id)
        report.refresh_from_db()

        self.assertEqual(report.form_3x.L8_cash_on_hand_close_ytd, 2005)
