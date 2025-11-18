from ..models import UploadSubmission, FECSubmissionState
import structlog

logger = structlog.get_logger(__name__)


def fail_open_submissions():
    UploadSubmission.objects.exclude(
        fecfile_task_state__in=FECSubmissionState.get_terminal_statuses_strings()
    ).update(fecfile_task_state=FECSubmissionState.FAILED)
    logger.info("All in-progress report submissions have been marked as FAILED.")
