from django.db import connection
from celery import shared_task
from datetime import datetime, timedelta
from .utils.redis_utils import set_redis_value, get_redis_value
from fecfiler.settings import SYSTEM_STATUS_CACHE_AGE, AWS_STORAGE_BUCKET_NAME
from fecfiler.s3 import S3_SESSION
import structlog

logger = structlog.get_logger(__name__)


SCHEDULER_STATUS = "SCHEDULER_STATUS"
CELERY_STATUS = "CELERY_STATUS"
DATABASE_STATUS = "DATABASE_STATUS"
INITIAL_DB_SIZE = "INITIAL_DB_SIZE"


@shared_task
def get_devops_status_report():
    scheduler_running = {"scheduler_is_running": True}
    set_redis_value(SCHEDULER_STATUS, scheduler_running, age=SYSTEM_STATUS_CACHE_AGE)
    logger.info(scheduler_running)

    celery_running = {"celery_is_running": True}  # If this task runs, celery is working
    set_redis_value(CELERY_STATUS, celery_running, age=SYSTEM_STATUS_CACHE_AGE)
    logger.info(celery_running)

    db_running = check_database_running()
    set_redis_value(DATABASE_STATUS, db_running, age=SYSTEM_STATUS_CACHE_AGE)
    logger.info(db_running)

    db_connections_results = get_database_connections()
    logger.info(db_connections_results)

    db_size = check_database_size()
    log_database_size(db_size)

    log_s3_bucket_size()


def log_s3_bucket_size():
    if S3_SESSION:
        total_size = 0
        bucket = S3_SESSION.Bucket(AWS_STORAGE_BUCKET_NAME)
        for object in bucket.objects.all():
            total_size += object.size
        logger.info("S3 bucket size (MB): " + str(round(total_size / 1024 / 1024, 2)))


def check_database_size():
    sql = "SELECT pg_database_size( current_database() );"

    results = None
    with connection.cursor() as cursor:
        cursor.execute(sql)
        results = cursor.fetchall()

    if results is not None:
        return results[0][0]


def log_database_size(nbytes):
    ngbytes = nbytes / (1024**3)
    capacity = 1024  # in GB
    pct_full = (ngbytes / capacity) * 100

    size_pretty = f"{round(ngbytes, 2)} GB / {capacity} GB ({round(pct_full, 2)}%)"

    log_dict = {
        "db_size_gb": ngbytes,
        "db_size_pretty": size_pretty,
        "db_growth": None,
        "db_est_days_to_full": None,
    }

    timestamp = datetime.now()
    logged_db_size = get_redis_value(INITIAL_DB_SIZE)
    if logged_db_size is not None:
        logged_nbytes = logged_db_size[0]
        logged_timestring = logged_db_size[1]
        logged_timestamp = datetime.strptime(logged_timestring, "%Y%m%d%H%M%S")

        logged_time_delta = timestamp - logged_timestamp
        logged_ngbytes_delta = (nbytes - logged_nbytes) / (1024**3)

        seconds_in_a_day = timedelta(days=1).total_seconds()
        days_since_logged = logged_time_delta.total_seconds() / seconds_in_a_day
        logged_time_delta_pretty = round(days_since_logged, 3)

        size_delta_pretty = round(logged_ngbytes_delta, 5)
        log_dict["db_growth"] = (
            f"{size_delta_pretty} GB in the last {logged_time_delta_pretty} days"
        )

        if days_since_logged >= 1 and logged_ngbytes_delta > 0:
            gb_per_day = logged_ngbytes_delta / days_since_logged
            space_remaining = capacity - ngbytes
            days_till_full = space_remaining / gb_per_day
            days_till_full_pretty = round(days_till_full, 2)
            log_dict["db_est_days_to_full"] = days_till_full_pretty
    else:
        set_redis_value(
            INITIAL_DB_SIZE, [nbytes, timestamp.strftime("%Y%m%d%H%M%S")], None
        )

    logger.info(log_dict)
    return log_dict


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
