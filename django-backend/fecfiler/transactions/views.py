import logging

from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.db.models import Q
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.f3x_summaries.views import ReportViewMixin
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.serializers import TransactionSerializerBase


logger = logging.getLogger(__name__)


class TransactionViewSetBase(CommitteeOwnedViewSet, ReportViewMixin):
    """ """

    filter_backends = [filters.OrderingFilter]
    ordering = ["-created"]


class TransactionViewSet(CommitteeOwnedViewSet, ReportViewMixin):

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializerBase
    filter_backends = [filters.OrderingFilter]

    ordering_fields = [
        "id",
        "transaction_type_identifier",
        "memo_code",
    ]
    ordering = ["-created"]

    @action(detail=False, methods=["get"])
    def previous(self, request):
        """Retrieves transaction that comes before this transactions,
        while bieng in the same group for aggregation"""
        transaction_id = request.query_params.get("transaction_id", None)
        contact_id = request.query_params.get("contact_id", None)
        action_date = request.query_params.get("action_date", None)
        aggregation_group = request.query_params.get("aggregation_group", None)
        if not (contact_id and action_date):
            return Response(
                "Please provide contact_id and action_date in query params.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        action_date = datetime.fromisoformat(action_date)

        previous_transaction = (
            self.get_queryset()
            .filter(
                ~Q(id=transaction_id or None),
                Q(contact_id=contact_id),
                Q(action_date__year=action_date.year),
                Q(action_date__lte=action_date),
                Q(aggregation_group=aggregation_group),
            )
            .order_by("-action_date", "-created")
            .first()
        )

        serializer = self.get_serializer(previous_transaction)
        return Response(data=serializer.data)
