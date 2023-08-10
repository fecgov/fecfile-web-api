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
from fecfiler.contacts.serializers import ContactSerializer
from fecfiler.transactions.schedule_a.serializers import ScheduleATransactionSerializer
from fecfiler.transactions.schedule_b.serializers import ScheduleBTransactionSerializer
from fecfiler.transactions.schedule_c.serializers import ScheduleCTransactionSerializer
from fecfiler.transactions.schedule_c1.serializers import (
    ScheduleC1TransactionSerializer,
)
from fecfiler.transactions.schedule_c2.serializers import (
    ScheduleC2TransactionSerializer,
)
from fecfiler.transactions.schedule_d.serializers import (
    ScheduleDTransactionSerializer
)
from fecfiler.transactions.schedule_e.serializers import (
    ScheduleETransactionSerializer
)


logger = logging.getLogger(__name__)


def save_transaction_pair(request):
    """Handle the saving of a strictly parent/child pair.

    The child is removed from the parent and saved separately with the
    parent_transaction_id so that each schedule serializer can handle
    just its specific schedule fields and validation rules
    """
    schedule_1_data = request.data
    schedule_2_data = request.data["children"][0]
    schedule_1_data["children"] = []

    serializers = dict(
        A=ScheduleATransactionSerializer,
        B=ScheduleBTransactionSerializer,
        C=ScheduleCTransactionSerializer,
        C1=ScheduleC1TransactionSerializer,
        C2=ScheduleC2TransactionSerializer,
        D=ScheduleDTransactionSerializer,
        E=ScheduleETransactionSerializer
    )

    serializer_1 = serializers.get(schedule_1_data.get("schedule_id"))
    serializer_2 = serializers.get(schedule_2_data.get("schedule_id"))

    if "id" in schedule_1_data:
        schedule_1 = Transaction.objects.get(pk=schedule_1_data["id"])
        schedule_1_serializer = serializer_1(schedule_1, data=schedule_1_data)
    else:
        schedule_1_serializer = serializer_1(data=schedule_1_data)

    with transaction.atomic():
        schedule_1_serializer.context["request"] = request
        if schedule_1_serializer.is_valid(raise_exception=True):
            schedule_1 = schedule_1_serializer.save()
            schedule_2_data["parent_transaction_id"] = schedule_1.id
            if schedule_2_data.pop("use_parent_contact", None):
                schedule_2_data["contact_1_id"] = schedule_1.contact_1_id
                schedule_2_data["contact_1"] = ContactSerializer().to_representation(
                    schedule_1.contact_1
                )

            if "id" in schedule_2_data:
                schedule_2 = Transaction.objects.get(pk=schedule_2_data["id"])
                schedule_2_serializer = serializer_2(schedule_2, data=schedule_2_data)
            else:
                schedule_2_serializer = serializer_2(data=schedule_2_data)

            schedule_2_serializer.context["request"] = request
            if schedule_2_serializer.is_valid(raise_exception=True):
                schedule_2_serializer.save()

                # Both 1 and 2 saves were successful, return parent transaction
                return Response(serializer_1(schedule_1).data)


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
