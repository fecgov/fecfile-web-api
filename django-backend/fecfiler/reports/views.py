from rest_framework import filters, status, pagination
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from fecfiler.committee_accounts.views import CommitteeOwnedViewMixin
from .models import Report
from .managers import STATUS_CODE_SUCCESS
from .report_code_label import report_code_label_case
from fecfiler.reports.utils.report import delete_all_reports
from .serializers import ReportSerializer
from fecfiler.transactions.aggregation import process_aggregation_for_debts
from django.db.models import Case, Value, When, CharField, IntegerField, F
from django.db.models.functions import Concat, Trim
from django.db import transaction as db_transaction
from django.conf import settings
import structlog

logger = structlog.get_logger(__name__)


version_labels = {
    "F3N": "Original",
    "F3A": "Amendment",
    "F3T": "Termination",
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
    "F3N": 20,
    "F3A": 20,
    "F3T": 20,
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

    Note that this ViewSet inherits from CommitteeOwnedViewMixin
    The queryset will be further limited by the user's committee
    in CommitteeOwnedViewMixin's implementation of get_queryset()
    """

    queryset = Report.objects
    serializer_class = ReportSerializer
    pagination_class = ReportListPagination
    filter_backends = [filters.OrderingFilter]
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
            # All reports are included by default, here we remove those
            # that are not identified in the schedules query param
            if "f3" not in report_type_list:
                queryset = queryset.filter(form_3__isnull=True)
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
        if report.report_status != STATUS_CODE_SUCCESS:
            raise ValidationError(
                f"Report {report.id} cannot be amended.",
            )
        report.amend()
        return Response(f"amended {report}")

    @action(detail=True, methods=["post"], url_name="unamend")
    def unamend(self, request, pk):
        report: Report = self.get_object()
        if not report.can_unamend:
            raise ValidationError(
                f"Report {report.id} cannot be unamended.",
            )
        report.unamend()
        return Response(f"unamended {report}")

    if settings.E2E_TEST:

        @action(
            detail=False,
            methods=["post"],
            url_path="e2e-delete-all-reports",
        )
        def e2e_delete_all_reports(self, request):
            reports = Report.objects.filter(committee_account__committee_id="C99999999")
            report_count = reports.count()

            delete_all_reports()
            delete_all_reports("C99999998")
            return Response(f"Deleted {report_count} Reports")

    @action(detail=True, methods=["post"], url_path="update-version-number")
    def update_version_number(self, request, pk):
        try:
            report: Report = self.get_object()
        except Exception:
            return Response({"detail": "Report not found."}, status=404)

        payload = request.data
        original_version = report.report_version
        amendment = payload.get("amendment")
        e_filing_id = payload.get("eFilingId")
        original_amendment_date = payload.get("previousSubmissionDate")

        try:
            report.form_type = report.get_form_name() + ("N" if amendment == "0" else "A")
            report.can_unamend = amendment != "0"
            report.report_version = amendment if amendment != "0" else None
            report.fec_report_id = e_filing_id
            if report.form_24:
                report.form_24.original_amendment_date = original_amendment_date
                report.form_24.save()
            report.save()
            logger.info(
                (
                    f"Changed version of report {report.id} "
                    f"from {original_version} to {amendment}"
                )
            )

            return Response(ReportSerializer(report).data, status=200)

        except Exception:
            return Response(
                {"detail": "An error occurred while updating the report"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create(self, request):
        response = {"message": "Create function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        report = self.get_object()
        with db_transaction.atomic():
            debts = list(report.transactions.filter(schedule_d__isnull=False))
            response = super().destroy(request, *args, **kwargs)
            for debt in debts:
                if debt.debt:
                    process_aggregation_for_debts(debt.debt)

        return response

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


class ReportViewMixin(CommitteeOwnedViewMixin, GenericViewSet):
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
