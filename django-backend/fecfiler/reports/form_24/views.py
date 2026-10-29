from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from fecfiler.reports.models import Report
from fecfiler.reports.managers import ReportType
from fecfiler.reports.views import ReportViewSet
from .serializers import Form24Serializer
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

    @action(detail=False)
    def validation_check(self, request):
        exclude_ids = (
            request.GET.get("exclude_ids").split(",")
            if request.GET.get("exclude_ids")
            else []
        )
        name = request.GET.get("name")
        if name:
            matches = (
                self.get_queryset()
                .exclude(id__in=exclude_ids)
                .filter(form_24__name__iexact=name)
                .count()
            )
            if matches != 0:
                return Response({"valid": False})
        return Response({"valid": True})

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
