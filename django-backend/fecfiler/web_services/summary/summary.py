from decimal import Decimal
from fecfiler.transactions.models import Transaction
from fecfiler.reports.models import Report
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
import logging

logger = logging.getLogger(__name__)


class SummaryService:
    def __init__(self, report) -> None:
        self.report = report
        self.previous_report = (
            Report.objects.filter(
                ~Q(id=report.id),
                committee_account=report.committee_account,
                form_3x__isnull=False,
                coverage_through_date__lt=report.coverage_from_date,
            )
            .order_by("-coverage_through_date")
            .first()
        )

    def calculate_summary(self):
        summary_a = self.calculate_summary_column_a()
        summary_b = self.calculate_summary_column_b()



        reports_from_prior_years = Report.objects.filter(
            committee_account=self.report.committee_account,
            coverage_through_date__year__lt=self.report.coverage_from_date.year,
            form_3x__isnull=False
        ).order_by("coverage_from_date")

        if reports_from_prior_years.count() > 0:
            summary_b["line_6a"] = reports_from_prior_years.last().form_3x.L8_cash_on_hand_close_ytd  # noqa: E501
        elif self.previous_report:
                summary_b["line_6a"] = self.previous_report.form_3x.L6a_cash_on_hand_jan_1_ytd  # noqa: E501

        if self.previous_report:
            summary_a["line_6b"] = self.previous_report.form_3x.L8_cash_on_hand_at_close_period  # noqa: E501
        else:
            summary_a["line_6b"] = summary_b["line_6a"]


        return summary_a, summary_b

    def calculate_summary_column_a(self):
        report_transactions = Transaction.objects.filter(report_id=self.report.id)
        summary = report_transactions.aggregate(
            line_11ai=self.get_line("SA11AI"),
            line_11aii=self.get_line("SA11AII"),
            line_11b=self.get_line("SA11B"),
            line_11c=self.get_line("SA11C"),
            line_12=self.get_line("SA12"),
            line_13=self.get_line("SA13"),
            line_14=self.get_line("SA14"),
            line_15=self.get_line("SA15"),
            line_16=self.get_line("SA16"),
            line_17=self.get_line("SA17"),
            line_21b=self.get_line("SB21B"),
            line_22=self.get_line("SB22"),
            line_23=self.get_line("SB23"),
            line_24=self.get_line("SE"),
            line_26=self.get_line("SB26"),
            line_27=self.get_line("SB27"),
            line_28a=self.get_line("SB28A"),
            line_28b=self.get_line("SB28B"),
            line_28c=self.get_line("SB28C"),
            line_29=self.get_line("SB29"),
            line_30b=self.get_line("SB30B"),
            # Temporary aggregations
            temp_sc9=self.get_line("SC/9", field="loan_balance"),
            temp_sd9=self.get_line("SD9", field="balance_at_close"),
            temp_sc10=self.get_line("SC/10", field="loan_balance"),
            temp_sd10=self.get_line("SD10", field="balance_at_close")
        )

        summary["line_9"] = (
            summary["temp_sc9"]
            + summary["temp_sd9"]
        )
        summary["line_10"] = (
            summary["temp_sc10"]
            + summary["temp_sd10"]
        )
        summary["line_11aiii"] = (
            summary["line_11ai"]
            + summary["line_11aii"]
        )
        summary["line_11d"] = (
            summary["line_11aiii"]
            + summary["line_11b"]
            + summary["line_11c"]
        )
        summary["line_18c"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_21ai"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_21aii"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_21c"] = (
            summary["line_21ai"]
            + summary["line_21aii"]
            + summary["line_21b"]
        )
        summary["line_25"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_28d"] = (
            summary["line_28a"]
            + summary["line_28b"]
            + summary["line_28c"]
        )
        summary["line_30ai"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_30aii"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_30c"] = (
            summary["line_30ai"]
            + summary["line_30aii"]
            + summary["line_30b"]
        )
        summary["line_31"] = (
            summary["line_21c"]
            + summary["line_22"]
            + summary["line_23"]
            + summary["line_24"]
            + summary["line_25"]
            + summary["line_26"]
            + summary["line_27"]
            + summary["line_28d"]
            + summary["line_29"]
            + summary["line_30c"]
        )
        summary["line_32"] = (
            summary["line_31"]
            - summary["line_21aii"]
            - summary["line_30aii"]
        )
        summary["line_33"] = (
            summary["line_11d"]
        )
        summary["line_34"] = (
            summary["line_28d"]
        )
        summary["line_35"] = (
            summary["line_33"]
            - summary["line_34"]
        )
        summary["line_36"] = (
            summary["line_21ai"]
            + summary["line_21b"]
        )
        summary["line_37"] = (
            summary["line_15"]
        )
        summary["line_38"] = (
            summary["line_36"]
            - summary["line_37"]
        )
        summary["line_6c"] = (
            summary["line_11d"]
            + summary["line_12"]
            + summary["line_13"]
            + summary["line_14"]
            + summary["line_15"]
            + summary["line_16"]
            + summary["line_17"]
            + summary["line_18c"]
        )
        summary["line_6d"] = (
            summary["line_6b"]
            + summary["line_6c"]
        )
        summary["line_7"] = (
            summary["line_31"]
        )
        summary["line_8"] = (
            summary["line_6d"]
            - summary["line_7"]
        )
        summary["line_19"] = (
            summary["line_6c"]
        )
        summary["line_20"] = (
            summary["line_19"]
            - summary["line_18c"]
        )

        # Remove temporary aggregations to clean up the summary
        for key in list(summary.keys()):
            if key.startswith("temp_"):
                summary.pop(key)

        return summary

    def calculate_summary_column_b(self):
        committee = self.report.committee_account
        report_date = self.report.coverage_through_date
        report_year = report_date.year

        ytd_transactions = Transaction.objects.filter(
            committee_account=committee, date__year=report_year, date__lte=report_date,
        )

        # build summary
        summary = ytd_transactions.aggregate(
            line_11ai=self.get_line("SA11AI"),
            line_11aii=self.get_line("SA11AII"),
            line_11b=self.get_line("SA11B"),
            line_11c=self.get_line("SA11C"),
            line_12=self.get_line("SA12"),
            line_13=self.get_line("SA13"),
            line_14=self.get_line("SA14"),
            line_15=self.get_line("SA15"),
            line_16=self.get_line("SA16"),
            line_17=self.get_line("SA17"),
            line_21b=self.get_line("SB21B"),
            line_22=self.get_line("SB22"),
            line_23=self.get_line("SB23"),
            line_24=self.get_line("SE"),
            line_26=self.get_line("SB26"),
            line_27=self.get_line("SB27"),
            line_28a=self.get_line("SB28A"),
            line_28b=self.get_line("SB28B"),
            line_28c=self.get_line("SB28C"),
            line_29=self.get_line("SB29"),
            line_30b=self.get_line("SB30B"),
        )

        summary["line_11aiii"] = (
            summary["line_11ai"]
            + summary["line_11aii"]
        )
        summary["line_11d"] = (
            summary["line_11aiii"]
            + summary["line_11b"]
            + summary["line_11c"]
        )
        summary["line_18c"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_21ai"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_21aii"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_21c"] = (
            summary["line_21ai"]
            + summary["line_21aii"]
            + summary["line_21b"]
        )
        summary["line_25"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_28d"] = (
            summary["line_28a"]
            + summary["line_28b"]
            + summary["line_28c"]
        )
        summary["line_30ai"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_30aii"] = Decimal(0)  # Stubbed out until a future ticket
        summary["line_30c"] = (
            summary["line_30ai"]
            + summary["line_30aii"]
            + summary["line_30b"]
        )
        summary["line_31"] = (
            summary["line_21c"]
            + summary["line_22"]
            + summary["line_23"]
            + summary["line_24"]
            + summary["line_25"]
            + summary["line_26"]
            + summary["line_27"]
            + summary["line_28d"]
            + summary["line_29"]
            + summary["line_30c"]
        )
        summary["line_32"] = (
            summary["line_31"]
            - summary["line_21aii"]
            - summary["line_30aii"]
        )
        summary["line_33"] = (
            summary["line_11d"]
        )
        summary["line_34"] = (
            summary["line_28d"]
        )
        summary["line_35"] = (
            summary["line_33"]
            - summary["line_34"]
        )
        summary["line_36"] = (
            summary["line_21ai"]
            + summary["line_21b"]
        )
        summary["line_37"] = (
            summary["line_15"]
        )
        summary["line_38"] = (
            summary["line_36"]
            - summary["line_37"]
        )
        summary["line_6c"] = (
            summary["line_11d"]
            + summary["line_12"]
            + summary["line_13"]
            + summary["line_14"]
            + summary["line_15"]
            + summary["line_16"]
            + summary["line_17"]
            + summary["line_18c"]
        )
        summary["line_6d"] = (
            summary["line_6a"]
            + summary["line_6c"]
        )
        summary["line_7"] = (
            summary["line_31"]
        )
        summary["line_8"] = (
            summary["line_6d"]
            - summary["line_7"]
        )
        summary["line_19"] = (
            summary["line_6c"]
        )
        summary["line_20"] = (
            summary["line_19"]
            - summary["line_18c"]
        )

        return summary

    def get_line(self, form_type, field="amount"):
        query = Q(~Q(memo_code=True), form_type=form_type)
        return Coalesce(Sum(field, filter=query), Decimal(0.0))
