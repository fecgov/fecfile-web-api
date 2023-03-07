from decimal import Decimal
from fecfiler.f3x_summaries.models import F3XSummary
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
            "b": self.calculate_summary_column_b()
        }

        return summary

    def calculate_summary_column_a(self):
        report_transactions = Transaction.objects.filter(report=self.report)
        # line 12
        sa12_query = Q(~Q(memo_code=True), form_type="SA12")
        line_12 = self._create_contribution_sum(sa12_query)
        # line 15
        sa15_query = Q(~Q(memo_code=True), form_type="SA15")
        line_15 = self._create_contribution_sum(sa15_query)
        # line 17
        sa17_query = Q(~Q(memo_code=True), form_type="SA17")
        line_17 = self._create_contribution_sum(sa17_query)
        # line 37 (intentional duplicate of Line 15)
        line_37 = line_15

        # build summary
        summary = report_transactions.aggregate(
            line_12=line_12,
            line_15=line_15,
            line_17=line_17,
            line_37=line_37
        )
        return summary

    def calculate_summary_column_b(self):
        committee = self.report.committee_account
        report_date = self.report.coverage_from_date
        report_year = report_date.year

        ytd_transactions = Transaction.objects.filter(
            committee_account=committee,
            date__year=report_year,
            date__lte=report_date,
        )

        # line 15
        sa15_query = Q(~Q(memo_code=True), form_type="SA15")
        line_15 = self._create_contribution_sum(sa15_query)

        # line 37 (intentional duplicate of Line 15)
        line_37 = line_15

        # build summary
        summary = ytd_transactions.aggregate(
            line_15=line_15,
            line_37=line_37
        )

        return summary

    def _create_contribution_sum(self, query):
        return Coalesce(
            Sum("amount", filter=query),
            Decimal(0.0),
        )
