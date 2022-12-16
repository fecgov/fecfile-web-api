from decimal import Decimal
from fecfiler.transactions.schedule_a.models import ScheduleATransaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce


class SummaryService:
    def __init__(self, report) -> None:
        self.report = report

    def calculate_summary(self):
        report_transactions = ScheduleATransaction.objects.filter(report=self.report)
        # just line 15
        sa15_query = Q(~Q(memo_code=True), form_type="SA15")
        line_15 = self._create_contribution_sum(sa15_query)
        summary = report_transactions.aggregate(line_15=line_15)
        return summary

    def _create_contribution_sum(self, query):
        return Coalesce(
            Sum("contribution_amount", filter=query),
            Decimal(0.0),
        )
