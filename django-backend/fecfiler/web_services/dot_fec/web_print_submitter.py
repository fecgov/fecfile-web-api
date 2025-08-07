import json
from uuid import uuid4 as uuid
from abc import ABC, abstractmethod
from zeep import Client
from zeep.plugins import HistoryPlugin
from fecfiler.web_services.models import FECStatus, BaseSubmission
from fecfiler.settings import EFO_FILING_API_KEY, EFO_FILING_API

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
        self.history = HistoryPlugin()
        self.fec_soap_client = Client(
            f"{EFO_FILING_API}/webprint/services/print?wsdl", plugins=[self.history]
        )

    def submit(self, email, dot_fec_bytes):
        response = self.fec_soap_client.service.print(
            EFO_FILING_API_KEY, email, dot_fec_bytes
        )
        logger.debug(f"FEC upload response: {response}")

        # Get the last HTTP response
        http_response = self.history.last_received
        status_code = http_response.status_code if http_response else None
        if status_code != 200:
            raise Exception(f"FEC upload failed with HTTP status code: {status_code}")

        return response

    def poll_status(self, submission: BaseSubmission):
        response = self.fec_soap_client.service.status(
            getattr(submission, "fec_batch_id", None), submission.fec_submission_id
        )
        logger.debug(f"FEC polling response: {response}")

        # Get the last HTTP response
        http_response = self.history.last_received
        status_code = http_response.status_code if http_response else None
        if status_code != 200:
            raise Exception(f"FEC polling failed with HTTP status code: {status_code}")

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
