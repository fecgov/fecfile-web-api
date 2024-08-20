import structlog
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from django.utils.html import escape
from django.db import connection
from celery import Celery
from fecfiler.celery import debug_task


logger = structlog.get_logger(__name__)


class SystemStatusViewSet(viewsets.ViewSet):
    @action(
        detail=False,
        methods=["get"],
        url_path="celery-status",
        permission_classes=[],
    )
    def celery_status(self, request):
        result = debug_task.delay().wait(timeout=30, interval=1)
        if result:
            return Response({"status": "celery is completing tasks"})
        return Response(
            {"status": "celery queue is not circulating"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="database-status",
        permission_classes=[],
    )
    def database_status(self, request):
        with connection.cursor() as cursor:
            cursor.execute(
                "select * from pg_stat_activity where datname = current_database()"
            )
            status_data = cursor.fetchone()
            if status_data:
                return Response(
                    {"status": "database is running"}, status=status.HTTP_200_OK
                )
            return Response(
                {"status": "cannot connect to database"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
