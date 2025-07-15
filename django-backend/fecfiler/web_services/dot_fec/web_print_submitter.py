import json
from uuid import uuid4 as uuid
from abc import ABC, abstractmethod
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


class WebPrintSubmitter(ABC):
    """Abstract submitter class for submitnig .FEC files to a web print service"""

    @abstractmethod
    def submit(self, email, dot_fec_bytes):
        pass

    @abstractmethod
    def poll_status(self, submission: BaseSubmission):
        pass


class EFOWebPrintSubmitter(WebPrintSubmitter):
    """Submitter class for submitting .FEC files to EFO's web print service"""

    def __init__(self):
        if MOCK_EFO_FILING:
            self.mock = True
            self.mock_submitter = MockWebPrintSubmitter()
        else:
            self.fec_soap_client = Client(
                f"{EFO_FILING_API}/webprint/services/print?wsdl"
            )

    def submit(self, email, dot_fec_bytes):
        if self.mock:
            response = self.mock_submitter.submit(email, dot_fec_bytes)
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
            response = self.mock_submitter.poll_status(submission)
        else:
            response = self.fec_soap_client.service.status(
                getattr(submission, "fec_batch_id", None), submission.fec_submission_id
            )

        logger.debug(f"FEC polling response: {response}")
        return response


class MockWebPrintSubmitter(WebPrintSubmitter):
    """Submitter class for mocking a response from a web print service"""

    def submit(self, email, dot_fec_bytes):
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

    def poll_status(self, submission: BaseSubmission):
        return json.dumps(
            {
                "status": FECStatus.COMPLETED.value,
                "image_url": "https://www.fec.gov/static/img/seal.svg",
                "message": "This did not really come from FEC",
                "submission_id": str(uuid()),
                "batch_id": 123,
            }
        )
