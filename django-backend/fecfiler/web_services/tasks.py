from datetime import datetime
import math
import json
import time
from zeep import Client
from celery import shared_task
from fecfiler.web_services.models import DotFEC, UploadSubmission
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_dot_fec
from .web_service_storage import store_file, get_file
from fecfiler.settings import (
    FEC_FILING_API,
    FEC_FILING_API_KEY,
    FILE_AS_TEST_COMMITTEE,
    TEST_COMMITTEE_PASSWORD,
)

import logging

logger = logging.getLogger(__name__)

test_fec_upload_client = Client(f"{FEC_FILING_API}/webload/services/upload?wsdl")


@shared_task
def create_dot_fec(report_id, force_write_to_disk=False):
    file_content = compose_dot_fec(report_id)
    file_name = f"{report_id}_{math.floor(datetime.now().timestamp())}.fec"
    if not file_content or not file_name:
        return None
    store_file(file_content, file_name, force_write_to_disk)
    dot_fec_record = DotFEC(report_id=report_id, file_name=file_name)
    dot_fec_record.save()

    return dot_fec_record.id


@shared_task
def submit_to_fec(dot_fec_id, upload_submission_record_id, e_filing_password):
    dot_fec_record = DotFEC.objects.get(id=dot_fec_id)

    if not e_filing_password:
        logger.error("Submit to FEC failed, no E-Filing Password provided")
        dot_fec_record.fecfile_task_state = "FAILED"
        dot_fec_record.save()
        return

    dot_fec_record.fecfile_task_state = "SUBMITTING"
    dot_fec_record.save()

    file_name = dot_fec_record.file_name
    try:
        file = get_file(file_name)
        logger.debug(f"Retrieved .FEC: {file_name}")
        file_bytes = bytearray(file.read(), "utf-8")
        file.close()
    except:
        file.close()
        dot_fec_record.fecfile_task_state = "FAILED"
        dot_fec_record.save()
        return

    logger.debug(f"uploading {file_name} to FEC {file_bytes}")
    submission_json = generate_submission_json(
        dot_fec_record.report.committee_account.committee_id,
        e_filing_password,
        dot_fec_record.report.confirmation_email_1,
        dot_fec_record.report.confirmation_email_2,
    )
    upload_response_string = test_fec_upload_client.service.upload(
        submission_json, file_bytes
    )
    logger.debug(f"upload_response: {upload_response_string}")
    submission_record = update_submission_status(
        upload_submission_record_id, json.loads(upload_response_string)
    )

    while submission_record.status not in ["ACCEPTED", "REJECTED"]:
        time.sleep(2)
        status_response_string = test_fec_upload_client.status(
            submission_record.submission_id
        )
        status_response = json.loads(status_response_string)
        submission_record = update_submission_status(
            upload_submission_record_id, status_response
        )
        logger.debug(
            f"Polling status for {submission_record.submission_id}. Status: {submission_record.status}"
        )

    dot_fec_record.fecfile_task_state = (
        "SUCCEEDED" if dot_fec_record.fec_status == "ACCEPTED" else "FAILED"
    )
    dot_fec_record.save()
    return file_name


def generate_submission_json(committee_id, e_filing_password, email_1, email_2):
    return json.dumps(
        {
            "committee_id": FILE_AS_TEST_COMMITTEE or committee_id,
            "password": (
                TEST_COMMITTEE_PASSWORD if FILE_AS_TEST_COMMITTEE else e_filing_password
            ),
            "api_key": FEC_FILING_API_KEY,
            "email_1": email_1,
            "email_2": email_2,
            "agency_id": "FEC",
            "wait": False,
        }
    )


def update_submission_status(upload_submission_record_id, response_json):
    upload_submission_record = UploadSubmission.objects.get(
        id=upload_submission_record_id
    )

    upload_submission_record.submission_id = response_json["submission_id"]
    upload_submission_record.status = response_json["status"]
    upload_submission_record.message = response_json["message"]
    upload_submission_record.fec_report_id = response_json["report_id"]

    upload_submission_record.save()
    return upload_submission_record
