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
            temp_sc9=self.get_line("SC/9"),
            temp_sd9=self.get_line("SD/9"),
            temp_sc10=self.get_line("SC/10"),
            temp_sd10=self.get_line("SD/10")
        )
        summary["line_6c"] = (
            summary.get("line_11c", 0) +
            summary.get("line_12", 0) +
            summary.get("line_13", 0) +
            summary.get("line_14", 0) +
            summary.get("line_15", 0) +
            summary.get("line_16", 0) +
            summary.get("line_17", 0) +
            summary.get("line_18c", 0)
        )
        summary["line_9"] = (
            summary.get("temp_sc9", 0) +
            summary.get("temp_sd9", 0)
        )
        summary["line_10"] = (
            summary.get("temp_sc10", 0) +
            summary.get("temp_sd10", 0)
        )
        summary["line_11aiii"] = (
            summary.get("line_11ai", 0) +
            summary.get("line_11aii", 0)
        )
        summary["line_11d"] = (
            summary.get("line_11aiii", 0) +
            summary.get("line_11b", 0) +
            summary.get("line_11c", 0)
        )
        summary["line_19"] = (
            summary.get("line_6c", 0)
        )
        summary["line_20"] = (
            summary.get("line_19", 0) -
            summary.get("line_18c", 0)
        )
        summary["line_21c"] = (
            summary.get("line_21ai", 0) +
            summary.get("line_21aii", 0) +
            summary.get("line_21b", 0)
        )
        summary["line_28d"] = (
            summary.get("line_28a", 0) +
            summary.get("line_28b", 0) +
            summary.get("line_28c", 0)
        )
        summary["line_30c"] = (
            summary.get("line_30ai", 0) +
            summary.get("line_30aii", 0) +
            summary.get("line_30b", 0)
        )
        summary["line_31"] = (
            summary.get("line_21c", 0) +
            summary.get("line_22", 0) +
            summary.get("line_23", 0) +
            summary.get("line_24", 0) +
            summary.get("line_25", 0) +
            summary.get("line_26", 0) +
            summary.get("line_27", 0) +
            summary.get("line_28d", 0) +
            summary.get("line_29", 0) +
            summary.get("line_30c", 0)
        )
        summary["line_33"] = (
            summary.get("line_11d", 0)
        )
        summary["line_34"] = (
            summary.get("line_28d", 0)
        )
        summary["line_35"] = (
            summary.get("line_33", 0) -
            summary.get("line_34", 0)
        )
        summary["line_36"] = (
            summary.get("line_21ai", 0) +
            summary.get("line_21b", 0)
        )
        summary["line_37"] = (
            summary.get("line_15", 0)
        )
        summary["line_38"] = (
            summary.get("line_36", 0) -
            summary.get("line_37", 0)
        )
        summary["line_7"] = (
            summary.get("line_31")
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
            line_11ai=self.get_line("SA11AI", True),
            line_11aii=self.get_line("SA11AI", False),
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
        summary["line_6c"] = (
            summary.get("line_11c", 0) +
            summary.get("line_12", 0) +
            summary.get("line_13", 0) +
            summary.get("line_14", 0) +
            summary.get("line_15", 0) +
            summary.get("line_16", 0) +
            summary.get("line_17", 0) +
            summary.get("line_18c", 0)
        )
        summary["line_11aiii"] = (
            summary.get("line_11ai", 0) +
            summary.get("line_11aii", 0)
        )
        summary["line_11d"] = (
            summary.get("line_11aiii", 0) +
            summary.get("line_11b", 0) +
            summary.get("line_11c", 0)
        )
        summary["line_19"] = (
            summary.get("line_6c", 0)
        )
        summary["line_20"] = (
            summary.get("line_19", 0) -
            summary.get("line_18c", 0)
        )
        summary["line_21c"] = (
            summary.get("line_21ai", 0) +
            summary.get("line_21aii", 0) +
            summary.get("line_21b", 0)
        )
        summary["line_28d"] = (
            summary.get("line_28a", 0) +
            summary.get("line_28b", 0) +
            summary.get("line_28c", 0)
        )
        summary["line_30c"] = (
            summary.get("line_30ai", 0) +
            summary.get("line_30aii", 0) +
            summary.get("line_30b", 0)
        )
        summary["line_31"] = (
            summary.get("line_21c", 0) +
            summary.get("line_22", 0) +
            summary.get("line_23", 0) +
            summary.get("line_24", 0) +
            summary.get("line_25", 0) +
            summary.get("line_26", 0) +
            summary.get("line_27", 0) +
            summary.get("line_28d", 0) +
            summary.get("line_29", 0) +
            summary.get("line_30c", 0)
        )
        summary["line_33"] = (
            summary.get("line_11d", 0)
        )
        summary["line_34"] = (
            summary.get("line_28d", 0)
        )
        summary["line_35"] = (
            summary.get("line_33", 0) -
            summary.get("line_34", 0)
        )
        summary["line_36"] = (
            summary.get("line_21ai", 0) +
            summary.get("line_21b", 0)
        )
        summary["line_37"] = (
            summary.get("line_15", 0)
        )
        summary["line_38"] = (
            summary.get("line_36", 0) -
            summary.get("line_37", 0)
        )
        summary["line_7"] = (
            summary.get("line_31", 0)
        )

        return summary

    def get_line(self, form_type, itemized=None):
        query = (
            Q(~Q(memo_code=True), itemized=itemized, _form_type=form_type)
            if itemized is not None
            else Q(~Q(memo_code=True), _form_type=form_type)
        )
        return Coalesce(Sum("amount", filter=query), Decimal(0.0))
