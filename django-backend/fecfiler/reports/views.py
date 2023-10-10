from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from .models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.web_services.models import FECSubmissionState, FECStatus
from fecfiler.memo_text.models import MemoText
from fecfiler.web_services.models import DotFEC, UploadSubmission, WebPrintSubmission
from .serializers import ReportSerializer
from django.db.models import Case, Value, When, Q
import logging

logger = logging.getLogger(__name__)

report_code_label_mapping = Case(
    When(report_code="Q1", then=Value("APRIL 15 (Q1)")),
    When(report_code="Q2", then=Value("JULY 15 (Q2)")),
    When(report_code="Q3", then=Value("OCTOBER 15 (Q3)")),
    When(report_code="YE", then=Value("JANUARY 31 (YE)")),
    When(report_code="TER", then=Value("TERMINATION (TER)")),
    When(report_code="MY", then=Value("JULY 31 (MY)")),
    When(report_code="12G", then=Value("GENERAL (12G)")),
    When(report_code="12P", then=Value("PRIMARY (12P)")),
    When(report_code="12R", then=Value("RUNOFF (12R)")),
    When(report_code="12S", then=Value("SPECIAL (12S)")),
    When(report_code="12C", then=Value("CONVENTION (12C)")),
    When(report_code="30G", then=Value("GENERAL (30G)")),
    When(report_code="30R", then=Value("RUNOFF (30R)")),
    When(report_code="30S", then=Value("SPECIAL (30S)")),
    When(report_code="M2", then=Value("FEBRUARY 20 (M2)")),
    When(report_code="M3", then=Value("MARCH 30 (M3)")),
    When(report_code="M4", then=Value("APRIL 20 (M4)")),
    When(report_code="M5", then=Value("MAY 20 (M5)")),
    When(report_code="M6", then=Value("JUNE 20 (M6)")),
    When(report_code="M7", then=Value("JULY 20 (M7)")),
    When(report_code="M8", then=Value("AUGUST 20 (M8)")),
    When(report_code="M9", then=Value("SEPTEMBER 20 (M9)")),
    When(report_code="M10", then=Value("OCTOBER 20 (M10)")),
    When(report_code="M11", then=Value("NOVEMBER 20 (M11)")),
    When(report_code="M12", then=Value("DECEMBER 20 (M12)")),
)


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
    failed = Q(upload_submission__fecfile_task_state=FECSubmissionState.FAILED) | Q(
        upload_submission__fec_status=FECStatus.REJECTED
    )

    return Case(
        When(in_progress, then=Value("In progress")),
        When(submitted, then=Value("Submission pending")),
        When(success, then=Value("Submission success")),
        When(failed, then=Value("Submission failure")),
    )


class ReportViewSet(CommitteeOwnedViewSet):
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

    serializer_class = ReportSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "form_type",
        "upload_submission__fec_status",
        "submission_status",
    ]
    ordering = ["form_type"]

    # Allow requests to filter reports output based on report type by
    # passing a query parameter
    def get_queryset(self):
        queryset = super().get_queryset()
        report_type_filters = self.request.query_params.get("report_type")
        if report_type_filters is not None:
            report_type_list = report_type_filters.split(",")
            # All transactions are included by default, here we remove those
            # that are not identified in the schedules query param
            if "f3x" not in report_type_list:
                queryset = queryset.filter(report_f3x__isnull=True)
            if "f24" not in report_type_list:
                queryset = queryset.filter(report_f24__isnull=True)
        return queryset

    @action(
        detail=False, methods=["post"], url_path="hard-delete-reports",
    )
    def hard_delete_reports(self, request):
        committee_id = request.data.get("committee_id")
        if not committee_id:
            return Response(
                "No committee_id provided", status=status.HTTP_400_BAD_REQUEST
            )

        reports = Report.objects.filter(committee_account__committee_id=committee_id)
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

    def create(self, request):
        response = {"message": "Create function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)


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
