from ..models import Report
from uuid import UUID
from fecfiler.web_services.models import (
    UploadSubmission,
    WebPrintSubmission,
)
import structlog

logger = structlog.get_logger(__name__)


def reset_submitting_report(id):
    report_uuid = UUID(id)

    # fetch upload_submission_id and delete associated upload record
    upload_submission_id = (
        Report.objects.filter(id=report_uuid)
        .values_list("upload_submission_id", flat=True)
        .first()
    )
    if upload_submission_id:
        UploadSubmission.objects.get(id=upload_submission_id).delete()

    # fetch webprint_submission_id and delete associated webprint record
    webprint_submission_id = (
        Report.objects.filter(id=report_uuid)
        .values_list("webprint_submission_id", flat=True)
        .first()
    )
    if webprint_submission_id:
        WebPrintSubmission.objects.get(id=webprint_submission_id).delete()

    Report.objects.filter(id=report_uuid).update(
        calculation_status=None,
        upload_submission_id=None,
        webprint_submission_id=None,
    )
