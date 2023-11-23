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
from fecfiler.web_services.dot_fec.dot_fec_submitter import DotFECSubmitter
from fecfiler.web_services.dot_fec.web_print_submitter import WebPrintSubmitter
from .web_service_storage import get_file_bytes, store_file
from fecfiler.settings import WEBPRINT_EMAIL, FEC_FILING_API

import logging

logger = logging.getLogger(__name__)


@shared_task
def create_dot_fec(
    report_id,
    upload_submission_id=None,
    webprint_submission_id=None,
    force_write_to_disk=False,
):
    if upload_submission_id:
        submission = UploadSubmission.objects.get(id=upload_submission_id)
        submission.save_state(FECSubmissionState.CREATING_FILE)
    if webprint_submission_id:
        submission = WebPrintSubmission.objects.get(id=webprint_submission_id)
        submission.save_state(FECSubmissionState.CREATING_FILE)
    try:
        file_content = compose_dot_fec(report_id, upload_submission_id)
        file_name = f"{report_id}_{math.floor(datetime.now().timestamp())}.fec"

        if not file_content or not file_name:
            raise Exception("No file created")
        store_file(file_content, file_name, force_write_to_disk)
        dot_fec_record = DotFEC(report_id=report_id, file_name=file_name)
        dot_fec_record.save()

    except Exception as e:
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
    api=None,
    force_read_from_disk=False,
    backdoor_code=None,
):
    logger.info(f"FEC API: {FEC_FILING_API}")
    logger.info(f"api submitter: {api}")
    submission = UploadSubmission.objects.get(id=submission_record_id)
    submission.save_state(FECSubmissionState.SUBMITTING)

    """Get Password"""
    if not e_filing_password:
        submission.save_error("No E-Filing Password provided")
        return

    """Get .FEC file bytes"""
    dot_fec_record = DotFEC.objects.get(id=dot_fec_id)
    file_name = dot_fec_record.file_name
    try:
        dot_fec_bytes = get_file_bytes(file_name, force_read_from_disk)
    except Exception:
        submission.save_error("Could not retrieve .FEC bytes")
        return

    """Submit to FEC"""
    try:
        submitter = DotFECSubmitter(api)
        logger.info(f"Uploading {file_name} to FEC")
        submission_json = submitter.get_submission_json(
            dot_fec_record, e_filing_password, backdoor_code
        )
        submission_response_string = submitter.submit(
            dot_fec_bytes, submission_json, dot_fec_record.report.report_id or None
        )
        submission.save_fec_response(submission_response_string)

        submission.save_error("HIT")
        return

        """Poll FEC for status of submission"""
        # TODO: add timeout?
        while submission.fec_status not in FECStatus.get_terminal_statuses_strings():
            logger.info(f"Polling status for {submission.fec_submission_id}.")
            logger.info(
                f"Status: {submission.fec_status}, Message: {submission.fec_message}"
            )
            time.sleep(2)
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
    dot_fec_id,
    submission_record_id,
    api=None,
    force_read_from_disk=False,
):
    logger.info(f"FEC API: {FEC_FILING_API}")
    logger.info(f"api submitter: {api}")
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
    submitter = WebPrintSubmitter(api)
    logger.info(f"Uploading {file_name} to FEC WebPrint")
    submission_response_string = submitter.submit(email, dot_fec_bytes)
    submission.save_fec_response(submission_response_string)

    """Poll FEC for status of submission"""
    # TODO: add timeout?
    while submission.fec_status not in FECStatus.get_terminal_statuses_strings():
        logger.info(f"Polling status for {submission.fec_submission_id}.")
        logger.info(
            f"Status: {submission.fec_status}, Message: {submission.fec_message}"
        )
        time.sleep(2)
        status_response_string = submitter.poll_status(
            submission.batch_id, submission.fec_submission_id
        )
        submission.save_fec_response(status_response_string)

    new_state = (
        FECSubmissionState.SUCCEEDED
        if submission.fec_status == FECStatus.COMPLETED.value
        else FECSubmissionState.FAILED
    )
    submission.save_state(new_state)
    return submission.id
