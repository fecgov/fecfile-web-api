from decimal import Decimal
from fecfiler.transactions.models import Transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce


class SummaryService:
    def __init__(self, report) -> None:
        self.report = report

    def calculate_summary(self):
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

    def _create_contribution_sum(self, query):
        return Coalesce(
            Sum("amount", filter=query),
            Decimal(0.0),
        )
