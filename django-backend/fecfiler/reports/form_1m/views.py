from rest_framework.viewsets import ModelViewSet
from fecfiler.reports.models import Report
from fecfiler.reports.managers import ReportType
from fecfiler.reports.views import ReportViewSet
from fecfiler.shared.utilities import strip_read_only_args_from_request
from .serializers import Form1MSerializer
import structlog

logger = structlog.get_logger(__name__)


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

    @strip_read_only_args_from_request(Form1MSerializer)
    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    @strip_read_only_args_from_request(Form1MSerializer)
    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
