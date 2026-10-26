from .models import ElectionCycle
from .serializers import ElectionCycleSerializer
from fecfiler.committee_accounts.views import CommitteeOwnedViewMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from fecfiler.reports.form_3.models import Form3
from django.db.models import Exists, OuterRef, Q
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError


class ElectionCyclesListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class ElectionCyclesViewSet(CommitteeOwnedViewMixin, ModelViewSet):
    def get_queryset(self):
        cycles = (
            super()
            .get_queryset()
            .annotate(
                has_form3=Exists(
                    Form3.objects.filter(
                        Q(election_cycle_id=OuterRef("pk"))
                        | Q(next_election_cycle_id=OuterRef("pk"))
                    )
                )
            )
        )
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

    @action(detail=False, methods=["get"], url_path="find-by-coverage")
    def find_by_coverage(self, request):
        start_date = parse_date(request.query_params.get("start_date", ""))
        end_date = parse_date(request.query_params.get("end_date", ""))

        if start_date is None or end_date is None:
            return Response(
                {
                    "error": (
                        "Both start_date and end_date query parameters "
                        "are required and must be valid dates."
                    )
                },
                status=HTTP_400_BAD_REQUEST,
            )

        if start_date > end_date:
            return Response(
                {"error": "start_date must be less than or equal to end_date."},
                status=HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset()

        election_cycle = queryset.filter(
            start_date__lte=start_date,
            end_date__gte=start_date,
        ).first()

        if not election_cycle:
            return Response({"needs_cycle": True, "needs_next_cycle": False})

        response_data = {
            "needs_cycle": False,
            "needs_next_cycle": False,
            "election_cycle": self.get_serializer(election_cycle).data,
        }

        if end_date <= election_cycle.end_date:
            return Response(response_data)

        next_cycle = (
            queryset.filter(start_date__gt=election_cycle.end_date)
            .order_by("start_date")
            .first()
        )

        response_data["needs_next_cycle"] = (
            not next_cycle
            or end_date < next_cycle.start_date
            or end_date > next_cycle.end_date
        )
        if response_data["needs_next_cycle"]:
            return Response(response_data)

        response_data["next_election_cycle"] = self.get_serializer(next_cycle).data
        return Response(response_data)

    def perform_destroy(self, instance):
        if not instance.can_delete:
            raise ValidationError(
                "Cannot delete an election cycle associated with a Form 3.",
                HTTP_400_BAD_REQUEST,
            )
        instance.delete()
