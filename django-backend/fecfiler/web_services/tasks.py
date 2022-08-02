from datetime import datetime
import math
from celery import shared_task
from fecfiler.web_services.models import DotFEC
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_dot_fec
from .web_service_storage import store_file, get_file

import logging

logger = logging.getLogger(__name__)


@shared_task
def create_dot_fec(report_id, force_write_to_disk=False):
    file_content = compose_dot_fec(report_id)
    file_name = f"{report_id}_{math.floor(datetime.now().timestamp())}.fec"
    if not file_content or not file_name:
        return None
    store_file(file_content, file_name, force_write_to_disk)
    dot_fec_record = DotFEC(report_id=report_id, file_name=file_name)
    dot_fec_record.save()

    return file_name


@shared_task
def submit_to_fec(dot_fec_id, force_write_to_disk=False):
    dot_fec_record = DotFEC.objects.get(dot_fec_record)
    file_name = dot_fec_record.first().file_name
    file = get_file(file_name)
    logger.debug(f"Retrieved .FEC: {file_name}")
    logger.debug(f"do something with {file}")

    return file_name
