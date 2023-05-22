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

    # line 11ai
    report.L11ai_itemized_period = summary["a"]["line_11ai"]
    report.L11ai_itemized_ytd = summary["b"]["line_11ai"]
    # line 11aii
    report.L11aii_unitemized_period = summary["a"]["line_11aii"]
    report.L11aii_unitemized_ytd = summary["b"]["line_11aii"]
    # line 11aiii
    report.L11aiii_total_period = summary["a"]["line_11aiii"]
    report.L11aiii_total_ytd = summary["b"]["line_11aiii"]
    # line 11b
    report.L11b_political_party_committees_period = summary["a"]["line_11b"]
    report.L11b_political_party_committees_ytd = summary["b"]["line_11b"]
    # line 11c
    report.L11c_other_political_committees_pacs_period = summary["a"]["line_11c"]
    report.L11c_other_political_committees_pacs_ytd = summary["b"]["line_11c"]
    # line 11d
    report.L11d_total_contributions_period = summary["a"]["line_11d"]
    report.L11d_total_contributions_ytd = summary["b"]["line_11d"]
    # line 12
    report.L12_transfers_from_affiliated_other_party_cmtes_period = summary["a"][
        "line_12"
    ]
    report.L12_transfers_from_affiliated_other_party_cmtes_ytd = summary["b"]["line_12"]
    # line 15
    report.L15_offsets_to_operating_expenditures_refunds_period = summary["a"][
        "line_15"
    ]
    report.L15_offsets_to_operating_expenditures_refunds_ytd = summary["b"]["line_15"]
    # line 17
    report.L17_other_federal_receipts_dividends_period = summary["a"]["line_17"]
    report.L17_other_federal_receipts_dividends_ytd = summary["b"]["line_17"]
    # line 28a
    report.L28a_individuals_persons_period = summary["a"]["line_28a"]
    report.L28a_individuals_persons_ytd = summary["b"]["line_28a"]
    # line 28b
    report.L28b_political_party_committees_period = summary["a"]["line_28b"]
    report.L28b_political_party_committees_ytd = summary["b"]["line_28b"]
    # line 28c
    report.L28c_other_political_committees_period = summary["a"]["line_28c"]
    report.L28c_other_political_committees_ytd = summary["b"]["line_28c"]
    # line 28d
    report.L28d_total_contributions_refunds_period = summary["a"]["line_28d"]
    report.L28d_total_contributions_refunds_ytd = summary["b"]["line_28d"]
    # line 33
    report.L33_total_contributions_period = summary["a"]["line_33"]
    report.L33_total_contributions_ytd = summary["b"]["line_33"]
    # line 34
    report.L34_total_contribution_refunds_period = summary["a"]["line_34"]
    report.L34_total_contribution_refunds_ytd = summary["b"]["line_34"]
    # line 37
    report.L37_offsets_to_operating_expenditures_period = summary["a"]["line_37"]
    report.L37_offsets_to_operating_expenditures_ytd = summary["b"]["line_37"]

    report.calculation_status = CalculationState.SUCCEEDED
    report.save()
    return report.id
