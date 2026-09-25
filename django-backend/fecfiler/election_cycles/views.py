from .models import ElectionCycle
from .serializers import ElectionCycleSerializer
from fecfiler.committee_accounts.views import CommitteeOwnedViewMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST


class ElectionCyclesListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class ElectionCyclesViewSet(CommitteeOwnedViewMixin, ModelViewSet):
    def get_queryset(self):
        cycles = super().get_queryset()
        return cycles

    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = ElectionCycle.objects.all()

    serializer_class = ElectionCycleSerializer
    pagination_class = ElectionCyclesListPagination

    filter_backends = [OrderingFilter]
    ordering = ["-election_year", "-start_date"]
    ordering_fields = [
        "election_year",
        "start_date",
        "office",
        "election_type",
    ]

    @action(detail=False, methods=["get"], url_path="check-overlap")
    def check_overlap(self, request):
        """
        Checks if a given date range overlaps with any existing election cycles
        for the current committee account, returning which bound(s) fail.

        Expected query params:
        - start_date (YYYY-MM-DD)
        - end_date (YYYY-MM-DD)
        - exclude_id (optional UUID string to exclude current item during updates)
        """
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        exclude_id = request.query_params.get("exclude_id")

        if not start_date or not end_date:
            return Response(
                {"error": "Both start_date and end_date query parameters are required."},
                status=HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset()
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        overlapping_records = queryset.filter(
            start_date__lte=end_date, end_date__gte=start_date
        )

        is_overlapping = overlapping_records.exists()

        start_date_failed = False
        end_date_failed = False

        if is_overlapping:
            start_date_failed = overlapping_records.filter(
                start_date__lte=start_date, end_date__gte=start_date
            ).exists()

            end_date_failed = overlapping_records.filter(
                start_date__lte=end_date, end_date__gte=end_date
            ).exists()

            if not start_date_failed and not end_date_failed:
                start_date_failed = True
                end_date_failed = True

        return Response(
            {
                "start_date": start_date_failed,
                "end_date": end_date_failed,
            }
        )
