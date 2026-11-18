from fecfiler.reports.form_3.models import Form3
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.line_mappings import LINE_MAPPINGS_BY_FORM_AND_LINE
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from decimal import Decimal
import structlog

logger = structlog.get_logger(__name__)


def calculate_summary(report):
    form_3: Form3 = report.form_3

    a, b = calculate_summary_columns(report)

    form_3.L6a_total_contributions_period = 0
    form_3.L6b_total_contribution_refunds_period = 0
    form_3.L6c_net_contributions_period = 0
    form_3.L7a_total_operating_expenditures_period = 0
    form_3.L7b_total_offsets_to_operating_expenditures_period = a.get("line_7b", 0)
    form_3.L7c_net_operating_expenditures_period = 0
    form_3.L8_cash_on_hand_at_close_period = 0
    form_3.L9_debts_owed_to_committee_period = 0
    form_3.L10_debts_owed_by_committee_period = 0
    form_3.L11ai_individuals_itemized_period = 0
    form_3.L11aii_individuals_unitemized_period = 0
    form_3.L11aiii_total_individual_period = 0
    form_3.L11b_political_party_committees_period = 0
    form_3.L11c_other_political_committees_period = 0
    form_3.L11d_the_candidate_period = 0
    form_3.L11e_total_contributions_period = 0
    form_3.L12_transfers_from_other_authorized_committees_period = 0
    form_3.L13a_loans_made_or_guaranteed_by_the_candidate_period = 0
    form_3.L13b_all_other_loans_period = 0
    form_3.L13c_total_loans_period = 0
    form_3.L14_offsets_to_operating_expenditures_period = a.get("line_14", 0)
    form_3.L15_other_receipts_period = 0
    form_3.L16_total_receipts_period = 0
    form_3.L17_operating_expenditures_period = 0
    form_3.L18_transfers_to_other_authorized_committees_period = 0
    form_3.L19a_loan_repayments_of_loans_made_or_guaranteed_by_candidate_period = 0
    form_3.L19b_loan_repayments_of_all_other_loans_period = 0
    form_3.L19c_total_loan_repayments_period = 0
    form_3.L20a_refunds_to_individuals_period = 0
    form_3.L20b_refunds_to_political_party_committees_period = 0
    form_3.L20c_refunds_to_other_political_committees_period = 0
    form_3.L20d_total_contribution_refunds_period = 0
    form_3.L21_other_disbursements_period = 0
    form_3.L22_total_disbursements_period = 0
    form_3.L23_cash_on_hand_beginning_reporting_period = 0
    form_3.L24_total_receipts_period = 0
    form_3.L25_subtotals_period = 0
    form_3.L26_total_disbursements_period = 0
    form_3.L27_cash_on_hand_at_close_period = 0
    form_3.L6a_total_contributions_ytd = 0
    form_3.L6b_total_contribution_refunds_ytd = 0
    form_3.L6c_net_contributions_ytd = 0
    form_3.L7a_total_operating_expenditures_ytd = 0
    form_3.L7b_total_offsets_to_operating_expenditures_ytd = b.get("line_7b", 0)
    form_3.L7c_net_operating_expenditures_ytd = 0
    form_3.L11ai_individuals_itemized_ytd = 0
    form_3.L11aii_individuals_unitemized_ytd = 0
    form_3.L11aiii_total_individual_ytd = 0
    form_3.L11b_political_party_committees_ytd = 0
    form_3.L11c_other_political_committees_ytd = 0
    form_3.L11d_the_candidate_ytd = 0
    form_3.L11e_total_contributions_ytd = 0
    form_3.L12_transfers_from_other_authorized_committees_ytd = 0
    form_3.L13a_loans_made_or_guaranteed_by_the_candidate_ytd = 0
    form_3.L13b_all_other_loans_ytd = 0
    form_3.L13c_total_loans_ytd = 0
    form_3.L14_offsets_to_operating_expenditures_ytd = b.get("line_14", 0)
    form_3.L15_other_receipts_ytd = 0
    form_3.L16_total_receipts_ytd = 0
    form_3.L17_operating_expenditures_ytd = 0
    form_3.L18_transfers_to_other_authorized_committees_ytd = 0
    form_3.L19a_loan_repayments_of_loans_made_or_guaranteed_by_candidate_ytd = 0
    form_3.L19b_loan_repayments_of_all_other_loans_ytd = 0
    form_3.L19c_total_loan_repayments_ytd = 0
    form_3.L20a_refunds_to_individuals_ytd = 0
    form_3.L20b_refunds_to_political_party_committees_ytd = 0
    form_3.L20c_refunds_to_other_political_committees_ytd = 0
    form_3.L20d_total_contribution_refunds_ytd = 0
    form_3.L21_other_disbursements_ytd = 0
    form_3.L22_total_disbursements_ytd = 0

    form_3.save()
    return


def calculate_summary_columns(report):
    column_a = calculate_summary_column_a(report)
    column_b = calculate_summary_column_b(report)

    return column_a, column_b


def calculate_summary_column_a(report: Report):
    committee_id = report.committee_account_id
    report_transactions = Transaction.objects.filter(
        reports__id=report.id,
        committee_account_id=committee_id,
    )
    column_a = report_transactions.aggregate(
        line_14=get_line("SA14"),
    )

    column_a["line_7b"] = column_a["line_14"]

    return column_a


def calculate_summary_column_b(report: Report):
    committee_id = report.committee_account_id
    report_date = report.coverage_through_date
    cycle_start_date = (
        report.form_3.election_cycle.start_date
        if report.form_3.election_cycle
        else report.coverage_from_date
    )

    ytd_transactions = Transaction.objects.filter(
        committee_account_id=committee_id,
        date__gte=cycle_start_date,
        date__lte=report_date,
    )

    column_b = ytd_transactions.aggregate(
        line_14=get_line("SA14"),
    )

    column_b["line_7b"] = column_b["line_14"]

    return column_b


def get_line(line_number, field="amount", itemized=None):
    transaction_types = LINE_MAPPINGS_BY_FORM_AND_LINE.get(
        ("form_3_id", line_number), []
    )
    query = Q(~Q(memo_code=True), transaction_type_identifier__in=transaction_types)
    if itemized is not None:
        query.add(Q(itemized=itemized), Q.AND)
    return Coalesce(Sum(field, filter=query), Decimal(0.0))
