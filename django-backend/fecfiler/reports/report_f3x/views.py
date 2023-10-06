from django.http import JsonResponse
from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from .models import F3XSummary
from .report_codes.views import report_code_label_mapping
from fecfiler.transactions.models import Transaction
from fecfiler.web_services.models import FECSubmissionState, FECStatus
from fecfiler.memo_text.models import MemoText
from fecfiler.web_services.models import DotFEC, UploadSubmission, WebPrintSubmission
from .serializers import F3XSummarySerializer
from django.db.models import Case, Value, When, Q
import logging

logger = logging.getLogger(__name__)


class ReportF3XViewSet(CommitteeOwnedViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    queryset = (
        Report.objects.annotate(report_code_label=report_code_label_mapping)
        .annotate(report_status=get_status_mapping())
        .all()
    )

    serializer_class = ReportF3XSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "form_type",
        "report_code_label",
        "coverage_through_date",
        "upload_submission__fec_status",
        "submission_status",
    ]
    ordering = ["form_type"]

    @action(detail=False)
    def coverage_dates(self, request):
        data = list(
            self.get_queryset()
            .distinct("coverage_from_date", "coverage_through_date")
            .values("report_code", "coverage_from_date", "coverage_through_date")
        )
        return JsonResponse(data, safe=False)

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)


class ReportF3XViewMixin(GenericViewSet):
    def get_queryset(self):
        report_id = (
            (
                self.request.query_params.get("report_id")
                or self.request.data.get("report_id")
            )
            if self.request
            else None
        )
        queryset = super().get_queryset()
        return queryset.filter(report_id=report_id) if report_id else queryset
