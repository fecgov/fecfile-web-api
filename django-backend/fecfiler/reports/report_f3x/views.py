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
from django.db.models import Case, Value, When, Q, F
import logging

logger = logging.getLogger(__name__)


class ReportF3XViewSet(ReportViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Report.objects.select_related("report_f3x").filter(
        report_type=ReportType.F3X.value
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
