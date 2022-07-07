from functools import reduce
from celery import shared_task
from fecfiler.f3x_summaries.models import F3XSummary
from fecfile_validate import validate
from django.db import models
import datetime

import logging

logger = logging.getLogger(__name__)

F3X_SCHEMA = validate.get_schema("F3X")
F3X_PROPERTIES = F3X_SCHEMA.get("properties", {}).items()
F3X_COLUMNS = {v.get("fec_spec", {}).get("COL_SEQ", None): k for k, v in F3X_PROPERTIES}
F3X_NUMBER_OF_COLUMNS = max(F3X_COLUMNS.keys())
SERIALIZERS = {
    models.BooleanField: lambda b, o, fn: "X" if b else "",
    models.DateField: lambda d, o, fn: d.isoformat() if d else "",
    models.ForeignKey: lambda fo, o, fn: getattr(o, fn + "_id", ""),
    None: lambda v, o, fn: v or "",
}


def serialize_field(object, field_name, model):
    field = model._meta.get_field(field_name)
    serializer = SERIALIZERS.get(type(field), SERIALIZERS[None])
    return serializer(getattr(object, field_name, None), object, field_name)


def serialize_f3x_summary(report_id):
    f3x_summary_result = F3XSummary.objects.filter(id=report_id)
    if f3x_summary_result.exists():
        logger.info(f"serializing f3x summary: {report_id}")
        f3x_summary = f3x_summary_result.first()
        row = [
            serialize_field(f3x_summary, F3X_COLUMNS[column_index], F3XSummary)
            for column_index in range(1, F3X_NUMBER_OF_COLUMNS)
        ]
        return ",".join(row)
    else:
        raise Exception(f"report: {report_id} not found")


@shared_task
def create_dot_fec(report_id):
    logger.info(f"creating .FEC for report: {report_id}")
    try:
        serialize_f3x_summary(report_id)
    except Exception as error:
        logger.error(f"failed to create .FEC for report {report_id}: {str(error)}")
