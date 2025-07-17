import json
from uuid import uuid4 as uuid
from abc import ABC, abstractmethod
from types import SimpleNamespace
from zeep import Client
from fecfiler.web_services.models import FECStatus, BaseSubmission
from fecfiler.settings import (
    EFO_FILING_API,
    EFO_FILING_API_KEY,
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

    def __init__(self, mock=False):
        if mock:
            self.mock = True
            self.mock_submitter = MockWebPrintResponse()
        else:
            self.fec_soap_client = Client(
                f"{EFO_FILING_API}/webprint/services/print?wsdl"
            )

    def submit(self, email, dot_fec_bytes):
        if self.mock:
            response = self.mock_submitter.processing()
        else:
            response = self.fec_soap_client.service.print(
                EFO_FILING_API_KEY, email, dot_fec_bytes
            )

        response_obj = json.loads(response, object_hook=lambda d: SimpleNamespace(**d))
        if response_obj.status != FECStatus.COMPLETED.value:
            logger.error(f"FEC upload failed: {response}")
        else:
            logger.info(f"FEC upload successful: {response}")
        return response

    def poll_status(self, submission: BaseSubmission):
        if self.mock:
            response = self.mock_submitter.completed()
        else:
            response = self.fec_soap_client.service.status(
                getattr(submission, "fec_batch_id", None), submission.fec_submission_id
            )

        logger.debug(f"FEC polling response: {response}")
        return response


class MockWebPrintResponse:
    """Mock response for web print service"""

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

    def processing(self):
        return json.dumps(
            {
                "status": FECStatus.PROCESSING.value,
                "image_url": "https://www.fec.gov/static/img/seal.svg",
                "message": "This did not really come from FEC",
                "submission_id": str(uuid()),
                "batch_id": 123,
            }
        )
