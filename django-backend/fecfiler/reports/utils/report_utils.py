from ..models import Report
from uuid import UUID
from fecfiler.web_services.models import (
    DotFEC,
    UploadSubmission,
    WebPrintSubmission,
)
from fecfiler.s3 import S3_SESSION
from fecfiler.settings import AWS_STORAGE_BUCKET_NAME
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

    # clear the dot_fec record if matching report_id found and delete from S3
    dot_fec_record = DotFEC.objects.get(report_id=report_uuid)
    if dot_fec_record:
        if S3_SESSION is not None:
            file_name = dot_fec_record.file_name
            s3_object = S3_SESSION.Object(AWS_STORAGE_BUCKET_NAME, file_name)
            s3_object.delete()
            logger.info(f"Deleted dotfec file {file_name} from S3.")
        dot_fec_record.delete()

    Report.objects.filter(id=report_uuid).update(
        calculation_status=None,
        calculation_token=None,
        upload_submission_id=None,
        webprint_submission_id=None,
    )
