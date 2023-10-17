import logging

from django.db.models.functions import Coalesce, Concat
from .serializers import ScheduleCTransactionSerializer
from fecfiler.transactions.views import TransactionViewSet
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.managers import Schedule
from django.db.models import TextField, Value
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class ScheduleCTransactionViewSet(TransactionViewSet):
    queryset = (
        Transaction.objects.select_related("schedule_c")
        .filter(schedule=Schedule.C.value)
        .alias(
            lender_name=Coalesce(
                "schedule_c__lender_organization_name",
                Concat(
                    "schedule_c__lender_last_name",
                    Value(", "),
                    "schedule_c__lender_first_name",
                    output_field=TextField(),
                ),
            ),
        )
    )
    serializer_class = ScheduleCTransactionSerializer
    ordering_fields = [
        "id",
        "line_label",
        "transaction_type_identifier",
        "lender_name",
        "memo_code",
    ]

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
