from django.db import connection
from celery import shared_task
from datetime import datetime, timedelta
from .utils.redis import set_redis_value, get_redis_value
from fecfiler.settings import (
    SYSTEM_STATUS_CACHE_AGE,
    AWS_STORAGE_BUCKET_NAME,
    S3_OBJECTS_MAX_AGE_DAYS,
)
from fecfiler.s3 import S3_SESSION
import structlog
from django.utils import timezone

logger = structlog.get_logger(__name__)


SCHEDULER_STATUS = "SCHEDULER_STATUS"
CELERY_STATUS = "CELERY_STATUS"
DATABASE_STATUS = "DATABASE_STATUS"
LOGGED_DB_SIZE_REDIS_KEY = "LOGGED_DB_SIZE_REDIS_KEY"
LOGGED_S3_SIZE_REDIS_KEY = "LOGGED_S3_SIZE_REDIS_KEY"


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


@shared_task
def size_analysis():

    db_size = check_database_size()
    log_database_size(db_size)

    if S3_SESSION is not None:
        log_s3_bucket_size()


@shared_task
def delete_expired_s3_objects():
    try:
        bucket = S3_SESSION.Bucket(AWS_STORAGE_BUCKET_NAME)
    except Exception as e:
        logger.error(
            "Failed to access S3 bucket",
            bucket_name=AWS_STORAGE_BUCKET_NAME,
            error=str(e),
        )
        return

    object_expiry_datetime = timezone.now() - timedelta(days=S3_OBJECTS_MAX_AGE_DAYS)
    keys_to_delete = [
        {"Key": object.key}
        for object in bucket.objects.all()
        if object is not None and object.last_modified < object_expiry_datetime
    ]
    delete_count = len(keys_to_delete)
    if delete_count > 0:
        logger.info(
            f"Deleting {delete_count} S3 objects older than "
            f"{S3_OBJECTS_MAX_AGE_DAYS} days"
        )
        bucket.delete_objects(Delete={"Objects": keys_to_delete})
    else:
        logger.info(
            f"No S3 objects older than {S3_OBJECTS_MAX_AGE_DAYS} days to clean up"
        )


def check_database_size():
    sql = "SELECT pg_database_size( current_database() );"

    results = None
    with connection.cursor() as cursor:
        cursor.execute(sql)
        results = cursor.fetchall()

    if results is not None:
        return results[0][0]


def log_database_size(current_size_bytes):
    resource_label = "database"
    capacity_gbytes = 1024
    logged_size_redis_key = LOGGED_DB_SIZE_REDIS_KEY
    return log_resource_size(
        resource_label, current_size_bytes, capacity_gbytes, logged_size_redis_key
    )


def log_s3_bucket_size():
    resource_label = "s3_bucket"
    capacity_gbytes = 5000
    logged_size_redis_key = LOGGED_S3_SIZE_REDIS_KEY
    current_size_bytes = 0
    bucket = S3_SESSION.Bucket(AWS_STORAGE_BUCKET_NAME)
    for object in bucket.objects.all():
        current_size_bytes += object.size
    return log_resource_size(
        resource_label, current_size_bytes, capacity_gbytes, logged_size_redis_key
    )


def log_resource_size(
    resource_label,
    current_size_bytes,
    capacity_gbytes,
    logged_size_redis_key,
):
    ngbytes = current_size_bytes / (1024**3)
    pct_full = (ngbytes / capacity_gbytes) * 100

    size_pretty = f"{round(ngbytes, 2)} GB / {capacity_gbytes} GB ({round(pct_full, 2)}%)"

    log_dict = {
        resource_label: {
            "current_size_gb": ngbytes,
            "current_size_pretty": size_pretty,
            "growth": None,
            "est_days_to_full": None,
        }
    }

    timestamp = datetime.now()
    logged_size = get_redis_value(logged_size_redis_key)
    if logged_size is not None:
        logged_nbytes = logged_size[0]
        logged_timestring = logged_size[1]
        logged_timestamp = datetime.strptime(logged_timestring, "%Y%m%d%H%M%S")

        logged_time_delta = timestamp - logged_timestamp
        logged_ngbytes_delta = (current_size_bytes - logged_nbytes) / (1024**3)

        seconds_in_a_day = timedelta(days=1).total_seconds()
        days_since_logged = logged_time_delta.total_seconds() / seconds_in_a_day
        logged_time_delta_pretty = round(days_since_logged, 3)

        size_delta_pretty = round(logged_ngbytes_delta, 5)
        log_dict[resource_label][
            "growth"
        ] = f"{size_delta_pretty} GB in the last {logged_time_delta_pretty} days"

        if days_since_logged >= 1 and logged_ngbytes_delta > 0:
            gb_per_day = logged_ngbytes_delta / days_since_logged
            space_remaining = capacity_gbytes - ngbytes
            days_till_full = space_remaining / gb_per_day
            days_till_full_pretty = round(days_till_full, 2)
            log_dict[resource_label]["est_days_to_full"] = days_till_full_pretty
    else:
        set_redis_value(
            logged_size_redis_key,
            [current_size_bytes, timestamp.strftime("%Y%m%d%H%M%S")],
            None,
        )

    logger.info(log_dict)
    return log_dict


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
