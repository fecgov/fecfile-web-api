from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.reports.models import Report
from fecfiler.reports.managers import ReportType
from fecfiler.reports.views import ReportViewSet
from .serializers import Form3XSerializer
import logging

logger = logging.getLogger(__name__)


class Form3XViewSet(ReportViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Report.objects.select_related("form_3x").filter(
        report_type=ReportType.F3X.value
    )

    serializer_class = Form3XSerializer

    @action(detail=False)
    def coverage_dates(self, request):
        data = list(
            self.get_queryset()
            .distinct("coverage_from_date", "coverage_through_date")
            .values(
                "report_code",
                "coverage_from_date",
                "coverage_through_date",
            )
        )
        return JsonResponse(data, safe=False)

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)

    @action(
        detail=True,
        methods=["post"],
        url_name="amend",
    )
    def amend(self, request, pk):
        report = self.get_object()
        report.form_type = "F3XA"
        report.report_version = int(report.report_version or "0") + 1
        report.upload_submission = None
        report.save()
        return Response(f"amended {report}")
