from celery import shared_task
from fecfiler.f3x_summaries.models import F3XSummary
from .summary import SummaryService

import logging

logger = logging.getLogger(__name__)


@shared_task
def calculate_summary(report_id):
    try:
        report = F3XSummary.objects.get(id=report_id)
    except Exception:
        return None
    summary_service = SummaryService(report)
    summary = summary_service.calculate_summary()
    report.L15_offsets_to_operating_expenditures_refunds_period = summary["line_15"]
    report.save()
    return summary
