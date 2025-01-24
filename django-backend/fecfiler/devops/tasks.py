from django.db import connection
from celery import shared_task
from fecfiler.celery import debug_task
from .utils.redis_utils import set_redis_value
from fecfiler.settings import SYSTEM_STATUS_CACHE_AGE
import structlog

logger = structlog.get_logger(__name__)


SCHEDULER_STATUS = "SCHEDULER_STATUS"


@shared_task
def get_database_connections():

    column_labels = (
        "total_connections",
        "non_idle_connections",
        "max_connections",
        "connections_utilization_pctg",
    )

    sql = """
        SELECT
        A.total_connections::text AS {},
        A.non_idle_connections::text AS {},
        B.max_connections::text AS {},
        ROUND(
            100 * (A.total_connections::numeric / B.max_connections::numeric), 2)::text
            AS {}
        FROM
        (SELECT count(1) AS total_connections,
         SUM(CASE WHEN state!='idle' THEN 1 ELSE 0 END) AS non_idle_connections
         FROM pg_stat_activity) A,
        (SELECT setting AS max_connections FROM pg_settings
         WHERE name='max_connections') B;
        """.format(
        *column_labels
    )

    with connection.cursor() as cursor:
        cursor.execute(sql)
        results = cursor.fetchall()

    results_dict = {"results": dict(zip(column_labels, row)) for row in results}
    logger.info(results_dict)
    set_redis_value(
        SCHEDULER_STATUS, {"scheduler_is_running": True}, age=SYSTEM_STATUS_CACHE_AGE
    )


def get_database_status():
    """
    Query the pg_stat_activity table to look for our current database.
    If we find a row, we can be confident the database is at least running.
    This doesn't give us a lot of information about the health of the database,
    but it's sufficient to warn us if it's down.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "select * from pg_stat_activity where datname = current_database()"
        )
        status_data = cursor.fetchone()
    return {"database_is_running": status_data is not None}


def get_celery_status():
    """
    Run a debug task and wait form it to complete (for 30s max)
    If the task completes, the queue is being circulated
    """
    # rigging this to be true because we can't turn off the pingdom check.
    # it seems like this celery task is locking the queue somehow.  will
    # need to investigate further.
    # return {"celery_is_running": True}
    return {"celery_is_running": debug_task.delay().wait(timeout=30, interval=1)}
