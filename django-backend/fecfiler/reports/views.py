from rest_framework import filters, status, pagination
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from fecfiler.committee_accounts.views import CommitteeOwnedViewMixin
from fecfiler.filters import CommitteeOwnedFilterBackend
from .models import Report
from .report_code_label import report_code_label_case
from fecfiler.transactions.models import Transaction
from fecfiler.memo_text.models import MemoText
from fecfiler.web_services.models import DotFEC, UploadSubmission, WebPrintSubmission
from .serializers import ReportSerializer
from django.db.models import Case, Value, When, CharField, IntegerField, F
from django.db.models.functions import Concat, Trim
import structlog

logger = structlog.get_logger(__name__)


version_labels = {
    "F3XN": "Original",
    "F3XA": "Amendment",
    "F3XT": "Termination",
    "F24N": "Original",
    "F24A": "Amendment",
    "F1MN": "Original",
    "F1MA": "Amendment",
    "F99": "Original",
}

form_type_ordering = {
    "F1MN": 10,
    "F1MA": 10,
    "F3XN": 20,
    "F3XA": 20,
    "F3XT": 20,
    "F24N": 30,
    "F24A": 30,
    "F99": 40,
}


class ReportListPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class ReportViewSet(CommitteeOwnedViewMixin, ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that the queryset will be limited by the user's committee
    via CommitteeOwnedFilterBackend
    """

    queryset = Report.objects
    serializer_class = ReportSerializer
    pagination_class = ReportListPagination
    filter_backends = [filters.OrderingFilter, CommitteeOwnedFilterBackend]
    ordering_fields = [
        "report_code_label",
        "coverage_through_date",
        "upload_submission__created",
        "report_status",
        "version_label",
        "form_type_ordering",
    ]
    ordering = ["form_type_ordering"]

    # Allow requests to filter reports output based on report type by
    # passing a query parameter
    def get_queryset(self):
        ordering_whens = [
            When(form_type=k, then=Value(v)) for k, v in form_type_ordering.items()
        ]
        form_type_label_whens = [
            When(form_type=k, then=Value(v)) for k, v in version_labels.items()
        ]
        queryset = (
            super()
            .get_queryset()
            .annotate(report_code_label=report_code_label_case)
            # alias fields used by the version_label annotation only. not part of payload
            .alias(
                form_type_label=Case(
                    *form_type_label_whens,
                    default=Value(""),
                    output_field=CharField(),
                ),
                report_version_label=Case(
                    When(report_version__isnull=True, then=Value("")),
                    default=F("report_version"),
                    output_field=CharField(),
                ),
            )
            .annotate(
                version_label=Trim(
                    Concat(
                        F("form_type_label"),
                        Value(" "),
                        F("report_version_label"),
                        output_field=CharField(),
                    )
                )
            )
            .annotate(
                form_type_ordering=Case(
                    *ordering_whens,
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
        )
        report_type_filters = self.request.query_params.get("report_type")
        if report_type_filters is not None:
            report_type_list = report_type_filters.split(",")
            # All transactions are included by default, here we remove those
            # that are not identified in the schedules query param
            if "f3x" not in report_type_list:
                queryset = queryset.filter(form_3x__isnull=True)
            if "f24" not in report_type_list:
                queryset = queryset.filter(form_24__isnull=True)
            if "f99" not in report_type_list:
                queryset = queryset.filter(form_99__isnull=True)
            if "f1m" not in report_type_list:
                queryset = queryset.filter(form_1m__isnull=True)

        return queryset

    @action(detail=True, methods=["post"], url_name="amend")
    def amend(self, request, pk):
        report = self.get_object()
        report.amend()
        return Response(f"amended {report}")

    @action(detail=True, methods=["post"], url_name="unamend")
    def unamend(self, request, pk):
        report: Report = self.get_object()
        latest_submission = (
            UploadSubmission.objects.filter(fec_report_id=report.report_id)
            .order_by("-created")
            .first()
        )
        report.unamend(latest_submission)
        return Response(f"unamended {report}")

    @action(
        detail=False,
        methods=["post"],
        url_path="e2e-delete-all-reports",
    )
    def e2e_delete_all_reports(self, request):
        reports = Report.objects.filter(committee_account__committee_id="C99999999")
        report_count = reports.count()

        delete_all_reports()
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

    def list(self, request, *args, **kwargs):
        ordering = request.query_params.get("ordering")
        if ordering in ["form_type", "-form_type"]:
            new_ordering = (
                "-form_type_ordering"
                if ordering.startswith("-")
                else "form_type_ordering"
            )
            request.query_params._mutable = True
            request.query_params["ordering"] = new_ordering
            request.query_params._mutable = False
        return super().list(request, args, kwargs)


class ReportViewMixin(GenericViewSet):
    def get_queryset(self):
        return filter_by_report(super().get_queryset(), self)


def filter_by_report(queryset, viewset):
    report_id = (
        (
            viewset.request.query_params.get("report_id")
            or viewset.request.data.get("report_id")
        )
        if viewset.request
        else None
    )
    return queryset.filter(report_id=report_id) if report_id else queryset


def delete_all_reports(committee_id="C99999999", log_method=logger.warn):
    reports = Report.objects.filter(committee_account__committee_id=committee_id)
    transactions = Transaction.objects.filter(
        committee_account__committee_id=committee_id
    )

    report_count = reports.count()
    transaction_count = transactions.count()
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

    log_method(f"Deleting Reports and Transactions for {committee_id}")
    log_method(f"Deleting Reports: {report_count}")
    log_method(f"Deleting Transactions: {transaction_count}")
    log_method(f"Memos: {memo_count}")
    log_method(f"Dot Fecs: {dot_fec_count}")
    log_method(f"Upload Submissions: {upload_submission_count}")
    log_method(f"WebPrint Submissions: {web_print_submission_count}")

    reports.delete()
    transactions.hard_delete()
