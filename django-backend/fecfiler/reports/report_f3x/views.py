from django.http import JsonResponse
from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.reports.models import Report
from fecfiler.reports.managers import ReportType
from fecfiler.reports.views import ReportViewSet
from .serializers import ReportF3XSerializer
from fecfiler.transactions.models import Transaction
from fecfiler.web_services.models import FECSubmissionState, FECStatus
from fecfiler.memo_text.models import MemoText
from fecfiler.web_services.models import DotFEC, UploadSubmission, WebPrintSubmission
from django.db.models import Case, Value, When, Q
import logging

logger = logging.getLogger(__name__)

report_code_label_mapping = Case(
    When(report_f3x__report_code="Q1", then=Value("APRIL 15 (Q1)")),
    When(report_f3x__report_code="Q2", then=Value("JULY 15 (Q2)")),
    When(report_f3x__report_code="Q3", then=Value("OCTOBER 15 (Q3)")),
    When(report_f3x__report_code="YE", then=Value("JANUARY 31 (YE)")),
    When(report_f3x__report_code="TER", then=Value("TERMINATION (TER)")),
    When(report_f3x__report_code="MY", then=Value("JULY 31 (MY)")),
    When(report_f3x__report_code="12G", then=Value("GENERAL (12G)")),
    When(report_f3x__report_code="12P", then=Value("PRIMARY (12P)")),
    When(report_f3x__report_code="12R", then=Value("RUNOFF (12R)")),
    When(report_f3x__report_code="12S", then=Value("SPECIAL (12S)")),
    When(report_f3x__report_code="12C", then=Value("CONVENTION (12C)")),
    When(report_f3x__report_code="30G", then=Value("GENERAL (30G)")),
    When(report_f3x__report_code="30R", then=Value("RUNOFF (30R)")),
    When(report_f3x__report_code="30S", then=Value("SPECIAL (30S)")),
    When(report_f3x__report_code="M2", then=Value("FEBRUARY 20 (M2)")),
    When(report_f3x__report_code="M3", then=Value("MARCH 30 (M3)")),
    When(report_f3x__report_code="M4", then=Value("APRIL 20 (M4)")),
    When(report_f3x__report_code="M5", then=Value("MAY 20 (M5)")),
    When(report_f3x__report_code="M6", then=Value("JUNE 20 (M6)")),
    When(report_f3x__report_code="M7", then=Value("JULY 20 (M7)")),
    When(report_f3x__report_code="M8", then=Value("AUGUST 20 (M8)")),
    When(report_f3x__report_code="M9", then=Value("SEPTEMBER 20 (M9)")),
    When(report_f3x__report_code="M10", then=Value("OCTOBER 20 (M10)")),
    When(report_f3x__report_code="M11", then=Value("NOVEMBER 20 (M11)")),
    When(report_f3x__report_code="M12", then=Value("DECEMBER 20 (M12)")),
)


class ReportF3XViewSet(ReportViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = (
        Report.objects.select_related("report_f3x")
        .filter(report_type=ReportType.F3X)
        .annotate(report_code_label=report_code_label_mapping)
    )

    serializer_class = ReportF3XSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "report_f3x__form_type",
        "report_code_label",
        "report_f3x__coverage_through_date",
        "upload_submission__fec_status",
        "submission_status",
    ]
    ordering = ["report_f3x__form_type"]

    @action(detail=False)
    def coverage_dates(self, request):
        data = list(
            self.get_queryset()
            .distinct(
                "report_f3x__coverage_from_date", "report_f3x__coverage_through_date"
            )
            .values(
                "report_f3x__report_code",
                "report_f3x__coverage_from_date",
                "report_f3x__coverage_through_date",
            )
        )
        return JsonResponse(data, safe=False)

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
