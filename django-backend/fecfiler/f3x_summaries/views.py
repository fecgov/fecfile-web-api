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


def get_status_mapping():
    """returns Django Case that determines report status based on upload submission"""
    in_progress = Q(upload_submission__fec_status=None) | Q(upload_submission=None)
    submitted = Q(
        upload_submission__fecfile_task_state__in=[
            FECSubmissionState.INITIALIZING,
            FECSubmissionState.CREATING_FILE,
            FECSubmissionState.SUBMITTING,
        ]
    ) | Q(upload_submission__fec_status=FECStatus.PROCESSING)
    success = Q(upload_submission__fec_status=FECStatus.ACCEPTED)
    failed = Q(
        upload_submission__fecfile_task_state=FECSubmissionState.FAILED
    ) | Q(
        upload_submission__fec_status=FECStatus.REJECTED
    )

    return Case(
        When(in_progress, then=Value("In progress")),
        When(submitted, then=Value("Submission pending")),
        When(success, then=Value("Submission success")),
        When(failed, then=Value("Submission failure")),
    )


class F3XSummaryViewSet(CommitteeOwnedViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    queryset = (
        F3XSummary.objects.annotate(report_code_label=report_code_label_mapping)
        .annotate(report_status=get_status_mapping())
        .all()
    )

    serializer_class = F3XSummarySerializer
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

    @action(
        detail=False,
        methods=["post"],
        url_path="hard-delete-reports",
    )
    def hard_delete_reports(self, request):
        committee_id = request.data.get("committee_id")
        if not committee_id:
            return Response(
                "No committee_id provided", status=status.HTTP_400_BAD_REQUEST
            )

        reports = F3XSummary.objects.filter(
            committee_account__committee_id=committee_id
        )
        report_count = reports.count()
        transaction_count = Transaction.objects.filter(
            report__committee_account__committee_id=committee_id
        ).count()
        memo_count = MemoText.objects.filter(
            report__committee_account__committee_id=committee_id
        ).count()
        dot_fec_count = DotFEC.objects.filter(
            report__committee_account__committee_id=committee_id
        ).count()
        upload_submission_count = UploadSubmission.objects.filter(
            dot_fec__report__committee_account__committee_id=committee_id
        ).count()
        web_print_submission_count = WebPrintSubmission.objects.filter(
            dot_fec__report__committee_account__committee_id=committee_id
        ).count()
        logger.warn(f"Deleting Reports: {report_count}")
        logger.warn(f"Deleting Transactions: {transaction_count}")
        logger.warn(f"Memos: {memo_count}")
        logger.warn(f"Dot Fecs: {dot_fec_count}")
        logger.warn(f"Upload Submissions: {upload_submission_count}")
        logger.warn(f"WebPrint Submissions: {web_print_submission_count}")

        reports.hard_delete()
        return Response(f"Deleted {report_count} Reports")


class ReportViewMixin(GenericViewSet):
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
