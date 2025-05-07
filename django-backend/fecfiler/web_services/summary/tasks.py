from enum import Enum
from celery import shared_task
from fecfiler.reports.models import Report, FORMS_TO_CALCULATE
from fecfiler.reports.form_3x.summary import calculate_summary as calculate_summary_3x
from fecfiler.reports.form_3.summary import calculate_summary as calculate_summary_3

import uuid
import structlog

logger = structlog.get_logger(__name__)


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
        primary_report = Report.objects.get(id=report_id)
    except Exception:
        return None

    if primary_report.get_form_name() not in FORMS_TO_CALCULATE:
        return primary_report.id

    reports_to_recalculate = Report.objects.filter(
        committee_account=primary_report.committee_account, form_3x__isnull=False
    ).order_by("coverage_through_date")
    calculation_token = uuid.uuid4()
    reports_to_recalculate.update(
        calculation_token=calculation_token,
        calculation_status=CalculationState.CALCULATING,
    )
    claimed_reports = list(reports_to_recalculate)

    for report in claimed_reports:
        if report.form_3x:
            calculate_summary_3x(report)
        elif report.form_3:
            calculate_summary_3(report)

        # Set the calculation status to SUCCEEDED *only*
        # if the recalculation still belongs to this task
        #
        # In the future, we can look into filtering on
        # calculation_status as well to prevent saving
        # reports that have been invalidated
        updated = bool(
            Report.objects.filter(
                id=report.id, calculation_token=calculation_token
            ).update(
                calculation_status=CalculationState.SUCCEEDED, calculation_token=None
            )
        )

        # If we failed to update, do not calculate any further reports
        if not updated:
            logger.info(
                f"Report: {report.id} (token: {calculation_token}) "
                "recalculation cancelled"
            )
            break
        else:
            logger.info(f"Report: {report.id} recalculated")

    return primary_report.id
