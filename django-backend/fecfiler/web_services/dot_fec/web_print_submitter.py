import json
from uuid import uuid4 as uuid
from abc import ABC, abstractmethod
from zeep import Client
from fecfiler.web_services.models import FECStatus
from fecfiler.settings import FEC_FILING_API_KEY, FEC_FILING_API

import structlog

logger = structlog.get_logger(__name__)


class WebPrintSubmitter(ABC):
    """Abstract submitter class for submitnig .FEC files to a web print service"""

    @abstractmethod
    def submit(self, email, dot_fec_bytes):
        pass

    @abstractmethod
    def poll_status(self, batch_id, submission_id):
        pass


class EFOWebPrintSubmitter(WebPrintSubmitter):
    """Submitter class for submitting .FEC files to EFO's web print service"""

    def __init__(self):
        self.fec_soap_client = Client(f"{FEC_FILING_API}/webprint/services/print?wsdl")

    def submit(self, email, dot_fec_bytes):
        response = self.fec_soap_client.service.print(
            FEC_FILING_API_KEY, email, dot_fec_bytes
        )
        logger.debug(f"FEC upload response: {response}")
        return response

    def poll_status(self, batch_id, submission_id):
        response = self.fec_soap_client.service.status(batch_id, submission_id)
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

    def poll_status(self, batch_id, submission_id):
        return json.dumps(
            {
                "status": FECStatus.COMPLETED.value,
                "image_url": "https://www.fec.gov/static/img/seal.svg",
                "message": "This did not really come from FEC",
                "submission_id": str(uuid()),
                "batch_id": 123,
            }
        )
