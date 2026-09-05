from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from fecfiler.reports.models import Report
from fecfiler.reports.managers import ReportType, STATUS_CODE_IN_PROGRESS
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

    @action(detail=False, methods=["get"], url_path=r"associated")
    def get_associated_form3x_report(self, request):
        disbursement_date = request.GET.get("disbursement_date", None)
        dissemination_date = request.GET.get("dissemination_date", None)
        base_query = self.get_queryset().filter(
            report_status=STATUS_CODE_IN_PROGRESS,
            coverage_from_date__isnull=False,
            coverage_through_date__isnull=False,
        )
        associated_form3x = None
        if disbursement_date:
            associated_form3x = base_query.filter(
                coverage_from_date__lte=disbursement_date,
                coverage_through_date__gte=disbursement_date,
            ).first()
        if associated_form3x is None and dissemination_date:
            associated_form3x = base_query.filter(
                coverage_from_date__lte=dissemination_date,
                coverage_through_date__gte=dissemination_date,
            ).first()

        if associated_form3x is None:
            return Response(None)
        return Response(Form3XSerializer(associated_form3x).data)

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
