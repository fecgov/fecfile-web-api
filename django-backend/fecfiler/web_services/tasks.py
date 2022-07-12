from celery import shared_task
from fecfiler.f3x_summaries.models import F3XSummary
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


@shared_task
def create_dot_fec(report_id):
    logger.info(f"creating .FEC for report: {report_id}")
    try:
        return serialize_f3x_summary(report_id)
    except Exception as error:
        logger.error(f"failed to create .FEC for report {report_id}: {str(error)}")
