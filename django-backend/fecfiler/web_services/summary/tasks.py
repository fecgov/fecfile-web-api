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
    report.L15_offsets_to_operating_expenditures_refunds_period = summary["line_15"]
    report.L37_offsets_to_operating_expenditures_period = summary["line_15"]
    report.L12_transfers_from_affiliated_other_party_cmtes_period = summary["line_12"]
    report.calculation_status = CalculationState.SUCCEEDED
    report.save()
    return report.id