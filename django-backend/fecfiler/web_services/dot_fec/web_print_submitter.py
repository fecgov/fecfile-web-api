import json
from uuid import uuid4 as uuid
from zeep import Client
from fecfiler.web_services.models import FECStatus
from fecfiler.settings import FEC_FILING_API_KEY

import logging

logger = logging.getLogger(__name__)


class WebPrintSubmitter:
    fec_soap_client = None

    def __init__(self, api):
        if api:
            self.fec_soap_client = Client(f"{api}/webprint/services/print?wsdl")

    def submit(self, email, dot_fec_bytes):
        response = ""
        if self.fec_soap_client:
            response = self.fec_soap_client.service.print(
                FEC_FILING_API_KEY, email, dot_fec_bytes
            )
        else:
            """return an accepted message without reaching out to api"""
            response = json.dumps(
                {
                    "status": FECStatus.COMPLETED.value,
                    "image_url": "https://www.fec.gov/static/img/seal.svg",
                    "message": "This did not really come from FEC",
                    "submission_id": str(uuid()),
                    "batch_id": 123,
                }
            )
        logger.debug("FEC upload response: {response}")
        return response

    def poll_status(self, batch_id, submission_id):
        response = ""
        if self.fec_soap_client:
            response = self.fec_soap_client.service.status(batch_id, submission_id)
        else:
            """return an accepted message without reaching out to api"""
            response = json.dumps(
                {
                    "status": FECStatus.COMPLETED.value,
                    "image_url": "https://www.fec.gov/static/img/seal.svg",
                    "message": "This did not really come from FEC",
                    "submission_id": str(uuid()),
                    "batch_id": 123,
                }
            )
        logger.debug(f"FEC polling response: {response}")
        return response
