from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from fecfiler.reports.models import Report
from fecfiler.reports.managers import ReportType
from fecfiler.reports.views import ReportViewSet
from .serializers import Form3XSerializer
import structlog
from rest_framework.response import Response
from fecfiler.reports.report_code_label import report_code_label_mapping

logger = structlog.get_logger(__name__)


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

    @action(detail=False)
    def report_code_map(self, request):
        return JsonResponse(report_code_label_mapping, safe=False)

    @action(detail=False, methods=["get"], url_path=r"future")
    def future_form3x_reports(self, request):
        json_date_string = request.GET.get("after", "")
        data = list(
            self.get_queryset().filter(coverage_through_date__gt=json_date_string)
        )
        return Response(Form3XSerializer(data, many=True).data)

    @action(detail=False, methods=["get"], url_path=r"final")
    def get_final_report(self, request):
        year = request.GET.get("year", "")
        logger.info(f"Getting final report for year {year}")
        if not year:
            return Response("Year is required", status=400)

        final_report = (
            self.get_queryset()
            .filter(coverage_through_date__year=year)
            .order_by("-coverage_through_date")
            .first()
        )
        if not final_report:
            return Response(None)
        return Response(Form3XSerializer(final_report).data)

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
