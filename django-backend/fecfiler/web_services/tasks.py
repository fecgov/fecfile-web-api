from datetime import datetime
import math
import time
from celery import shared_task
from fecfiler.web_services.models import (
    DotFEC,
    UploadSubmission,
    UploadSubmissionState,
    FECStatus,
)
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_dot_fec
from fecfiler.web_services.dot_fec.dot_fec_submitter import DotFECSubmitter
from .web_service_storage import get_file_bytes, store_file

import logging

logger = logging.getLogger(__name__)


@shared_task
def create_dot_fec(report_id, submission_record_id, force_write_to_disk=False):
    if submission_record_id:
        submission = UploadSubmission.objects.get(id=submission_record_id)
        submission.save_state(UploadSubmissionState.CREATING_FILE)
    file_content = compose_dot_fec(report_id, submission_record_id)
    file_name = f"{report_id}_{math.floor(datetime.now().timestamp())}.fec"
    if not file_content or not file_name:
        if submission:
            submission.save_error("Creating .FEC failed")
        return None
    store_file(file_content, file_name, force_write_to_disk)
    dot_fec_record = DotFEC(report_id=report_id, file_name=file_name)
    dot_fec_record.save()

    return dot_fec_record.id


@shared_task
def submit_to_fec(dot_fec_id, submission_record_id, e_filing_password, api=None):
    submission = UploadSubmission.objects.get(id=submission_record_id)
    submission.save_state(UploadSubmissionState.SUBMITTING)

    """Get Password"""
    if not e_filing_password:
        submission.save_error("No E-Filing Password provided")
        return

    """Get .FEC file bytes"""
    dot_fec_record = DotFEC.objects.get(id=dot_fec_id)
    file_name = dot_fec_record.file_name
    try:
        dot_fec_bytes = get_file_bytes(file_name)
    except Exception:
        submission.save_error("Could not retrieve .FEC bytes")
        return

    """Submit to FEC"""
    submitter = DotFECSubmitter(api)
    logger.info(f"Uploading {file_name} to FEC")
    submission_json = submitter.get_submission_json(dot_fec_record, e_filing_password)
    submission_response_string = submitter.submit(dot_fec_bytes, submission_json)
    submission.save_fec_response(submission_response_string)

    """Poll FEC for status of submission"""
    # TODO: add timeout?
    while submission.fec_status not in ["ACCEPTED", "REJECTED"]:
        logger.info(f"Polling status for {submission.fec_submission_id}.")
        logger.info(
            f"Status: {submission.fec_status}, Message: {submission.fec_message}"
        )
        time.sleep(2)
        status_response_string = submitter.poll_status(submission.fec_submission_id)
        submission.save_fec_response(status_response_string)

    new_state = (
        UploadSubmissionState.SUCCEEDED
        if submission.fec_status == FECStatus.ACCEPTED.value
        else UploadSubmissionState.FAILED
    )
    submission.save_state(new_state)
    return submission.id
