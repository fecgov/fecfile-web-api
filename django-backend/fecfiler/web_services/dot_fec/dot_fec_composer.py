from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.scha_transactions.models import SchATransaction
from django.core.exceptions import ObjectDoesNotExist
from .dot_fec_serializer import serialize_header, serialize_model_instance, CRLF_STR

import logging

logger = logging.getLogger(__name__)


def compose_f3x_summary(report_id):
    f3x_summary_result = F3XSummary.objects.filter(id=report_id)
    if f3x_summary_result.exists():
        logger.info(f"composing f3x summary: {report_id}")
        return f3x_summary_result.first()
    else:
        raise ObjectDoesNotExist(f"report: {report_id} not found")


def compose_transactions(report_id):
    transactions = SchATransaction.objects.filter(report_id=report_id)
    if transactions.exists():
        logger.info(f"composing transactions: {report_id}")
        return transactions
    else:
        logger.info(f"no transactions found for report: {report_id}")
        return []


def compose_header():
    return {
        "record_type": "HDR",
        "ef_type": "FEC",
        "fec_version": "8.4",
        "soft_name": "FECFile Online",
        "soft_ver": "0.0.1",
        "rpt_id": None,
        "rpt_number": None,
        "hdrcomment": None,
    }


def add_row_to_content(content, row):
    """Returns new string with `row` appended to `content` and adds .FEC line breaks
    Args:
        content (string): .FEC content to add row to
        row (string): Row that will be appended to `content`
    """
    return (content or "") + str(row) + CRLF_STR


def compose_dot_fec(report_id):
    logger.info(f"composing .FEC for report: {report_id}")
    try:
        header = compose_header()
        header_row = serialize_header(header)
        logger.debug("Serialized HDR:")
        logger.debug(header_row)
        file_content = add_row_to_content(None, header_row)

        f3x_summary = compose_f3x_summary(report_id)
        f3x_summary_row = serialize_model_instance("F3X", F3XSummary, f3x_summary)
        logger.debug("Serialized Report Summary:")
        logger.debug(f3x_summary_row)
        file_content = add_row_to_content(file_content, f3x_summary_row)

        transactions = compose_transactions(report_id)
        transaction_rows = [
            serialize_model_instance("SchA", SchATransaction, transaction)
            for transaction in transactions
        ]
        for transaction in transaction_rows:
            logger.debug("Serialized Transaction:")
            logger.debug(transaction)
            file_content = add_row_to_content(file_content, transaction)

        return file_content
    except Exception as error:
        logger.error(f"failed to compose .FEC for report {report_id}: {str(error)}")
        raise error
