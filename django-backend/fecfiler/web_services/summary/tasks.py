from enum import Enum
from celery import shared_task
from fecfiler.f3x_summaries.models import F3XSummary
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
        report = F3XSummary.objects.get(id=report_id)
    except Exception:
        return None
    report.calculation_status = CalculationState.CALCULATING
    report.save()

    summary_service = SummaryService(report)
    summary = summary_service.calculate_summary()
    a = summary["a"]
    b = summary["b"]

    # line 11ai
    report.L11ai_itemized_period = a["line_11ai"]
    report.L11ai_itemized_ytd = b["line_11ai"]
    # line 11aii
    report.L11aii_unitemized_period = a["line_11aii"]
    report.L11aii_unitemized_ytd = b["line_11aii"]
    # line 11aiii
    report.L11aiii_total_period = a["line_11aiii"]
    report.L11aiii_total_ytd = b["line_11aiii"]
    # line 11b
    report.L11b_political_party_committees_period = a["line_11b"]
    report.L11b_political_party_committees_ytd = b["line_11b"]
    # line 11c
    report.L11c_other_political_committees_pacs_period = a["line_11c"]
    report.L11c_other_political_committees_pacs_ytd = b["line_11c"]
    # line 11d
    report.L11d_total_contributions_period = a["line_11d"]
    report.L11d_total_contributions_ytd = b["line_11d"]
    # line 12
    report.L12_transfers_from_affiliated_other_party_cmtes_period = a["line_12"]
    report.L12_transfers_from_affiliated_other_party_cmtes_ytd = b["line_12"]
    # line 13
    report.L13_all_loans_received_period = a["line_13"]
    report.L13_all_loans_received_ytd = b["line_13"]
    # line 14
    report.L14_loan_repayments_received_period = a["line_14"]
    report.L14_loan_repayments_received_ytd = b["line_14"]
    # line 15
    report.L15_offsets_to_operating_expenditures_refunds_period = a["line_15"]
    report.L15_offsets_to_operating_expenditures_refunds_ytd = b["line_15"]
    # line 16
    report.L16_refunds_of_federal_contributions_period = a["line_16"]
    report.L16_refunds_of_federal_contributions_ytd = b["line_16"]
    # line 17
    report.L17_other_federal_receipts_dividends_period = a["line_17"]
    report.L17_other_federal_receipts_dividends_ytd = b["line_17"]
    # line 21b
    report.L21b_other_federal_operating_expenditures_period = a["line_21b"]
    report.L21b_other_federal_operating_expenditures_ytd = b["line_21b"]
    # line 22
    report.L22_transfers_to_affiliated_other_party_cmtes_period = a["line_22"]
    report.L22_transfers_to_affiliated_other_party_cmtes_ytd = b["line_22"]
    # line 23
    report.L23_contributions_to_federal_candidates_cmtes_period = a["line_23"]
    report.L23_contributions_to_federal_candidates_cmtes_ytd = b["line_23"]
    # line 26
    report.L26_loan_repayments_period = a["line_26"]
    report.L26_loan_repayments_made_ytd = b["line_26"]
    # line 27
    report.L27_loans_made_period = a["line_27"]
    report.L27_loans_made_ytd = b["line_27"]
    # line 28a
    report.L28a_individuals_persons_period = a["line_28a"]
    report.L28a_individuals_persons_ytd = b["line_28a"]
    # line 28b
    report.L28b_political_party_committees_period = a["line_28b"]
    report.L28b_political_party_committees_ytd = b["line_28b"]
    # line 28c
    report.L28c_other_political_committees_period = a["line_28c"]
    report.L28c_other_political_committees_ytd = b["line_28c"]
    # line 28d
    report.L28d_total_contributions_refunds_period = a["line_28d"]
    report.L28d_total_contributions_refunds_ytd = b["line_28d"]
    # line 29
    report.L29_other_disbursements_period = a["line_29"]
    report.L29_other_disbursements_ytd = b["line_29"]
    # line 30b
    report.L30b_nonallocable_fed_election_activity_period = a["line_30b"]
    report.L30b_nonallocable_fed_election_activity_ytd = b["line_30b"]
    # line 33
    report.L33_total_contributions_period = a["line_33"]
    report.L33_total_contributions_ytd = b["line_33"]
    # line 34
    report.L34_total_contribution_refunds_period = a["line_34"]
    report.L34_total_contribution_refunds_ytd = b["line_34"]
    # line 35
    report.L35_net_contributions_period = a["line_35"]
    report.L35_net_contributions_ytd = b["line_35"]
    # line 37
    report.L37_offsets_to_operating_expenditures_period = a["line_37"]
    report.L37_offsets_to_operating_expenditures_ytd = b["line_37"]

    report.calculation_status = CalculationState.SUCCEEDED
    report.save()
    return report.id
