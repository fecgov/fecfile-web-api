import logging

# from functools import lru_cache
from django.db import connection

# from fecfiler.core.views import get_entities, NoOPError, superceded_report_id_list
import datetime

logger = logging.getLogger(__name__)


def renew_report_update_date(report_id):
    """
    a helper function to update last update date on report when a transaction is added to deleted
    """
    try:
        logger.debug(
            "renew report last_update_date with report_id:{}".format(report_id)
        )
        _sql = """
        UPDATE public.reports
        SET last_update_date = %s
        WHERE report_id = %s 
        """
        with connection.cursor() as cursor:
            cursor.execute(_sql, [datetime.datetime.now(), report_id])
            if cursor.rowcount == 0:
                raise Exception("Error: updating report update date failed.")
    except:
        raise
