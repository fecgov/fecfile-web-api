import logging

from django.db.models.functions import Coalesce, Concat
from datetime import datetime
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.f3x_summaries.views import ReportViewMixin

from fecfiler.transactions.schedule_b.models import ScheduleBTransaction
from fecfiler.transactions.views import TransactionViewSetBase
from fecfiler.transactions.schedule_b.serializers import ScheduleBTransactionSerializer
from django.db.models import TextField, Value, Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class ScheduleBTransactionViewSet(TransactionViewSetBase):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limmited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    queryset = ScheduleBTransaction.objects.alias(
        payee_name=Coalesce(
            "payee_organization_name",
            Concat(
                "payee_last_name",
                Value(", "),
                "payee_first_name",
                output_field=TextField(),
            ),
        )
    ).all()

    serializer_class = ScheduleBTransactionSerializer
    ordering_fields = [
        "id",
        "transaction_type_identifier",
        "payee_name",
        "expenditure_date",
        "memo_code",
        "expenditure_amount",
    ]

    @action(detail=False, methods=["get"])
    def previous(self, request):
        """Retrieves transaction that comes before this transactions,
        while bieng in the same group for aggregation"""
        transaction_id = request.query_params.get("transaction_id", None)
        contact_id = request.query_params.get("contact_id", None)
        expenditure_date = request.query_params.get("expenditure_date", None)
        aggregation_group = request.query_params.get("aggregation_group", None)
        if not (contact_id and expenditure_date):
            return Response(
                "Please provide contact_id and expenditure_date in query params.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        expenditure_date = datetime.fromisoformat(expenditure_date)

        previous_transaction = (
            self.get_queryset()
            .filter(
                ~Q(id=transaction_id or None),
                Q(contact_id=contact_id),
                Q(expenditure_date__year=expenditure_date.year),
                Q(expenditure_date__lte=expenditure_date),
                Q(aggregation_group=aggregation_group),
            )
            .order_by("-expenditure_date", "-created")
            .first()
        )

        serializer = self.get_serializer(previous_transaction)
        return Response(data=serializer.data)
