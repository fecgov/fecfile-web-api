from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from fecfiler.reports.models import Report
from .models import Form3X
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

    @action(detail=True, methods=["get", "put"])
    def jan1_cash_on_hand(self, request):
        if request.method == "GET":
            year = request.GET.get("year")
            if year is None:
                return HttpResponseBadRequest("year query param is required")
            retval = (
                Report.objects.filter(
                    committee_account=self.get_committee_uuid(),
                    coverage_from_date__year=year,
                    form_3x__isnull=False,
                )
                .order_by("coverage_from_date")
                .values("form_3x__L6a_cash_on_hand_jan_1_ytd")
                .first()
            )
            return HttpResponse(retval.get("form_3x__L6a_cash_on_hand_jan_1_ytd"))
        if request.method == "PUT":
            year = request.data.get("year")
            amount = request.data.get("amount")
            if not year or not amount:
                return HttpResponseBadRequest(
                    "year and amount are required in request body"
                )
            first_f3x_report = (
                Report.objects.filter(
                    committee_account=self.get_committee_uuid(),
                    coverage_from_date__year=year,
                    form_3x__isnull=False,
                )
                .order_by("coverage_from_date")
                .first()
            )
            if not first_f3x_report:
                return HttpResponseBadRequest("no f3x reports found")
            Form3X.objects.filter(pk=first_f3x_report.form_3x.id).update(
                L6a_cash_on_hand_jan_1_ytd=amount
            )
            return HttpResponse("Cash on hand updated")

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
