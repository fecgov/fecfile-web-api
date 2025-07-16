import copy
import json
from uuid import uuid4 as uuid
from zeep import Client
from types import SimpleNamespace
from fecfiler.web_services.models import FECStatus, BaseSubmission
from fecfiler.settings import (
    EFO_FILING_API,
    EFO_FILING_API_KEY,
    FEC_AGENCY_ID,
    MOCK_EFO_FILING,
)
import structlog

logger = structlog.get_logger(__name__)


class EFODotFECSubmitter():
    """Submitter class for submitting .FEC files to EFO's webload service"""

    def __init__(self) -> None:
        if MOCK_EFO_FILING:
            self.force_mock()
            self.mock_responder = MockDotFECResponse()
        else:
            self.fec_soap_client = Client(
                f"{EFO_FILING_API}/webload/services/upload?wsdl"
            )

    def force_mock(self):
        """Force the submitter to use mock responses"""
        self.mock = True

    def get_submission_json(self, dot_fec_record, e_filing_password, backdoor_code=None):
        """Generate json payload for submission and log it"""
        json_obj = {
            "committee_id": dot_fec_record.report.committee_account.committee_id,
            "password": e_filing_password,
            "api_key": EFO_FILING_API_KEY,
            "email_1": dot_fec_record.report.confirmation_email_1,
            "email_2": dot_fec_record.report.confirmation_email_2,
            "agency_id": FEC_AGENCY_ID,
            "wait": False,
        }
        if dot_fec_record.report.report_id:
            json_obj["amendment_id"] = dot_fec_record.report.report_id
            if backdoor_code:
                json_obj["amendment_id"] += backdoor_code
        self.log_submission_json(json_obj, dot_fec_record, backdoor_code)
        return json.dumps(json_obj)

    def log_submission_json(self, json_obj, dot_fec_record, backdoor_code):
        copy_json_obj = copy.deepcopy(json_obj)
        copy_json_obj.pop("password", None)
        copy_json_obj.pop("api_key", None)
        if "amendment_id" in copy_json_obj and backdoor_code:
            copy_json_obj["amendment_id"] = dot_fec_record.report.report_id + "xxxxx"
        logger.info(f"submission json: {json.dumps(copy_json_obj)}")

    def submit(self, dot_fec_bytes, json_payload, fec_report_id=None):
        if self.mock:
            response = self.mock_responder.processing()
        else:
            response = self.fec_soap_client.service.upload(
                json_payload, dot_fec_bytes
            )

        response_obj = json.loads(response, object_hook=lambda d: SimpleNamespace(**d))
        if response_obj.status == FECStatus.ACCEPTED.value:
            logger.info(f"FEC upload successful: {response}")
        elif response_obj.status == FECStatus.PROCESSING.value:
            logger.info(f"FEC upload processing: {response}")
        else:
            logger.error(f"FEC upload failed: {response}")
        return response

    def poll_status(self, submission: BaseSubmission):
        if self.mock:
            response = self.mock_responder.accepted()
        else:
            response = self.fec_soap_client.service.status(submission.fec_submission_id)

        logger.debug(f"FEC polling response: {response}")
        return response


class MockDotFECResponse():
    """Mock responses from FEC webload service"""

    def accepted(self):
        return json.dumps(
            {
                "submission_id": "fake_submission_id",
                "status": FECStatus.ACCEPTED.value,
                "message": "We didn't really send anything to FEC",
                "report_id": str(uuid()),
            }
        )

    def processing(self):
        return json.dumps(
            {
                "submission_id": "fake_submission_id",
                "status": FECStatus.PROCESSING.value,
                "message": "We didn't really send anything to FEC",
                "report_id": str(uuid()),
            }
        )
