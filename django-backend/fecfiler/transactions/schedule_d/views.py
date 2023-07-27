import logging

from django.db.models.functions import Coalesce, Concat
from .serializers import ScheduleDTransactionSerializer
from fecfiler.transactions.views import TransactionViewSet
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.managers import Schedule
from django.db.models import TextField, Value
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class ScheduleDTransactionViewSet(TransactionViewSet):
    queryset = (
        Transaction.objects.select_related("schedule_d")
        .filter(schedule=Schedule.D.value)
        .alias(
            creditor_name=Coalesce(
                "schedule_d__creditor_organization_name",
                Concat(
                    "schedule_d__creditor_last_name",
                    Value(", "),
                    "schedule_d__creditor_first_name",
                    output_field=TextField(),
                ),
            ),
        )
    )
    serializer_class = ScheduleDTransactionSerializer
    ordering_fields = [
        "id",
        "transaction_type_identifier",
        "creditor_name",
    ]

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
