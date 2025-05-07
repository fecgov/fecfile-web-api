from fecfiler.reports.form_3.models import Form3
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.cash_on_hand.models import CashOnHandYearly
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from decimal import Decimal
import structlog

logger = structlog.get_logger(__name__)


def calculate_summary(report):
    form_3: Form3 = report.form_3

    form_3.L6a_total_contributions_period = 6.1
    form_3.L6b_total_contribution_refunds_period = 6.2
    form_3.L6c_net_contributions_period = 6.3
    form_3.L7a_total_operating_expenditures_period = 7.1
    form_3.L7b_total_offsets_to_operating_expenditures_period = 7.2
    form_3.L7c_net_operating_expenditures_period = 7.3
    form_3.L8_cash_on_hand_at_close_period = 8.1
    form_3.L9_debts_owed_to_committee_period = 9.1
    form_3.L10_debts_owed_by_committee_period = 10.1
    form_3.L11ai_individuals_itemized_period = 11.1
    form_3.L11aii_individuals_unitemized_period = 11.2
    form_3.L11aiii_total_individual_period = 11.3
    form_3.L11b_political_party_committees_period = 11.4
    form_3.L11c_other_political_committees_period = 11.5
    form_3.L11d_the_candidate_period = 11.6
    form_3.L11e_total_contributions_period = 11.7
    form_3.L12_transfers_from_other_authorized_committees_period = 12.1
    form_3.L13a_loans_made_or_guaranteed_by_the_candidate_period = 13.1
    form_3.L13b_all_other_loans_period = 13.2
    form_3.L13c_total_loans_period = 13.3
    form_3.L14_offsets_to_operating_expenditures_period = 14.1
    form_3.L15_other_receipts_period = 15.1
    form_3.L16_total_receipts_period = 16.1
    form_3.L17_operating_expenditures_period = 17.1
    form_3.L18_transfers_to_other_authorized_committees_period = 18.1
    form_3.L19a_loan_repayments_of_loans_made_or_guaranteed_by_candidate_period = 19.1
    form_3.L19b_loan_repayments_of_all_other_loans_period = 19.2
    form_3.L19c_total_loan_repayments_period = 19.3
    form_3.L20a_refunds_to_individuals_period = 20.1
    form_3.L20b_refunds_to_political_party_committees_period = 20.2
    form_3.L20c_refunds_to_other_political_committees_period = 20.3
    form_3.L20d_total_contribution_refunds_period = 20.4
    form_3.L21_other_disbursements_period = 21.1
    form_3.L22_total_disbursements_period = 22.1
    form_3.L23_cash_on_hand_beginning_reporting_period = 23.1
    form_3.L24_total_receipts_period = 24.1
    form_3.L25_subtotals_period = 25.1
    form_3.L26_total_disbursements_period = 26.1
    form_3.L27_cash_on_hand_at_close_period = 27.1
    form_3.L6a_total_contributions_ytd = 6.1
    form_3.L6b_total_contribution_refunds_ytd = 6.2
    form_3.L6c_net_contributions_ytd = 6.3
    form_3.L7a_total_operating_expenditures_ytd = 7.1
    form_3.L7b_total_offsets_to_operating_expenditures_ytd = 7.2
    form_3.L7c_net_operating_expenditures_ytd = 7.3
    form_3.L11ai_individuals_itemized_ytd = 11.1
    form_3.L11aii_individuals_unitemized_ytd = 11.2
    form_3.L11aiii_total_individual_ytd = 11.3
    form_3.L11b_political_party_committees_ytd = 11.4
    form_3.L11c_other_political_committees_ytd = 11.5
    form_3.L11d_the_candidate_ytd = 11.6
    form_3.L11e_total_contributions_ytd = 11.7
    form_3.L12_transfers_from_other_authorized_committees_ytd = 12.1
    form_3.L13a_loans_made_or_guaranteed_by_the_candidate_ytd = 13.1
    form_3.L13b_all_other_loans_ytd = 13.2
    form_3.L13c_total_loans_ytd = 13.3
    form_3.L14_offsets_to_operating_expenditures_ytd = 14.1
    form_3.L15_other_receipts_ytd = 15.1
    form_3.L16_total_receipts_ytd = 16.1
    form_3.L17_operating_expenditures_ytd = 17.1
    form_3.L18_transfers_to_other_authorized_committees_ytd = 18.1
    form_3.L19a_loan_repayments_of_loans_made_or_guaranteed_by_candidate_ytd = 19.1
    form_3.L19b_loan_repayments_of_all_other_loans_ytd = 19.2
    form_3.L19c_total_loan_repayments_ytd = 19.3
    form_3.L20a_refunds_to_individuals_ytd = 20.1
    form_3.L20b_refunds_to_political_party_committees_ytd = 20.2
    form_3.L20c_refunds_to_other_political_committees_ytd = 20.3
    form_3.L20d_total_contribution_refunds_ytd = 20.4
    form_3.L21_other_disbursements_ytd = 21.1
    form_3.L22_total_disbursements_ytd = 22.1

    form_3.save()
    return
