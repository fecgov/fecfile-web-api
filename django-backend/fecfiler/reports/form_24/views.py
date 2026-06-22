from rest_framework.viewsets import ModelViewSet
from fecfiler.reports.models import Report
from fecfiler.reports.managers import ReportType
from fecfiler.reports.views import ReportViewSet
from .serializers import Form24Serializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import structlog

logger = structlog.get_logger(__name__)


class Form24ViewSet(ReportViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = Report.objects.select_related("form_24").filter(
        report_type=ReportType.F24.value
    )

    serializer_class = Form24Serializer

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)

    @action(detail=False, methods=["get"], url_path="check")
    def check_name(self, request):
        name = request.query_params.get("name", None)

        if not name:
            return Response(
                {"error": "Name parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exists = self.get_queryset().filter(form_24__name__iexact=name).exists()
        return Response({"available": not exists}, status=status.HTTP_200_OK)
