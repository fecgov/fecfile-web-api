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
            "b": self.calculate_summary_column_b()
        }

        return summary

    def calculate_summary_column_a(self):
        report_transactions = Transaction.objects.filter(report=self.report)
        # line 11ai
        sa11ai_query = Q(~Q(memo_code=True), itemized=True, form_type="SA11AI")
        line_11ai = self._create_amount_sum(sa11ai_query)
        # line 11aii
        sa11aii_query = Q(~Q(memo_code=True), itemized=False, form_type="SA11AI")
        line_11aii = self._create_amount_sum(sa11aii_query)
        # line 11b
        sa11b_query = Q(~Q(memo_code=True), form_type="SA11B")
        line_11b = self._create_amount_sum(sa11b_query)
        # line 11c
        sa11c_query = Q(~Q(memo_code=True), form_type="SA11C")
        line_11c = self._create_amount_sum(sa11c_query)
        # line 12
        sa12_query = Q(~Q(memo_code=True), form_type="SA12")
        line_12 = self._create_amount_sum(sa12_query)
        # line 15
        sa15_query = Q(~Q(memo_code=True), form_type="SA15")
        line_15 = self._create_amount_sum(sa15_query)
        # line 17
        sa17_query = Q(~Q(memo_code=True), form_type="SA17")
        line_17 = self._create_amount_sum(sa17_query)
        # line 28a
        sb28a_query = Q(~Q(memo_code=True), form_type="SB28A")
        line_28a = self._create_amount_sum(sb28a_query)
        # line 28b
        sb28b_query = Q(~Q(memo_code=True), form_type="SB28B")
        line_28b = self._create_amount_sum(sb28b_query)
        # line 28c
        sb28c_query = Q(~Q(memo_code=True), form_type="SB28C")
        line_28c = self._create_amount_sum(sb28c_query)
        summary = report_transactions.aggregate(
            line_11ai=line_11ai,
            line_11aii=line_11aii,
            line_11b=line_11b,
            line_11c=line_11c,
            line_12=line_12,
            line_15=line_15,
            line_17=line_17,
            line_28a=line_28a,
            line_28b=line_28b,
            line_28c=line_28c,
            line_37=line_15
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

        # line 11ai
        sa11ai_query = Q(~Q(memo_code=True), itemized=True, form_type="SA11AI")
        line_11ai = self._create_amount_sum(sa11ai_query)
        # line 11aii
        sa11aii_query = Q(~Q(memo_code=True), itemized=False, form_type="SA11AI")
        line_11aii = self._create_amount_sum(sa11aii_query)
        # line 11b
        sa11b_query = Q(~Q(memo_code=True), form_type="SA11B")
        line_11b = self._create_amount_sum(sa11b_query)
        # line 11c
        sa11c_query = Q(~Q(memo_code=True), form_type="SA11C")
        line_11c = self._create_amount_sum(sa11c_query)
        # line 12
        sa12_query = Q(~Q(memo_code=True), form_type="SA12")
        line_12 = self._create_amount_sum(sa12_query)
        # line 15
        sa15_query = Q(~Q(memo_code=True), form_type="SA15")
        line_15 = self._create_amount_sum(sa15_query)
        # line 17
        sa17_query = Q(~Q(memo_code=True), form_type="SA17")
        line_17 = self._create_amount_sum(sa17_query)
        # line 28a
        sb28a_query = Q(~Q(memo_code=True), form_type="SB28A")
        line_28a = self._create_amount_sum(sb28a_query)
        # line 28b
        sb28b_query = Q(~Q(memo_code=True), form_type="SB28B")
        line_28b = self._create_amount_sum(sb28b_query)
        # line 28c
        sb28c_query = Q(~Q(memo_code=True), form_type="SB28C")
        line_28c = self._create_amount_sum(sb28c_query)

        # build summary
        summary = ytd_transactions.aggregate(
            line_11ai=line_11ai,
            line_11aii=line_11aii,
            line_11b=line_11b,
            line_11c=line_11c,
            line_12=line_12,
            line_15=line_15,
            line_17=line_17,
            line_28a=line_28a,
            line_28b=line_28b,
            line_28c=line_28c,
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
        summary["line_37"] = summary["line_15"]

        return summary

    def _create_amount_sum(self, query):
        return Coalesce(
            Sum("amount", filter=query),
            Decimal(0.0),
        )
