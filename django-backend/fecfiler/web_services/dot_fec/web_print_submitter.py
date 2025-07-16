import json
from uuid import uuid4 as uuid
from types import SimpleNamespace
from zeep import Client
from fecfiler.web_services.models import FECStatus, BaseSubmission
from fecfiler.settings import (
    EFO_FILING_API,
    EFO_FILING_API_KEY,
    MOCK_EFO_FILING,
)

import structlog

logger = structlog.get_logger(__name__)


class EFOWebPrintSubmitter():
    """Submitter class for submitting .FEC files to EFO's web print service"""

    def __init__(self):
        if MOCK_EFO_FILING:
            self.force_mock()
            self.mock_responder = MockWebPrintResponse()
        else:
            self.fec_soap_client = Client(
                f"{EFO_FILING_API}/webprint/services/print?wsdl"
            )

    def force_mock(self):
        """Force the submitter to use mock responses"""
        self.mock = True

    def submit(self, email, dot_fec_bytes):
        if self.mock:
            response = self.mock_responder.completed()
        else:
            response = self.fec_soap_client.service.print(
                EFO_FILING_API_KEY, email, dot_fec_bytes
            )

        response_obj = json.loads(response, object_hook=lambda d: SimpleNamespace(**d))
        if response_obj.status != FECStatus.ACCEPTED.value:
            logger.error(f"FEC upload failed: {response}")
        else:
            logger.info(f"FEC upload successful: {response}")
        return response

    def poll_status(self, submission: BaseSubmission):
        if self.mock:
            response = self.mock_responder.completed()
        else:
            response = self.fec_soap_client.service.status(
                getattr(submission, "fec_batch_id", None), submission.fec_submission_id
            )

        logger.debug(f"FEC polling response: {response}")
        return response


class MockWebPrintResponse():
    """Mock responses from a web print service"""

    def completed(self):
        """return an accepted message without reaching out to api"""
        return json.dumps(
            {
                "status": FECStatus.COMPLETED.value,
                "image_url": "https://www.fec.gov/static/img/seal.svg",
                "message": "This did not really come from FEC",
                "submission_id": str(uuid()),
                "batch_id": 123,
            }
        )
