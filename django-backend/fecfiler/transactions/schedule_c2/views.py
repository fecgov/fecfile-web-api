import logging

from .serializers import ScheduleC2TransactionSerializer
from fecfiler.transactions.views import TransactionViewSet
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.managers import Schedule
from rest_framework.viewsets import ModelViewSet

logger = logging.getLogger(__name__)


class ScheduleC2TransactionViewSet(TransactionViewSet):
    queryset = Transaction.objects.select_related("schedule_c2").filter(
        schedule=Schedule.C2.value
    )
    serializer_class = ScheduleC2TransactionSerializer
    ordering_fields = [
        "id",
        "line_label",
        "transaction_type_identifier",
        "guarantor_last_name",
        "guarantor_first_name",
    ]

    def create(self, request):
        return super(ModelViewSet, self).create(request)

    def update(self, request, pk=None):
        return super(ModelViewSet, self).update(request, pk)

    def partial_update(self, request, pk=None):
        return super(ModelViewSet, self).partial_update(request, pk)
