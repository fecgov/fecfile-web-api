from django.db import connection
from celery import shared_task
from fecfiler.celery import debug_task
from datetime import datetime, timezone, timedelta
from .utils.redis_utils import set_redis_value, get_redis_value
from fecfiler.settings import SYSTEM_STATUS_CACHE_AGE
import structlog

logger = structlog.get_logger(__name__)


SCHEDULER_STATUS = "SCHEDULER_STATUS"
INITIAL_DB_SIZE = "INITIAL_DB_SIZE"


@shared_task
def get_database_status_report():
    set_redis_value(
        SCHEDULER_STATUS, {"scheduler_is_running": True}, age=SYSTEM_STATUS_CACHE_AGE
    )

    db_connections_results = get_database_connections()
    logger.info(db_connections_results)

    db_size = get_database_size()
    report_database_size(db_size)


def get_database_size():
    sql = "SELECT pg_database_size( current_database() );"

    results = None
    with connection.cursor() as cursor:
        cursor.execute(sql)
        results = cursor.fetchall()

    if results != None:
        return results[0][0]


def report_database_size(nbytes):
    ngbytes = nbytes / (1024**3)
    capacity = 1024  # in GB
    pct_full = (ngbytes / capacity) * 100

    size_pretty = f"{round(ngbytes, 2)} GB / {capacity} GB ({round(pct_full, 2)}%)"
    logger.info(f"Database Size: {size_pretty}")

    timestamp = datetime.now()
    logged_db_size = get_redis_value(INITIAL_DB_SIZE)
    if logged_db_size is not None:
        logged_nbytes = logged_db_size[0]
        logged_timestring = logged_db_size[1]
        logged_timestamp = datetime.strptime(logged_timestring, '%Y%m%d%H%M%S')

        logged_time_delta = timestamp - logged_timestamp
        logged_ngbytes_delta = (nbytes - logged_nbytes) / (1024 ** 3)

        seconds_in_a_day = timedelta(days=1).total_seconds()
        days_since_logged = logged_time_delta.total_seconds() / seconds_in_a_day
        logged_time_delta_pretty = round(days_since_logged, 2)

        size_delta_pretty = round(logged_ngbytes_delta, 2)
        logger.info(f"""DB has grown {size_delta_pretty} GB in the last {
            logged_time_delta_pretty
        } days""")

        if days_since_logged >= 1 and logged_ngbytes_delta > 0:
            gb_per_day = logged_ngbytes_delta / days_since_logged
            space_remaining = capacity - ngbytes
            days_till_full = space_remaining / gb_per_day
            days_till_full_pretty = round(days_till_full, 2)
            logger.info(f"DB estimated to reach capacity in {days_till_full_pretty} days")
    else:
        set_redis_value(
            INITIAL_DB_SIZE, [nbytes, timestamp.strftime('%Y%m%d%H%M%S')], None
        )



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

    return {"results": dict(zip(column_labels, row)) for row in results}


def check_database_running():
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
