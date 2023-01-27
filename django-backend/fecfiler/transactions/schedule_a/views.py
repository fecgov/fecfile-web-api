import logging

from django.db.models.functions import Coalesce, Concat
from .serializers import ScheduleATransactionSerializer as newSCHA
from fecfiler.transactions.views import TransactionViewSet
from fecfiler.transactions.models import Transaction
from django.db.models import TextField, Value, F
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class ScheduleATransactionViewSet(TransactionViewSet):
    queryset = (
        Transaction.objects.select_related("schedule_a")
        .alias(
            contribution_amount=F("action_amount"),
            contribution_date=F("action_date"),
            contributor_name=Coalesce(
                "schedule_a__contributor_organization_name",
                Concat(
                    "schedule_a__contributor_last_name",
                    Value(", "),
                    "schedule_a__contributor_first_name",
                    output_field=TextField(),
                ),
            ),
        )
        .annotate(contribution_aggregate=F("action_aggregate"))
    )
    serializer_class = newSCHA
    ordering_fields = [
        "id",
        "transaction_type_identifier",
        "contributor_name",
        "contribution_date",
        "memo_code",
        "contribution_amount",
        "contribution_aggregate",
    ]

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
