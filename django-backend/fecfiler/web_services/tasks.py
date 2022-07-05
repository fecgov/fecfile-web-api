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
F3X_NUMBER_OF_COLUMNS = reduce(
    lambda last_index, index: max(last_index, index), F3X_COLUMNS.keys(), 0
)
SERIALIZERS = {
    models.BooleanField: lambda b: "X" if b else "",
    models.DateField: lambda d: d.isoformat(),
    models.ForeignKey: lambda fo, fk: 

}


@shared_task
def create_dot_fec(report_id):
    f3x_summary_result = F3XSummary.objects.filter(id=report_id)
    if f3x_summary_result.exists():
        logger.info(f"creating .FEC for report: {report_id}")
        f3x_summary = f3x_summary_result.first()
        [
            getattr(f3x_summary, F3X_COLUMNS[column_index], None)
            for column_index in range(F3X_NUMBER_OF_COLUMNS)
        ]
    else:
        logger.error(f"report: {report_id} not found")
