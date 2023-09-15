from fecfiler.reports.f3x_report.models import F3XReport
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .tasks import calculate_summary, CalculationState
from ..serializers import ReportIdSerializer

import logging

logger = logging.getLogger(__name__)


class SummaryViewSet(viewsets.ViewSet):
    """
    A viewset that provides actions to start summary calculation tasks and
    retrieve their statuses and results
    """

    @action(
        detail=False,
        methods=["post"],
        url_path="calculate-summary",
    )
    def calculate_summary(self, request):
        """ """
        serializer = ReportIdSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        report_id = serializer.validated_data["report_id"]
        report = F3XReport.objects.get(id=report_id)
        report.calculation_status = CalculationState.CALCULATING
        report.save()
        logger.debug(f"Starting Celery Task calculate_summary for report :{report_id}")
        task = calculate_summary.apply_async((report_id,), retry=False)
        logger.debug(f"Status from calculate_summary report {report_id}: {task.status}")
        return Response({"status": "summary task created"})
