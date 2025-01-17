from django.conf import settings
import structlog
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import connection
from fecfiler.celery import debug_task
from fecfiler.settings import SYSTEM_STATUS_CACHE_BACKEND, SYSTEM_STATUS_CACHE_AGE
import json
import redis

if settings.FLAG__COMMITTEE_DATA_SOURCE == "MOCKED":
    redis_instance = redis.Redis.from_url(settings.MOCK_OPENFEC_REDIS_URL)
elif SYSTEM_STATUS_CACHE_BACKEND:
    redis_instance = redis.Redis.from_url(SYSTEM_STATUS_CACHE_BACKEND)
else:
    raise SystemError("SYSTEM_STATUS_CACHE_BACKEND is not set")

CELERY_STATUS = "CELERY_STATUS"
DATABASE_STATUS = "DATABASE_STATUS"
SCHEDULER_STATUS = "SCHEDULER_STATUS"


logger = structlog.get_logger(__name__)


class SystemStatusViewSet(viewsets.ViewSet):
    """
    A viewset that provides actions to check the status of the system

    The pattern here is that we check the cache for the status of some component.
    If the cache is empty, we flag it with a `{}` and then process the status.
    When the status has been determined, we update the cache with the result.
    Whether the status comes from the cache or is determined on the fly, we return it.

    The `{}` protects us from someone maliciously calling the endpoint to bog down the
    system.  The side effect of that is that if you call the endpoint again before the
    original request completes, you'll get the 503 response.  Calling the endpoint
    multiple times rapidly is not a valid use case, so this is acceptable.

    TODO: It would be ideal to have a scheduled task updating the cache rather than
    the api request If we integrate something like Celery Beat, we could drastically
    reduce the complexity of these endpoints to simply return the cache value.
    """

    @action(
        detail=False,
        methods=["get"],
        url_path="celery-status",
        permission_classes=[],
    )
    def celery_status(self, request):
        """
        Check the status of the celery queue
        Get the status from the cache if it exists, otherwise update the cache
        """
        celery_status = get_redis_value(CELERY_STATUS)

        if celery_status is None:
            celery_status = update_status_cache(CELERY_STATUS, get_celery_status)

        if celery_status.get("celery_is_running"):
            return Response({"status": "celery is completing tasks"})
        return Response(
            {"status": "celery queue is not circulating"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="scheduler-status",
        permission_classes=[],
    )
    def scheduler_status(self, request):
        """
        Check the status of the celery beat queue
        Get the status from the cache if it exists, otherwise update the cache
        """
        scheduler_status = get_redis_value(SCHEDULER_STATUS)

        if scheduler_status is None:
            scheduler_status = update_status_cache(SCHEDULER_STATUS, get_scheduler_status)

        if scheduler_status.get("scheduler_is_running"):
            return Response({"status": "scheduler is completing tasks"})
        return Response(
            {"status": "scheduler queue is not circulating"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="database-status",
        permission_classes=[],
    )
    def database_status(self, request):
        """
        Check the status of the celery queue
        Get the status from the cache if it exists, otherwise update the cache
        """
        db_status = get_redis_value(DATABASE_STATUS)

        if db_status is None:
            db_status = update_status_cache(DATABASE_STATUS, get_database_status)

        if db_status.get("database_is_running"):
            return Response({"status": "database is running"})
        return Response(
            {"status": "cannot connect to database"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
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


def get_scheduler_status():
    """
    Run a debug task and wait form it to complete (for 30s max)
    If the task completes, the queue is being circulated
    """

    return {"scheduler_is_running": redis_instance.get("scheduler_status") is not None}


def update_status_cache(key, method):
    """
    First set the cache value to an empty dictionary to indicate that the status is
    being checked.  Then run the method to get the status and update the cache with
    the result. The empty dictionary value keeps us from checking the status multiple
    times if the cache expires.
    """
    redis_instance.set(key, json.dumps({}), ex=SYSTEM_STATUS_CACHE_AGE)
    status = method()
    redis_instance.set(key, json.dumps(status), ex=SYSTEM_STATUS_CACHE_AGE)
    return status


def get_redis_value(key):
    """
    Get value from redis and parse the json.
    If they value is falsy ("", None), return None
    """
    value = redis_instance.get(key)
    return json.loads(value) if value else None
