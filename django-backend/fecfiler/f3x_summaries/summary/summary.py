from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.scha_transactions.models import SchATransaction
from django.db.models import Q, Sum


class SummaryService:
    def __init__(self, report) -> None:
        self.report = report

    def calculate_summary(self):
        report_transactions = SchATransaction.objects.filter(report=self.report)
        # just line 15
        sa15_query = Q(form_type="SA15", memo_code=False)
        line_15 = Sum("contribution_amount", filter=sa15_query)
        summary = report_transactions.aggregate(line_15=line_15)
        return summary
