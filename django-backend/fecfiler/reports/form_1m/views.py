from rest_framework.viewsets import ModelViewSet
from fecfiler.reports.models import Report
from fecfiler.reports.managers import ReportType
from fecfiler.reports.views import ReportViewSet
from .serializers import Form1MSerializer
import logging

logger = logging.getLogger(__name__)


class Form1MViewSet(ReportViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Report.objects.select_related("form_1m").filter(
        report_type=ReportType.F1M.value
    )

    serializer_class = Form1MSerializer

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
