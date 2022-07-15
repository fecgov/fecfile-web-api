from celery import shared_task
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.scha_transactions.models import SchATransaction
from django.core.exceptions import ObjectDoesNotExist
from .dot_fec_serializer import serialize_model_instance

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
    transaction_type = getattr(transaction, "transaction_type_identifier")
    return serialize_model_instance(transaction_type, SchATransaction, transaction)


def serialize_transactions(transactions):
    if transactions.exists():
        return [serialize_transaction(transaction) for transaction in transactions]
    return []


@shared_task
def create_dot_fec(report_id):
    logger.info(f"creating .FEC for report: {report_id}")
    try:
        f3x_summary_row = serialize_f3x_summary(report_id)
        transactions = SchATransaction.objects.filter(report_id_id=report_id)
        transaction_rows = serialize_transactions(transactions)
        logger.info("Serialized Report:")
        logger.info(f3x_summary_row)
        for transaction in transaction_rows:
            logger.info(transaction)
    except Exception as error:
        logger.error(f"failed to create .FEC for report {report_id}: {str(error)}")
