import logging

from django.db.models.functions import Coalesce, Concat
from .serializers import ScheduleETransactionSerializer
from fecfiler.transactions.views import TransactionViewSet
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.managers import Schedule
from django.db.models import TextField, Value
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class ScheduleETransactionViewSet(TransactionViewSet):
    queryset = (
        Transaction.objects.select_related("schedule_e")
        .filter(schedule=Schedule.E.value)
        .alias(
            payee_name=Coalesce(
                "schedule_e__payee_organization_name",
                Concat(
                    "schedule_e__payee_last_name",
                    Value(", "),
                    "schedule_e__payee_first_name",
                    output_field=TextField(),
                ),
            ),
        )
    )
    serializer_class = ScheduleETransactionSerializer
    ordering_fields = [
        "id",
        "line_label_order_key",
        "transaction_type_identifier",
        "payee_name",
    ]

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
