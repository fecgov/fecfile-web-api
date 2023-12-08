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
        column_a = self.calculate_summary_column_a()
        column_b = self.calculate_summary_column_b()

        column_a, column_b = self.calculate_cash_on_hand_fields(column_a, column_b)

        return column_a, column_b

    def calculate_summary_column_a(self):
        report_transactions = Transaction.objects.filter(report_id=self.report.id)
        column_a = report_transactions.aggregate(
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
            temp_sd10=self.get_line("SD10", field="balance_at_close"),
        )

        column_a["line_9"] = column_a["temp_sc9"] + column_a["temp_sd9"]
        column_a["line_10"] = column_a["temp_sc10"] + column_a["temp_sd10"]
        column_a["line_11aiii"] = column_a["line_11ai"] + column_a["line_11aii"]
        column_a["line_11d"] = (
            column_a["line_11aiii"] + column_a["line_11b"] + column_a["line_11c"]
        )
        column_a["line_18c"] = Decimal(0)  # Stubbed out until a future ticket
        column_a["line_21ai"] = Decimal(0)  # Stubbed out until a future ticket
        column_a["line_21aii"] = Decimal(0)  # Stubbed out until a future ticket
        column_a["line_21c"] = (
            column_a["line_21ai"] + column_a["line_21aii"] + column_a["line_21b"]
        )
        column_a["line_25"] = Decimal(0)  # Stubbed out until a future ticket
        column_a["line_28d"] = (
            column_a["line_28a"] + column_a["line_28b"] + column_a["line_28c"]
        )
        column_a["line_30ai"] = Decimal(0)  # Stubbed out until a future ticket
        column_a["line_30aii"] = Decimal(0)  # Stubbed out until a future ticket
        column_a["line_30c"] = (
            column_a["line_30ai"] + column_a["line_30aii"] + column_a["line_30b"]
        )
        column_a["line_31"] = (
            column_a["line_21c"]
            + column_a["line_22"]
            + column_a["line_23"]
            + column_a["line_24"]
            + column_a["line_25"]
            + column_a["line_26"]
            + column_a["line_27"]
            + column_a["line_28d"]
            + column_a["line_29"]
            + column_a["line_30c"]
        )
        column_a["line_32"] = (
            column_a["line_31"] - column_a["line_21aii"] - column_a["line_30aii"]
        )
        column_a["line_33"] = column_a["line_11d"]
        column_a["line_34"] = column_a["line_28d"]
        column_a["line_35"] = column_a["line_33"] - column_a["line_34"]
        column_a["line_36"] = column_a["line_21ai"] + column_a["line_21b"]
        column_a["line_37"] = column_a["line_15"]
        column_a["line_38"] = column_a["line_36"] - column_a["line_37"]
        column_a["line_6c"] = (
            column_a["line_11d"]
            + column_a["line_12"]
            + column_a["line_13"]
            + column_a["line_14"]
            + column_a["line_15"]
            + column_a["line_16"]
            + column_a["line_17"]
            + column_a["line_18c"]
        )
        column_a["line_7"] = column_a["line_31"]
        column_a["line_19"] = column_a["line_6c"]
        column_a["line_20"] = column_a["line_19"] - column_a["line_18c"]

        # Remove temporary aggregations to clean up the summary
        for key in list(column_a.keys()):
            if key.startswith("temp_"):
                column_a.pop(key)

        return column_a

    def calculate_summary_column_b(self):
        committee = self.report.committee_account
        report_date = self.report.coverage_through_date
        report_year = report_date.year

        ytd_transactions = Transaction.objects.filter(
            committee_account=committee,
            date__year=report_year,
            date__lte=report_date,
        )

        # build summary
        column_b = ytd_transactions.aggregate(
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

        column_b["line_11aiii"] = column_b["line_11ai"] + column_b["line_11aii"]
        column_b["line_11d"] = (
            column_b["line_11aiii"] + column_b["line_11b"] + column_b["line_11c"]
        )
        column_b["line_18c"] = Decimal(0)  # Stubbed out until a future ticket
        column_b["line_21ai"] = Decimal(0)  # Stubbed out until a future ticket
        column_b["line_21aii"] = Decimal(0)  # Stubbed out until a future ticket
        column_b["line_21c"] = (
            column_b["line_21ai"] + column_b["line_21aii"] + column_b["line_21b"]
        )
        column_b["line_25"] = Decimal(0)  # Stubbed out until a future ticket
        column_b["line_28d"] = (
            column_b["line_28a"] + column_b["line_28b"] + column_b["line_28c"]
        )
        column_b["line_30ai"] = Decimal(0)  # Stubbed out until a future ticket
        column_b["line_30aii"] = Decimal(0)  # Stubbed out until a future ticket
        column_b["line_30c"] = (
            column_b["line_30ai"] + column_b["line_30aii"] + column_b["line_30b"]
        )
        column_b["line_31"] = (
            column_b["line_21c"]
            + column_b["line_22"]
            + column_b["line_23"]
            + column_b["line_24"]
            + column_b["line_25"]
            + column_b["line_26"]
            + column_b["line_27"]
            + column_b["line_28d"]
            + column_b["line_29"]
            + column_b["line_30c"]
        )
        column_b["line_32"] = (
            column_b["line_31"] - column_b["line_21aii"] - column_b["line_30aii"]
        )
        column_b["line_33"] = column_b["line_11d"]
        column_b["line_34"] = column_b["line_28d"]
        column_b["line_35"] = column_b["line_33"] - column_b["line_34"]
        column_b["line_36"] = column_b["line_21ai"] + column_b["line_21b"]
        column_b["line_37"] = column_b["line_15"]
        column_b["line_38"] = column_b["line_36"] - column_b["line_37"]
        column_b["line_6c"] = (
            column_b["line_11d"]
            + column_b["line_12"]
            + column_b["line_13"]
            + column_b["line_14"]
            + column_b["line_15"]
            + column_b["line_16"]
            + column_b["line_17"]
            + column_b["line_18c"]
        )
        column_b["line_7"] = column_b["line_31"]
        column_b["line_19"] = column_b["line_6c"]
        column_b["line_20"] = column_b["line_19"] - column_b["line_18c"]

        return column_b

    def calculate_cash_on_hand_fields(self, column_a, column_b):
        reports_from_prior_years = Report.objects.filter(
            committee_account=self.report.committee_account,
            coverage_through_date__year__lt=self.report.coverage_from_date.year,
            form_3x__isnull=False,
        ).order_by("coverage_from_date")

        if reports_from_prior_years.count() > 0:
            column_b["line_6a"] = reports_from_prior_years.last().form_3x.L8_cash_on_hand_close_ytd # noqa: E501
        elif self.previous_report:
            column_b["line_6a"] = self.previous_report.form_3x.L6a_cash_on_hand_jan_1_ytd  # noqa: E501
        else:
            #  user defined cash on hand
            column_b["line_6a"] = self.report.form_3x.L6a_cash_on_hand_jan_1_ytd

        if self.previous_report:
            column_a["line_6b"] = self.previous_report.form_3x.L8_cash_on_hand_at_close_period # noqa: E501
        else:
            #  user defined cash on hand
            column_a["line_6b"] = self.report.form_3x.L6a_cash_on_hand_jan_1_ytd

        if column_a["line_6b"] and column_b["line_6a"]:
            column_a["line_6d"] = column_a["line_6b"] + column_a["line_6c"]
            column_a["line_8"] = column_a["line_6d"] - column_a["line_7"]
            column_b["line_6d"] = column_b["line_6a"] + column_b["line_6c"]
            column_b["line_8"] = column_b["line_6d"] - column_b["line_7"]
        return column_a, column_b

    def get_line(self, form_type, field="amount"):
        query = Q(~Q(memo_code=True), form_type=form_type)
        return Coalesce(Sum(field, filter=query), Decimal(0.0))
