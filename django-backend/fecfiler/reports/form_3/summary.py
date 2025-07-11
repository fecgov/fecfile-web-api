from fecfiler.reports.form_3.models import Form3
import structlog

logger = structlog.get_logger(__name__)


def calculate_summary(report):
    form_3: Form3 = report.form_3

    form_3.L6a_total_contributions_period = 0
    form_3.L6b_total_contribution_refunds_period = 0
    form_3.L6c_net_contributions_period = 0
    form_3.L7a_total_operating_expenditures_period = 0
    form_3.L7b_total_offsets_to_operating_expenditures_period = 0
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
    form_3.L14_offsets_to_operating_expenditures_period = 0
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
    form_3.L7b_total_offsets_to_operating_expenditures_ytd = 0
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
    form_3.L14_offsets_to_operating_expenditures_ytd = 0
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
