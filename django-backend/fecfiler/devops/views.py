import structlog
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from .tasks import DATABASE_STATUS, CELERY_STATUS, SCHEDULER_STATUS

from .utils.redis_utils import get_redis_value


logger = structlog.get_logger(__name__)


@extend_schema_view(
    celery_status=extend_schema(exclude=True),
    scheduler_status=extend_schema(exclude=True),
    database_status=extend_schema(exclude=True),
    status=extend_schema(exclude=True),
)
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
        celery_status = get_redis_value(CELERY_STATUS, {})

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
        scheduler_status = get_redis_value(SCHEDULER_STATUS, {})

        if scheduler_status is not None:
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
        db_status = get_redis_value(DATABASE_STATUS, {})

        if db_status.get("database_is_running"):
            return Response({"status": "database is running"})

        return Response(
            {"status": "cannot connect to database"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="status",
        permission_classes=[],
    )
    def status(self, request):
        # Can't reasonably send 500 error if API isn't running
        return Response({"status": "API is running"})
