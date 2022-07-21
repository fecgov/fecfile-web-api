from celery import shared_task
from io import BytesIO
from django.core.files.storage import default_storage
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.scha_transactions.models import SchATransaction
from django.core.exceptions import ObjectDoesNotExist
from .dot_fec_serializer import serialize_model_instance
import boto3
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


session = boto3.session.Session()
s3 = session.resource(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


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
        file_content = str(f3x_summary_row).encode()
        for transaction in transaction_rows:
            logger.info(transaction)
            file_content += str(transaction).encode()

        file_name = f"{report_id}.fec"
        file_content_io = BytesIO(file_content)

        logger.info(f"uploading .FEC to s3 for report: {report_id}")
        s3_object = s3.Object(settings.AWS_STORAGE_BUCKET_NAME, file_name)
        s3_object.put(Body=file_content_io)
        logger.info(f"SUCCESS .FEC was uploaded s3 for report: {report_id}")

    except Exception as error:
        logger.error(f"failed to create .FEC for report {report_id}: {str(error)}")
