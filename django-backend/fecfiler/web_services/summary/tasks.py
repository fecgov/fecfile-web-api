from enum import Enum
from celery import shared_task
from fecfiler.reports.models import Report, FORMS_TO_CALCULATE, Q
from fecfiler.reports.form_3x.summary import calculate_summary as calculate_summary_3x
from fecfiler.reports.form_3.summary import calculate_summary as calculate_summary_3
from fecfiler.settings import SYSTEM_STATUS_CACHE_BACKEND
import uuid
import structlog
import redis

logger = structlog.get_logger(__name__)

if SYSTEM_STATUS_CACHE_BACKEND:
    redis_instance = redis.Redis.from_url(SYSTEM_STATUS_CACHE_BACKEND)
else:
    raise SystemError("SYSTEM_STATUS_CACHE_BACKEND is not set")


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
        Q(form_3x__isnull=False) | Q(form_3__isnull=False),
        committee_account=primary_report.committee_account,
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
            if redis_instance:
                try:
                    channel_name = f"calculation_status:{report.id}"
                    redis_instance.publish(channel_name, str(CalculationState.SUCCEEDED))
                    logger.info(f"Published SUCCEEDED to {channel_name}")
                except Exception as e:
                    logger.error(
                        f"Failed to publish to Redis for report {report.id}: {e}"
                    )

    return primary_report.id
