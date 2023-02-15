import logging

from django.db.models.functions import Coalesce, Concat
from .serializers import ScheduleBTransactionSerializer
from fecfiler.transactions.views import TransactionViewSet
from fecfiler.transactions.models import Transaction
from django.db.models import TextField, Value, F
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class ScheduleBTransactionViewSet(TransactionViewSet):
    queryset = (
        Transaction.objects.select_related("schedule_b")
        .filter(schedule_b__isnull=False)
        .alias(
            expenditure_amount=F("amount"),
            expenditure_date=F("date"),
            payee_name=Coalesce(
                "schedule_b__payee_organization_name",
                Concat(
                    "schedule_b__payee_last_name",
                    Value(", "),
                    "schedule_b__payee_first_name",
                    output_field=TextField(),
                ),
            ),
        )
        .annotate(aggregate_amount=F("aggregate"))
    )
    serializer_class = ScheduleBTransactionSerializer
    ordering_fields = [
        "id",
        "transaction_type_identifier",
        "payee_name",
        "expenditure_date",
        "memo_code",
        "expenditure_amount",
        "aggregate_amount",
    ]

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
