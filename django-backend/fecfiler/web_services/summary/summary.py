from decimal import Decimal
from fecfiler.transactions.models import Transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
import logging

logger = logging.getLogger(__name__)


class SummaryService:
    def __init__(self, report) -> None:
        self.report = report

    def calculate_summary(self):
        summary = {
            "a": self.calculate_summary_column_a(),
            "b": self.calculate_summary_column_b(),
        }

        return summary

    def calculate_summary_column_a(self):
        report_transactions = Transaction.objects.filter(report=self.report)
        summary = report_transactions.aggregate(
            line_11ai=self.get_line("SA11AI", True),
            line_11aii=self.get_line("SA11AI", False),
            line_11b=self.get_line("SA11B"),
            line_11c=self.get_line("SA11C"),
            line_12=self.get_line("SA12"),
            line_15=self.get_line("SA15"),
            line_16=self.get_line("SA16"),
            line_17=self.get_line("SA17"),
            line_22=self.get_line("SB22"),
            line_28a=self.get_line("SB28A"),
            line_28b=self.get_line("SB28B"),
            line_28c=self.get_line("SB28C"),
            line_30b=self.get_line("SB30B"),
        )
        summary["line_11aiii"] = summary["line_11ai"] + summary["line_11aii"]
        summary["line_11d"] = (
            summary["line_11aiii"] + summary["line_11b"] + summary["line_11c"]
        )
        summary["line_28d"] = (
            summary["line_28a"] + summary["line_28b"] + summary["line_28c"]
        )
        summary["line_33"] = summary["line_11d"]
        summary["line_34"] = summary["line_28d"]
        summary["line_35"] = summary["line_33"] - summary["line_34"]
        summary["line_37"] = summary["line_15"]
        return summary

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
        summary = ytd_transactions.aggregate(
            line_11ai=self.get_line("SA11AI", True),
            line_11aii=self.get_line("SA11AI", False),
            line_11b=self.get_line("SA11B"),
            line_11c=self.get_line("SA11C"),
            line_12=self.get_line("SA12"),
            line_15=self.get_line("SA15"),
            line_16=self.get_line("SA16"),
            line_17=self.get_line("SA17"),
            line_22=self.get_line("SB22"),
            line_28a=self.get_line("SB28A"),
            line_28b=self.get_line("SB28B"),
            line_28c=self.get_line("SB28C"),
            line_30b=self.get_line("SB30B"),
        )
        summary["line_11aiii"] = summary["line_11ai"] + summary["line_11aii"]
        summary["line_11d"] = (
            summary["line_11aiii"] + summary["line_11b"] + summary["line_11c"]
        )
        summary["line_28d"] = (
            summary["line_28a"] + summary["line_28b"] + summary["line_28c"]
        )
        summary["line_33"] = summary["line_11d"]
        summary["line_34"] = summary["line_28d"]
        summary["line_35"] = summary["line_33"] - summary["line_34"]
        summary["line_37"] = summary["line_15"]

        return summary

    def get_line(self, form_type, itemized=None):
        query = (
            Q(~Q(memo_code=True), itemized=itemized, _form_type=form_type)
            if itemized is not None
            else Q(~Q(memo_code=True), _form_type=form_type)
        )
        return Coalesce(Sum("amount", filter=query), Decimal(0.0))
