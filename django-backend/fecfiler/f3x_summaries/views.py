from django.http import JsonResponse
from rest_framework import filters
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.decorators import action
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from .models import F3XSummary, ReportCodeLabel
from .serializers import F3XSummarySerializer, ReportCodeLabelSerializer


class F3XSummaryViewSet(CommitteeOwnedViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    queryset = F3XSummary.objects.select_related("report_code").all()
    """Join on report code labels"""

    serializer_class = F3XSummarySerializer
    permission_classes = []
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["form_type", "report_code__label", "coverage_through_date"]
    ordering = ["form_type"]

    @action(detail=False)
    def coverage_dates(self, request):
        data = list(
            F3XSummary.objects.distinct(
                "coverage_from_date", "coverage_through_date"
            ).values("report_code", "coverage_from_date", "coverage_through_date")
        )
        return JsonResponse(data, safe=False)


class ReportCodeLabelViewSet(GenericViewSet, ListModelMixin):
    queryset = ReportCodeLabel.objects.all()
    serializer_class = ReportCodeLabelSerializer
    pagination_class = None
