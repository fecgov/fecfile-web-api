from datetime import datetime
import math
from celery import shared_task
from fecfiler.web_services.models import (
    BaseSubmission,
    DotFEC,
    UploadSubmission,
    WebPrintSubmission,
    FECSubmissionState,
    FECStatus,
)
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_dot_fec
from fecfiler.web_services.dot_fec.dot_fec_submitter import (
    EFODotFECSubmitter,
    MockDotFECSubmitter,
)
from fecfiler.web_services.dot_fec.web_print_submitter import (
    EFOWebPrintSubmitter,
    MockWebPrintSubmitter,
)
from .web_service_storage import get_file_bytes, store_file
from fecfiler.settings import (
    INITIAL_POLLING_INTERVAL,
    INITIAL_POLLING_DURATION,
    INITIAL_POLLING_MAX_ATTEMPTS,
    SECONDARY_POLLING_INTERVAL,
    SECONDARY_POLLING_DURATION,
    SECONDARY_POLLING_MAX_ATTEMPTS,
)
import time
import structlog

logger = structlog.get_logger(__name__)


WEB_PRINT_KEY = "WebPrint"
MOCK_WEB_PRINT_KEY = "MockWebPrint"
EFO_SUBMITTER_KEY = "DotFEC"
MOCK_SUBMITTER_KEY = "MockDotFEC"
SUBMISSION_MANAGERS = {
    WEB_PRINT_KEY: EFOWebPrintSubmitter,
    MOCK_WEB_PRINT_KEY: MockWebPrintSubmitter,
    EFO_SUBMITTER_KEY: EFODotFECSubmitter,
    MOCK_SUBMITTER_KEY: MockDotFECSubmitter,
}
SUBMISSION_CLASSES = {
    WEB_PRINT_KEY: WebPrintSubmission,
    MOCK_WEB_PRINT_KEY: WebPrintSubmission,
    EFO_SUBMITTER_KEY: UploadSubmission,
    MOCK_SUBMITTER_KEY: UploadSubmission,
}

MAX_ATTEMPTS = INITIAL_POLLING_MAX_ATTEMPTS + SECONDARY_POLLING_MAX_ATTEMPTS


@shared_task
def create_dot_fec(
    report_id,
    upload_submission_id=None,
    webprint_submission_id=None,
    force_write_to_disk=False,
    file_name=None,
):
    submission = None
    if upload_submission_id:
        submission = UploadSubmission.objects.get(id=upload_submission_id)
        submission.save_state(FECSubmissionState.CREATING_FILE)
    if webprint_submission_id:
        submission = WebPrintSubmission.objects.get(id=webprint_submission_id)
        submission.save_state(FECSubmissionState.CREATING_FILE)

    logger.info("DANTEST: Sleeping for 10m.")
    time.sleep(600)
    logger.info("DANTEST: Awake and proceeding.")

    try:
        file_content = compose_dot_fec(report_id)
        if file_name is None:
            file_name = f"{report_id}_{math.floor(datetime.now().timestamp())}.fec"

        if not file_content:
            raise Exception("No file created")
        store_file(file_content, file_name, force_write_to_disk)
        dot_fec_record = DotFEC(report_id=report_id, file_name=file_name)
        dot_fec_record.save()
    except Exception as e:
        logger.error(f"Creating .FEC for report {report_id} failed: {e}")
        if submission is not None:
            submission.save_error("Creating .FEC failed")
        raise e

    if upload_submission_id:
        UploadSubmission.objects.filter(id=upload_submission_id).update(
            dot_fec=dot_fec_record
        )
    if webprint_submission_id:
        WebPrintSubmission.objects.filter(id=webprint_submission_id).update(
            dot_fec=dot_fec_record
        )

    return dot_fec_record.id


def log_polling_notice(attempts):
    duration = INITIAL_POLLING_DURATION + SECONDARY_POLLING_DURATION
    interval = (
        INITIAL_POLLING_INTERVAL
        if attempts <= INITIAL_POLLING_MAX_ATTEMPTS
        else SECONDARY_POLLING_INTERVAL
    )

    duration_in_minutes = duration / 60
    duration_in_hours = duration_in_minutes / 60
    duration_in_days = duration_in_hours / 24

    duration_string = f"{duration} second(s)"
    if duration_in_days >= 1:
        duration_string = f"{duration_in_days} day(s)"
    elif duration_in_hours >= 1:
        duration_string = f"{duration_in_hours} hour(s)"
    elif duration_in_minutes >= 1:
        duration_string = f"{duration_in_minutes} minutes(s)"

    logger.info(
        f"""Submission queued for processing.  Polling every {
            interval} seconds for {
            MAX_ATTEMPTS} attempts over {duration_string}"""
    )


@shared_task
def submit_to_fec(
    dot_fec_id,
    submission_record_id,
    e_filing_password,
    force_read_from_disk=False,
    backdoor_code=None,
    mock=False,
):
    submission = UploadSubmission.objects.get(id=submission_record_id)
    if submission.fecfile_task_state == FECSubmissionState.FAILED:
        return
    submission.save_state(FECSubmissionState.SUBMITTING)

    """Get Password"""
    if not e_filing_password:
        submission.save_error("No E-Filing Password provided")
        return

    """Get .FEC file bytes"""
    try:
        dot_fec_record = DotFEC.objects.get(id=dot_fec_id)
        file_name = dot_fec_record.file_name
        dot_fec_bytes = get_file_bytes(file_name, force_read_from_disk)
    except Exception:
        submission.save_error("Could not retrieve .FEC bytes")
        return

    """Submit to FEC"""
    try:
        submission_type_key = EFO_SUBMITTER_KEY if not mock else MOCK_SUBMITTER_KEY
        submitter = SUBMISSION_MANAGERS[submission_type_key]()
        logger.info(f"Uploading {file_name} to FEC")
        submission_json = submitter.get_submission_json(
            dot_fec_record, e_filing_password, backdoor_code
        )
        submission_response_string = submitter.submit(
            dot_fec_bytes, submission_json, dot_fec_record.report.report_id or None
        )
        submission.save_fec_response(submission_response_string)

        """Poll FEC for status of submission"""
        if submission.fec_status not in FECStatus.get_terminal_statuses_strings():
            log_polling_notice(submission.fecfile_polling_attempts)
            """ apply_async()
            The apply_async() method can only take json serializable values as arguments.
            This means we can't pass objects with methods.  To get around that, we pass
            the submission id and a key that we can use to determine the type of the
            submission.  This lets us instantiate objects of the correct classes as we
            need them."""
            return poll_for_fec_response.apply_async(
                [submission.id, submission_type_key, "Dot FEC"]
            )
        else:
            return resolve_final_submission_state(submission)
    except Exception as e:
        logger.error(f"Error before polling: {str(e)}")
        submission.save_error("Failed submitting to FEC")
        return resolve_final_submission_state(submission)


@shared_task
def submit_to_webprint(
    dot_fec_id, submission_record_id, force_read_from_disk=False, mock=False
):
    submission = WebPrintSubmission.objects.get(id=submission_record_id)
    submission.save_state(FECSubmissionState.SUBMITTING)

    """Get .FEC file bytes"""
    dot_fec_record = DotFEC.objects.get(id=dot_fec_id)
    file_name = dot_fec_record.file_name
    try:
        dot_fec_bytes = get_file_bytes(file_name, force_read_from_disk)
    except Exception:
        submission.save_error("Could not retrieve .FEC bytes")
        return

    """Submit to WebPrint"""
    try:
        submission_type_key = WEB_PRINT_KEY if not mock else MOCK_WEB_PRINT_KEY
        submitter = SUBMISSION_MANAGERS[submission_type_key]()
        logger.info(f"Uploading {file_name} to FEC WebPrint")
        submission_response_string = submitter.submit(None, dot_fec_bytes)
        submission.save_fec_response(submission_response_string)

        if submission.fec_status not in FECStatus.get_terminal_statuses_strings():
            log_polling_notice(submission.fecfile_polling_attempts)
            """ apply_async()
            The apply_async() method can only take json serializable values as arguments.
            This means we can't pass objects with methods.  To get around that, we pass
            the submission id and a key that we can use to determine the type of the
            submission.  This lets us instantiate objects of the correct classes as we
            need them."""
            countdown = calculate_polling_interval(submission.fecfile_polling_attempts)
            return poll_for_fec_response.apply_async(
                [submission.id, submission_type_key, "WebPrint"],
                countdown=countdown,
            )
        else:
            return resolve_final_submission_state(submission)
    except Exception as e:
        logger.error(f"Error before polling: {str(e)}")
        submission.save_error("Failed submitting to WebPrint")
        return resolve_final_submission_state(submission)


@shared_task
def poll_for_fec_response(submission_id, submission_type_key, submission_name):
    try:
        submission = SUBMISSION_CLASSES[submission_type_key].objects.get(id=submission_id)
        submitter = SUBMISSION_MANAGERS[submission_type_key]()

        submission.fecfile_polling_attempts += 1
        logger.info(f"Polling status for {submission.fec_submission_id}.")
        logger.info(f"Status: {submission.fec_status}, Message: {submission.fec_message}")
        logger.info(
            f"""Submission Polling - Attempt {
                submission.fecfile_polling_attempts
            } / {MAX_ATTEMPTS}"""
        )
        status_response_string = submitter.poll_status(submission)
        submission.save_fec_response(status_response_string)
        if (
            submission.fec_status in FECStatus.get_terminal_statuses_strings()
            or submission.fecfile_polling_attempts >= MAX_ATTEMPTS
        ):
            if submission.fecfile_polling_attempts >= MAX_ATTEMPTS:
                logger.warning("POLLING ATTEMPTS EXCEEDED")
                submission.fecfile_task_state = FECSubmissionState.FAILED.value
            return resolve_final_submission_state(submission)
        else:
            countdown = calculate_polling_interval(submission.fecfile_polling_attempts)
            return poll_for_fec_response.apply_async(
                [submission_id, submission_type_key, submission_name],
                countdown=countdown,
            )
    except Exception as e:
        logger.error(f"Error in polling: {str(e)}")
        submission.save_error(f"Failed submitting to {submission_name}")
        return resolve_final_submission_state(submission)


def calculate_polling_interval(attempts):
    """
    Determine the countdown interval based on the number of attempts.
    """
    if attempts <= INITIAL_POLLING_MAX_ATTEMPTS:
        return INITIAL_POLLING_INTERVAL
    elif attempts <= MAX_ATTEMPTS:
        return SECONDARY_POLLING_INTERVAL
    else:
        raise ValueError("Polling attempts exceeded the maximum allowed.")


def resolve_final_submission_state(submission: BaseSubmission):
    new_state = (
        FECSubmissionState.SUCCEEDED
        if submission.fec_status in [FECStatus.COMPLETED.value, FECStatus.ACCEPTED.value]
        else FECSubmissionState.FAILED
    )

    submission.save_state(new_state)

    if new_state == FECSubmissionState.FAILED:
        submission.log_submission_failure_state()

    return submission.id
