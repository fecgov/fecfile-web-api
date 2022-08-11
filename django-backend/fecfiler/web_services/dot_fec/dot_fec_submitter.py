import json
from urllib import response
from zeep import Client
from fecfiler.settings import (
    FEC_FILING_API,
    FEC_FILING_API_KEY,
    FILE_AS_TEST_COMMITTEE,
    TEST_COMMITTEE_PASSWORD,
)

import logging

logger = logging.getLogger(__name__)


class DotFECSubmitter:
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
                "agency_id": "FEC",
                "wait": False,
            }
        )

    def submit(self, dot_fec_bytes, json_payload):
        if self.fec_soap_client:
            response = self.fec_soap_client.service.upload(json_payload, dot_fec_bytes)
        else:
            response = "{}"
        logger.debug("FEC upload response: {response}")
        return response

    def poll_status(self, submission_id):
        if self.fec_soap_client:
            response = self.fec_soap_client.service.status(submission_id)
        else:
            response = "{}"
        logger.debug(f"FEC polling response: {response}")
        return response
