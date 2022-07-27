from datetime import datetime
import math
from celery import shared_task
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.scha_transactions.models import SchATransaction
from fecfiler.web_services.models import DotFEC
from django.core.exceptions import ObjectDoesNotExist
from .dot_fec_serializer import add_row_to_fec_str, serialize_model_instance
from .web_service_storage import store_file

import logging

logger = logging.getLogger(__name__)


def serialize_f3x_summary(report_id):
    f3x_summary_result = F3XSummary.objects.filter(id=report_id)
    if f3x_summary_result.exists():
        logger.info(f"serializing f3x summary: {report_id}")
        f3x_summary = f3x_summary_result.first()
        return serialize_model_instance("F3X", F3XSummary, f3x_summary)
    else:
        raise ObjectDoesNotExist(f"report: {report_id} not found")


def serialize_transaction(transaction):
    if not isinstance(transaction, SchATransaction):
        raise TypeError(f"{type(transaction)} is not a transaction")
    logger.info(f"serializing transaction: {transaction.id}")
    return serialize_model_instance("SchA", SchATransaction, transaction)


def serialize_transactions(transactions):
    if transactions.exists():
        return [serialize_transaction(transaction) for transaction in transactions]
    return []


def create_dot_fec_content(report_id):
    logger.info(f"creating .FEC for report: {report_id}")
    try:
        f3x_summary_row = serialize_f3x_summary(report_id)
        transactions = SchATransaction.objects.filter(report_id=report_id)
        transaction_rows = serialize_transactions(transactions)
        logger.info("Serialized Report:")
        logger.info(f3x_summary_row)
        file_content = add_row_to_fec_str(None, f3x_summary_row)
        for transaction in transaction_rows:
            logger.info(transaction)
            file_content = add_row_to_fec_str(file_content, transaction)

        file_name = f"{report_id}_{math.floor(datetime.now().timestamp())}.fec"
        return (file_content, file_name)
    except Exception as error:
        logger.error(f"failed to create .FEC for report {report_id}: {str(error)}")
        return (None, None)


@shared_task
def create_dot_fec(report_id, force_write_to_disk=False):
    file_content, file_name = create_dot_fec_content(report_id)
    if not file_content or not file_name:
        return None
    store_file(file_content, file_name, force_write_to_disk)
    dot_fec_record = DotFEC(report_id=report_id, file_name=file_name)
    dot_fec_record.save()

    return file_name
