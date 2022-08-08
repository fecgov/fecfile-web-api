from datetime import datetime
import math
import json
import time
from zeep import Client
from celery import shared_task
from fecfiler.web_services.models import DotFEC, UploadSubmission
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_dot_fec
from .web_service_storage import store_file, get_file

import logging

logger = logging.getLogger(__name__)

test_fec_upload_client = Client(
    "https://test-efoservices.fec.gov/webload/services/upload?wsdl"
)


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
def submit_to_fec(dot_fec_id, upload_submission_record_id):
    dot_fec_record = DotFEC.objects.get(id=dot_fec_id)
    file_name = dot_fec_record.file_name
    try:
        file = get_file(file_name)
        logger.debug(f"Retrieved .FEC: {file_name}")
        file_bytes = bytearray(file.read(), "utf-8")
        file.close()
        upload_string = json.dumps(
            {
                "committee_id": "C00020057",
                "password": "T3stUpl@ad",
                "api_key": "4ac854dd46c804b96f8fba61c21bfc5a07calHnZ",
                "email_1": "mbasupally.ctr@fec.gov",
                "email_2": "mbasupally.ctr@fec.gov",
                "agency_id": "FEC",
                "wait": False,
            }
        )
        logger.debug(f"uploading {file_name} to FEC {file_bytes}")
        upload_response_string = test_fec_upload_client.service.upload(
            upload_string, file_bytes
        )
        upload_response = json.loads(upload_response_string)
        submission_record = update_submission_status(
            upload_submission_record_id, upload_response
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

    except:
        file.close()
    return file_name


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
