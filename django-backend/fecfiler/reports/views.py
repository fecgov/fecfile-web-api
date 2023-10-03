import logging

from fecfiler.reports.models import Report
from fecfiler.reports.serializers import ReportSerializerBase
from rest_framework import filters, pagination
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.reports.f3x_report.views import ReportViewMixin


logger = logging.getLogger(__name__)


class ReportListPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"


class ReportViewSetBase(CommitteeOwnedViewSet, ReportViewMixin):
    """ """

    filter_backends = [filters.OrderingFilter]
    ordering = ["-created"]


class ReportViewSet(CommitteeOwnedViewSet):
    queryset = Report.objects.all()
    print("\n\n\nHEYO",queryset,"\n\n")
    serializer_class = ReportSerializerBase
    pagination_class = ReportListPagination
    filter_backends = [filters.OrderingFilter]

    ordering_fields = [
        "id",
        "_form_type"
    ]
    ordering = ["-created"]

    # Allow requests to filter transactions output based on schedule type by
    # passing a query parameter
    def get_queryset(self):
        queryset = self.queryset
        report_filters = self.request.query_params.get("reports")
        if report_filters is not None:
            report_list = report_filters.split(",")
            # All transactions are included by default, here we remove those
            # that are not identified in the schedules query param
            if "F3X" not in report_list:
                queryset = queryset.filter(f3x_report__isnull=True)
        return queryset