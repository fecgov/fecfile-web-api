from rest_framework import filters
from rest_framework.viewsets import ModelViewSet
from fecfiler.reports.models import Report
from fecfiler.reports.managers import ReportType
from fecfiler.reports.views import ReportViewSet
from .serializers import ReportF24Serializer
import logging

logger = logging.getLogger(__name__)


class ReportF24ViewSet(ReportViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Report.objects.select_related("report_f24").filter(
        report_type=ReportType.F24.value
    )

    serializer_class = ReportF24Serializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "form_type",
        "report_code_label",
        "upload_submission__fec_status",
        "submission_status",
    ]
    ordering = ["form_type"]

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
