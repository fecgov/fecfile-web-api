from datetime import datetime
import math
import time
from celery import shared_task
from fecfiler.web_services.models import (
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
from fecfiler.settings import WEBPRINT_EMAIL, EFO_POLLING_MAX_ATTEMPTS, EFO_POLLING_INTERVAL

import structlog

logger = structlog.get_logger(__name__)


WEB_PRINT_KEY = "WebPrint"
MOCK_WEB_PRINT_KEY = "MockWebPrint"
DOT_FEC_KEY = "DotFEC"
MOCK_DOT_FEC_KEY = "MockDotFEC"
SUBMISSION_MANAGERS = {
    WEB_PRINT_KEY: EFOWebPrintSubmitter,
    MOCK_WEB_PRINT_KEY: MockWebPrintSubmitter,
    DOT_FEC_KEY: EFODotFECSubmitter,
    MOCK_DOT_FEC_KEY: MockDotFECSubmitter,
}
SUBMISSION_CLASSES = {
    WEB_PRINT_KEY: WebPrintSubmission,
    MOCK_WEB_PRINT_KEY: WebPrintSubmission,
    DOT_FEC_KEY: UploadSubmission,
    MOCK_DOT_FEC_KEY: UploadSubmission,
}


@shared_task
def create_dot_fec(
    report_id,
    upload_submission_id=None,
    webprint_submission_id=None,
    force_write_to_disk=False,
    file_name=None,
):
    if upload_submission_id:
        submission = UploadSubmission.objects.get(id=upload_submission_id)
        submission.save_state(FECSubmissionState.CREATING_FILE)
    if webprint_submission_id:
        submission = WebPrintSubmission.objects.get(id=webprint_submission_id)
        submission.save_state(FECSubmissionState.CREATING_FILE)
    try:
        file_content = compose_dot_fec(report_id, upload_submission_id)
        if file_name is None:
            file_name = f"{report_id}_{math.floor(datetime.now().timestamp())}.fec"

        if not file_content:
            raise Exception("No file created")
        store_file(file_content, file_name, force_write_to_disk)
        dot_fec_record = DotFEC(report_id=report_id, file_name=file_name)
        dot_fec_record.save()

    except Exception:
        submission.save_error("Creating .FEC failed")
        return None

    if upload_submission_id:
        UploadSubmission.objects.filter(id=upload_submission_id).update(
            dot_fec=dot_fec_record
        )
    if webprint_submission_id:
        WebPrintSubmission.objects.filter(id=webprint_submission_id).update(
            dot_fec=dot_fec_record
        )

    return dot_fec_record.id


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
        submitter = EFODotFECSubmitter() if not mock else MockDotFECSubmitter()
        logger.info(f"Uploading {file_name} to FEC")
        submission_json = submitter.get_submission_json(
            dot_fec_record, e_filing_password, backdoor_code
        )
        submission_response_string = submitter.submit(
            dot_fec_bytes, submission_json, dot_fec_record.report.report_id or None
        )
        submission.save_fec_response(submission_response_string)

        """Poll FEC for status of submission"""
        while (
            submission.fec_status not in FECStatus.get_terminal_statuses_strings() and
            submission.fecfile_polling_attempts < EFO_POLLING_MAX_ATTEMPTS
        ):
            submission.fecfile_polling_attempts += 1
            logger.info(f"Polling status for {submission.fec_submission_id}.")
            logger.info(
                f"Status: {submission.fec_status}, Message: {submission.fec_message}"
            )
            logger.info(
                f"""Attempt #{
                    submission.fecfile_polling_attempts
                } / {EFO_POLLING_MAX_ATTEMPTS}"""
            )
            time.sleep(EFO_POLLING_INTERVAL)
            status_response_string = submitter.poll_status(submission.fec_submission_id)
            submission.save_fec_response(status_response_string)
    except Exception:
        submission.save_error("Failed submitting to FEC")
        return

    new_state = (
        FECSubmissionState.SUCCEEDED
        if submission.fec_status == FECStatus.ACCEPTED.value
        else FECSubmissionState.FAILED
    )
    submission.save_state(new_state)
    return submission.id


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

    """Get email for WebPrint
    There is no way to override this in the UI and we do not
    want to email actual committees, so this is stopgap"""
    email = WEBPRINT_EMAIL

    """Submit to WebPrint"""
    try:
        mock=False
        submission_type_key = WEB_PRINT_KEY if not mock else MOCK_WEB_PRINT_KEY
        submitter = SUBMISSION_MANAGERS[submission_type_key]()
        logger.info(f"Uploading {file_name} to FEC WebPrint")
        submission_response_string = submitter.submit(email, dot_fec_bytes)
        submission.save_fec_response(submission_response_string)

        if not submission.fec_status in FECStatus.get_terminal_statuses_strings():
            logger.info(f"""Submission queued for processing.  Polling every {
                EFO_POLLING_INTERVAL} seconds for {EFO_POLLING_MAX_ATTEMPTS} attempts"""
            )
            """ apply_async()
            The apply_async() method can only take json serializable values as arguments.
            This means we can't pass objects with methods.  To get around that, we pass the
            submission id and a key that we can use to determine the type of the submission.
            This lets us instantiate objects of the correct classes as we need them."""
            return poll_for_fec_response.apply_async(
                [submission.id, submission_type_key, "WebPrint"], countdown=EFO_POLLING_INTERVAL
            )
        else:
            return resolve_final_submission_state(submission)
    except Exception as e:
        logger.error(f"Error before polling: {str(e)}")
        submission.save_error("Failed submitting to WebPrint")
        return resolve_final_submission_state(submission)

@shared_task
def poll_for_fec_response(submission_id, submission_type_key, submission_type):
    try:
        submission = SUBMISSION_CLASSES[submission_type_key].objects.get(id=submission_id)
        submitter = SUBMISSION_MANAGERS[submission_type_key]()

        submission.fecfile_polling_attempts += 1
        logger.info(f"Polling status for {submission.fec_submission_id}.")
        logger.info(
            f"Status: {submission.fec_status}, Message: {submission.fec_message}"
        )
        logger.info(
            f"""Submission Polling - Attempt {
                submission.fecfile_polling_attempts
            } / {EFO_POLLING_MAX_ATTEMPTS}"""
        )
        status_response_string = submitter.poll_status(
            submission.fec_batch_id, submission.fec_submission_id
        )
        submission.save_fec_response(status_response_string)
        if (
            submission.fec_status in FECStatus.get_terminal_statuses_strings() or
            submission.fecfile_polling_attempts >= EFO_POLLING_MAX_ATTEMPTS
        ):
            if submission.fecfile_polling_attempts >= EFO_POLLING_MAX_ATTEMPTS:
                logger.warning("POLLING ATTEMPTS EXCEEDED")
            return resolve_final_submission_state(submission)
        else:
            return poll_for_fec_response.apply_async(
                [submission_id, submission_type_key, submission_type], countdown=EFO_POLLING_INTERVAL
            )
    except Exception as e:
        logger.error(f"Error in polling: {str(e)}")
        submission.save_error(f"Failed submitting to {submission_type}")
        return resolve_final_submission_state(submission)
    
def resolve_final_submission_state(submission):
    new_state = (
        FECSubmissionState.SUCCEEDED
        if submission.fec_status == FECStatus.COMPLETED.value
        else FECSubmissionState.FAILED
    )
    submission.save_state(new_state)
    return submission.id
