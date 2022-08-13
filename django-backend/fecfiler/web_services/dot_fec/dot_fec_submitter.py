import json
from uuid import uuid4 as uuid
from zeep import Client
from fecfiler.web_services.models import FECStatus
from fecfiler.settings import (
    FEC_FILING_API_KEY,
    FILE_AS_TEST_COMMITTEE,
    TEST_COMMITTEE_PASSWORD,
    FEC_AGENCY_ID,
)

import logging

logger = logging.getLogger(__name__)


class DotFECSubmitter:
    fec_soap_client = None

    def __init__(self, api):
        if api:
            self.fec_soap_client = Client(f"{api}/webload/services/upload?wsdl")

    def get_submission_json(self, dot_fec_record, e_filing_password):
        return json.dumps(
            {
                "committee_id": FILE_AS_TEST_COMMITTEE
                or dot_fec_record.report.committee_account.committee_id,
                "password": (
                    TEST_COMMITTEE_PASSWORD
                    if FILE_AS_TEST_COMMITTEE
                    else e_filing_password
                ),
                "api_key": FEC_FILING_API_KEY,
                "email_1": dot_fec_record.report.confirmation_email_1,
                "email_2": dot_fec_record.report.confirmation_email_2,
                "agency_id": FEC_AGENCY_ID,
                "wait": False,
            }
        )

    def submit(self, dot_fec_bytes, json_payload):
        response = ""
        if self.fec_soap_client:
            response = self.fec_soap_client.service.upload(json_payload, dot_fec_bytes)
        else:
            """return an accepted message without reaching out to api"""
            response = json.dumps(
                {
                    "submission_id": "fake_submission_id",
                    "status": FECStatus.ACCEPTED.value,
                    "message": "We didn't really send anything to FEC",
                    "report_id": str(uuid()),
                }
            )
        logger.debug("FEC upload response: {response}")
        return response

    def poll_status(self, submission_id):
        response = ""
        if self.fec_soap_client:
            response = self.fec_soap_client.service.status(submission_id)
        else:
            """return an accepted message without reaching out to api"""
            response = json.dumps(
                {
                    "submission_id": "fake_submission_id",
                    "status": FECStatus.ACCEPTED.value,
                    "message": "We didn't really send anything to FEC",
                    "report_id": str(uuid()),
                }
            )
        logger.debug(f"FEC polling response: {response}")
        return response
