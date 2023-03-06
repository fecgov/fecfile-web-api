from decimal import Decimal
from fecfiler.transactions.models import Transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce


class SummaryService:
    def __init__(self, report) -> None:
        self.report = report

    def calculate_summary(self):
        report_transactions = Transaction.objects.filter(report=self.report)
        # line 11ai
        sa11ai_query = Q(~Q(memo_code=True), form_type="SA11AI")
        line_11ai = self._create_contribution_sum(sa11ai_query)
        # line 11aii
        sa11aii_query = Q(~Q(memo_code=True), form_type="SA11AII")
        line_11aii = self._create_contribution_sum(sa11aii_query)
        # line 11aiii
        sa11aiii_query = sa11ai_query | sa11aii_query
        line_11aiii = self._create_contribution_sum(sa11aiii_query)
        # line 11b
        sa11b_query = Q(~Q(memo_code=True), form_type="SA11B")
        line_11b = self._create_contribution_sum(sa11b_query)
        # line 11c
        sa11c_query = Q(~Q(memo_code=True), form_type="SA11C")
        line_11c = self._create_contribution_sum(sa11c_query)
        # line 11d
        sa11d_query = sa11aiii_query | sa11b_query | sa11c_query
        line_11d = self._create_contribution_sum(sa11d_query)
        # line 12
        sa12_query = Q(~Q(memo_code=True), form_type="SA12")
        line_12 = self._create_contribution_sum(sa12_query)
        # just line 15
        sa15_query = Q(~Q(memo_code=True), form_type="SA15")
        line_15 = self._create_contribution_sum(sa15_query)
        # line 33
        line_33 = line_11d
        summary = report_transactions.aggregate(
            line_11ai=line_11ai,
            line_11aii=line_11aii,
            line_11aiii=line_11aiii,
            line_11b=line_11b,
            line_11c=line_11c,
            line_11d=line_11d,
            line_12=line_12,
            line_15=line_15,
            line_33=line_33,
        )
        return summary

    def _create_contribution_sum(self, query):
        return Coalesce(
            Sum("amount", filter=query),
            Decimal(0.0),
        )
