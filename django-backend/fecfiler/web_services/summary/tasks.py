from enum import Enum
from celery import shared_task
from fecfiler.reports.models import Report
from .summary import SummaryService

import logging

logger = logging.getLogger(__name__)


class CalculationState(Enum):
    """States of calculating summary"""

    CALCULATING = "CALCULATING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

    def __str__(self):
        return str(self.value)


@shared_task
def calculate_summary(report_id):
    try:
        report = Report.objects.get(id=report_id)
    except Exception:
        return None
    report.calculation_status = CalculationState.CALCULATING
    report.save()

    summary_service = SummaryService(report)
    summary = summary_service.calculate_summary()
    a = summary["a"]
    b = summary["b"]

    for key in a.keys():
        print("A", key, "-", a.get(key, 0))
    for key in b.keys():
        print("B", key, "-", b.get(key, 0))

    # line 6a
    report.form_3x.L6a_cash_on_hand_jan_1_ytd = b.get("line_6a", 0)
    report.form_3x.L6a_year_for_above_ytd = b.get("line_6a", 0)
    # line 6b
    report.form_3x.L6b_cash_on_hand_beginning_period = a.get("line_6b", 0)
    # line 6c
    report.form_3x.L6c_total_receipts_period = a.get("line_6c", 0)
    report.form_3x.L6c_total_receipts_ytd = b.get("line_6c", 0)
    # line 6d
    report.form_3x.L6d_subtotal_period = a.get("line_6d", 0)
    report.form_3x.L6d_subtotal_ytd = b.get("line_6d", 0)
    # line 7
    report.form_3x.L7_total_disbursements_period = a.get("line_7", 0)
    report.form_3x.L7_total_disbursements_ytd = b.get("line_7", 0)
    # line 8
    report.form_3x.L8_cash_on_hand_at_close_period = a.get("line_8", 0)
    report.form_3x.L8_cash_on_hand_close_ytd = b.get("line_8", 0)
    # line 9
    report.form_3x.L9_debts_to_period = a.get("line_9", 0)
    # line 10
    report.form_3x.L10_debts_by_period = a.get("line_10", 0)
    # line 11ai
    report.form_3x.L11ai_itemized_period = a.get("line_11ai", 0)
    report.form_3x.L11ai_itemized_ytd = b.get("line_11ai", 0)
    # line 11aii
    report.form_3x.L11aii_unitemized_period = a.get("line_11aii", 0)
    report.form_3x.L11aii_unitemized_ytd = b.get("line_11aii", 0)
    # line 11aiii
    report.form_3x.L11aiii_total_period = a.get("line_11aiii", 0)
    report.form_3x.L11aiii_total_ytd = b.get("line_11aiii", 0)
    # line 11b
    report.form_3x.L11b_political_party_committees_period = a.get("line_11b", 0)
    report.form_3x.L11b_political_party_committees_ytd = b.get("line_11b", 0)
    # line 11c
    report.form_3x.L11c_other_political_committees_pacs_period = a.get("line_11c", 0)
    report.form_3x.L11c_other_political_committees_pacs_ytd = b.get("line_11c", 0)
    # line 11d
    report.form_3x.L11d_total_contributions_period = a.get("line_11d", 0)
    report.form_3x.L11d_total_contributions_ytd = b.get("line_11d", 0)
    # line 12
    report.form_3x.L12_transfers_from_affiliated_other_party_cmtes_period = a.get("line_12", 0)
    report.form_3x.L12_transfers_from_affiliated_other_party_cmtes_ytd = b.get("line_12", 0)
    # line 13
    report.form_3x.L13_all_loans_received_period = a.get("line_13", 0)
    report.form_3x.L13_all_loans_received_ytd = b.get("line_13", 0)
    # line 14
    report.form_3x.L14_loan_repayments_received_period = a.get("line_14", 0)
    report.form_3x.L14_loan_repayments_received_ytd = b.get("line_14", 0)
    # line 15
    report.form_3x.L15_offsets_to_operating_expenditures_refunds_period = a.get("line_15", 0)
    report.form_3x.L15_offsets_to_operating_expenditures_refunds_ytd = b.get("line_15", 0)
    # line 16
    report.form_3x.L16_refunds_of_federal_contributions_period = a.get("line_16", 0)
    report.form_3x.L16_refunds_of_federal_contributions_ytd = b.get("line_16", 0)
    # line 17
    report.form_3x.L17_other_federal_receipts_dividends_period = a.get("line_17", 0)
    report.form_3x.L17_other_federal_receipts_dividends_ytd = b.get("line_17", 0)
    # line 18a
    report.form_3x.L18a_transfers_from_nonfederal_account_h3_period = a.get("line_18a", 0)
    report.form_3x.L18a_transfers_from_nonfederal_account_h3_ytd = b.get("line_18a", 0)
    # line 18b
    report.form_3x.L18b_transfers_from_nonfederal_levin_h5_period = a.get("line_18b", 0)
    report.form_3x.L18b_transfers_from_nonfederal_levin_h5_ytd = b.get("line_18b", 0)
    # line 18c
    report.form_3x.L18c_total_nonfederal_transfers_18a_18b_period = a.get("line_18c", 0)
    report.form_3x.L18c_total_nonfederal_transfers_18a_18b_ytd = b.get("line_18c", 0)
    # line 19
    report.form_3x.L19_total_receipts_period = a.get("line_19", 0)
    report.form_3x.L19_total_receipts_ytd = b.get("line_19", 0)
    # line 20
    report.form_3x.L20_total_federal_receipts_period = a.get("line_20", 0)
    report.form_3x.L20_total_federal_receipts_ytd = b.get("line_20", 0)
    # line 21ai
    report.form_3x.L21ai_federal_share_period = a.get("line_21ai", 0)
    report.form_3x.L21ai_federal_share_ytd = b.get("line_21ai", 0)
    # line 21aii
    report.form_3x.L21aii_nonfederal_share_period = a.get("line_21aii", 0)
    report.form_3x.L21aii_nonfederal_share_ytd = b.get("line_21aii", 0)
    # line 21b
    report.form_3x.L21b_other_federal_operating_expenditures_period = a.get("line_21b", 0)
    report.form_3x.L21b_other_federal_operating_expenditures_ytd = b.get("line_21b", 0)
    # line 21c
    report.form_3x.L21c_total_operating_expenditures_ytd = b.get("line_21c", 0)
    report.form_3x.L21c_total_operating_expenditures_period = a.get("line_21c", 0)
    # line 22
    report.form_3x.L22_transfers_to_affiliated_other_party_cmtes_period = a.get("line_22", 0)
    report.form_3x.L22_transfers_to_affiliated_other_party_cmtes_ytd = b.get("line_22", 0)
    # line 23
    report.form_3x.L23_contributions_to_federal_candidates_cmtes_period = a.get("line_23", 0)
    report.form_3x.L23_contributions_to_federal_candidates_cmtes_ytd = b.get("line_23", 0)
    # line 24
    report.form_3x.L24_independent_expenditures_period = a.get("line_24", 0)
    report.form_3x.L24_independent_expenditures_ytd = b.get("line_24", 0)
    # line 25
    report.form_3x.L25_coordinated_expend_made_by_party_cmtes_period = a.get("line_25", 0)
    report.form_3x.L25_coordinated_expend_made_by_party_cmtes_ytd = b.get("line_25", 0)
    # line 26
    report.form_3x.L26_loan_repayments_period = a.get("line_26", 0)
    report.form_3x.L26_loan_repayments_made_ytd = b.get("line_26", 0)
    # line 27
    report.form_3x.L27_loans_made_period = a.get("line_27", 0)
    report.form_3x.L27_loans_made_ytd = b.get("line_27", 0)
    # line 28a
    report.form_3x.L28a_individuals_persons_period = a.get("line_28a", 0)
    report.form_3x.L28a_individuals_persons_ytd = b.get("line_28a", 0)
    # line 28b
    report.form_3x.L28b_political_party_committees_period = a.get("line_28b", 0)
    report.form_3x.L28b_political_party_committees_ytd = b.get("line_28b", 0)
    # line 28c
    report.form_3x.L28c_other_political_committees_period = a.get("line_28c", 0)
    report.form_3x.L28c_other_political_committees_ytd = b.get("line_28c", 0)
    # line 28d
    report.form_3x.L28d_total_contributions_refunds_period = a.get("line_28d", 0)
    report.form_3x.L28d_total_contributions_refunds_ytd = b.get("line_28d", 0)
    # line 29
    report.form_3x.L29_other_disbursements_period = a.get("line_29", 0)
    report.form_3x.L29_other_disbursements_ytd = b.get("line_29", 0)
    # line 30ai
    report.form_3x.L30ai_shared_federal_activity_h6_fed_share_period = a.get("line_30ai", 0)
    report.form_3x.L30ai_shared_federal_activity_h6_fed_share_ytd = b.get("line_30ai", 0)
    # line 30aii
    report.form_3x.L30aii_shared_federal_activity_h6_nonfed_period = a.get("line_30aii", 0)
    report.form_3x.L30aii_shared_federal_activity_h6_nonfed_ytd = b.get("line_30aii", 0)
    # line 30b
    report.form_3x.L30b_nonallocable_fed_election_activity_period = a.get("line_30b", 0)
    report.form_3x.L30b_nonallocable_fed_election_activity_ytd = b.get("line_30b", 0)
    # line 30c
    report.form_3x.L30c_total_federal_election_activity_period = a.get("line_30c", 0)
    report.form_3x.L30c_total_federal_election_activity_ytd = b.get("line_30c", 0)
    # line 31
    report.form_3x.L31_total_disbursements_period = a.get("line_31", 0)
    report.form_3x.L31_total_disbursements_ytd = b.get("line_31", 0)
    # line 32
    report.form_3x.L32_total_federal_disbursements_period = a.get("line_32", 0)
    report.form_3x.L32_total_federal_disbursements_ytd = b.get("line_32", 0)
    # line 33
    report.form_3x.L33_total_contributions_period = a.get("line_33", 0)
    report.form_3x.L33_total_contributions_ytd = b.get("line_33", 0)
    # line 34
    report.form_3x.L34_total_contribution_refunds_period = a.get("line_34", 0)
    report.form_3x.L34_total_contribution_refunds_ytd = b.get("line_34", 0)
    # line 35
    report.form_3x.L35_net_contributions_period = a.get("line_35", 0)
    report.form_3x.L35_net_contributions_ytd = b.get("line_35", 0)
    # line 36
    report.form_3x.L36_total_federal_operating_expenditures_period = a.get("line_36", 0)
    report.form_3x.L36_total_federal_operating_expenditures_ytd = b.get("line_36", 0)
    # line 37
    report.form_3x.L37_offsets_to_operating_expenditures_period = a.get("line_37", 0)
    report.form_3x.L37_offsets_to_operating_expenditures_ytd = b.get("line_37", 0)
    # line 38
    report.form_3x.L38_net_operating_expenditures_period = a.get("line_38", 0)
    report.form_3x.L38_net_operating_expenditures_ytd = b.get("line_38", 0)

    report.form_3x.save()
    report.calculation_status = CalculationState.SUCCEEDED
    report.save()
    return report.id
