import json
from zeep import Client
from fecfiler.settings import (
    FEC_FILING_API,
    FEC_FILING_API_KEY,
    FILE_AS_TEST_COMMITTEE,
    TEST_COMMITTEE_PASSWORD,
)

import logging

logger = logging.getLogger(__name__)

fec_soap_client = Client(f"{FEC_FILING_API}/webload/services/upload?wsdl")


class BaseSubmitter:
    def get_submission_json(dot_fec_record, e_filing_password):
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
        return "{}"

    def poll_status(self, submission_id):
        return "{}"


class DotFECSubmitter(BaseSubmitter):
    def submit(self, dot_fec_bytes, json_payload):
        return self.fec_soap_client.service.upload(json_payload, dot_fec_bytes)

    def poll_status(self, submission_id):
        return self.fec_soap_client.service.status(submission_id)
