import logging

from django.db import transaction
from rest_framework import filters, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.db.models import Q, Value
from django.db.models.fields import TextField
from django.db.models.functions import Coalesce, Concat
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.f3x_summaries.views import ReportViewMixin
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.serializers import TransactionSerializerBase
from fecfiler.transactions.schedule_a.serializers import ScheduleATransactionSerializer
from fecfiler.transactions.schedule_b.serializers import ScheduleBTransactionSerializer


logger = logging.getLogger(__name__)


def save_transaction_pair(request):
    """Handle the saving of a strictly parent/child pair whose parent
    is a Schedule A and child is a Schedule B.

    IMPORTANT: The Schedule B transaction contact info will be overriden by the
    contact info in the Schedule A transaction

    The child is removed from the parent and saved separately with the
    parent_transaction_id so that each schedule serializer can handle
    just its specific schedule fields and validation rules
    """
    schedule_a_data = request.data
    schedule_b_data = request.data["children"][0]
    schedule_a_data["children"] = []

    if "id" in schedule_a_data:
        schedule_a = Transaction.objects.get(pk=schedule_a_data["id"])
        schedule_a_serializer = ScheduleATransactionSerializer(
            schedule_a, data=schedule_a_data
        )
    else:
        schedule_a_serializer = ScheduleATransactionSerializer(data=schedule_a_data)

    with transaction.atomic():
        schedule_a_serializer.context["request"] = request
        if schedule_a_serializer.is_valid():
            schedule_a = schedule_a_serializer.save()
            schedule_b_data["parent_transaction_id"] = schedule_a.id
            # Assign contact in the Schedule A to the Schedule B
            schedule_b_data["contact_id"] = schedule_a.contact_id
            schedule_b_data["contact"] = schedule_a_data["contact"]

            if "id" in schedule_b_data:
                schedule_b = Transaction.objects.get(pk=schedule_b_data["id"])
                schedule_b_serializer = ScheduleBTransactionSerializer(
                    schedule_b, data=schedule_b_data
                )
            else:
                schedule_b_serializer = ScheduleBTransactionSerializer(
                    data=schedule_b_data
                )

            schedule_b_serializer.context["request"] = request
            if schedule_b_serializer.is_valid():
                schedule_b_serializer.save()

                # Both A and B saves were successful, return parent transaction
                return Response(ScheduleATransactionSerializer(schedule_a).data)
            else:
                return Response(
                    schedule_b_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                schedule_a_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


class TransactionListPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"


class TransactionViewSetBase(CommitteeOwnedViewSet, ReportViewMixin):
    """ """

    filter_backends = [filters.OrderingFilter]
    ordering = ["-created"]


class TransactionViewSet(CommitteeOwnedViewSet, ReportViewMixin):

    queryset = Transaction.objects.all().alias(
        name=Coalesce(
            Coalesce(
                "schedule_b__payee_organization_name",
                "schedule_a__contributor_organization_name",
            ),
            Concat(
                Coalesce(
                    "schedule_b__payee_last_name", "schedule_a__contributor_last_name"
                ),
                Value(", "),
                Coalesce(
                    "schedule_b__payee_first_name", "schedule_a__contributor_first_name"
                ),
                output_field=TextField(),
            ),
        )
    )
    serializer_class = TransactionSerializerBase
    pagination_class = TransactionListPagination
    filter_backends = [filters.OrderingFilter]

    ordering_fields = [
        "id",
        "transaction_type_identifier",
        "memo_code",
        "name",
        "date",
        "amount",
        "aggregate",
    ]
    ordering = ["-created"]

    @action(detail=False, methods=["get"])
    def previous(self, request):
        """Retrieves transaction that comes before this transactions,
        while bieng in the same group for aggregation"""
        transaction_id = request.query_params.get("transaction_id", None)
        contact_1_id = request.query_params.get("contact_1_id", None)
        date = request.query_params.get("date", None)
        aggregation_group = request.query_params.get("aggregation_group", None)
        if not (contact_1_id and date):
            return Response(
                "Please provide contact_1_id and date in query params.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        date = datetime.fromisoformat(date)

        previous_transaction = (
            self.get_queryset()
            .filter(
                ~Q(id=transaction_id or None),
                Q(contact_1_id=contact_1_id),
                Q(date__year=date.year),
                Q(date__lte=date),
                Q(aggregation_group=aggregation_group),
            )
            .order_by("-date", "-created")
            .first()
        )

        if previous_transaction:
            serializer = self.get_serializer(previous_transaction)
            return Response(data=serializer.data)

        response = {"message": "No previous transaction found."}
        return Response(response, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"], url_path=r"save-pair")
    def create_pair(self, request):
        return save_transaction_pair(request)

    @action(detail=False, methods=["put"], url_path=r"save-pair/(?P<pk>[^/.]+)")
    def update_pair(self, request, pk=None):
        return save_transaction_pair(request)

    def create(self, request):
        response = {"message": "Create function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)
