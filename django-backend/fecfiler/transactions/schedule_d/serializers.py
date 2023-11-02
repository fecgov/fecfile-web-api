from decimal import Decimal
import logging

from django.db import transaction, models
from django.db.models import Q
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.serializers import TransactionSerializerBase
from fecfiler.shared.utilities import get_model_data
from rest_framework.fields import DecimalField, CharField
import copy

logger = logging.getLogger(__name__)


class ScheduleDTransactionSerializer(TransactionSerializerBase):
    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        transaction = TransactionSerializerBase(context=self.context).to_internal_value(
            data
        )
        internal.update(transaction)
        return internal

    def validate(self, data):
        """Adds stub aggregate_amount to pass validation"""
        data["beginning_balance"] = 0
        validated_data = super().validate(data)
        del validated_data["beginning_balance"]
        return validated_data

    def create(self, validated_data: dict):
        with transaction.atomic():
            schedule_d_data = get_model_data(validated_data, ScheduleD)
            schedule_d = ScheduleD.objects.create(**schedule_d_data)
            transaction_data = validated_data.copy()
            transaction_data["schedule_d_id"] = schedule_d.id
            for key in schedule_d_data.keys():
                if key != "id":
                    del transaction_data[key]

            schedule_d_transaction = super().create(transaction_data)
            if Transaction.objects.filter(
                ~Q(balance_at_close=Decimal(0)) | Q(balance_at_close__isnull=True),
                id=schedule_d_transaction.id,
            ).count():
                self.create_in_future_reports(schedule_d_transaction)
            return schedule_d_transaction

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.schedule_d, attr, value)
            instance.schedule_d.save()
            schedule_d_transaction = super().update(instance, validated_data)
            self.update_in_future_reports(schedule_d_transaction, validated_data)
            return schedule_d_transaction

    def create_in_future_reports(self, transaction: Transaction):
        future_reports = super().get_future_in_progress_reports(transaction.report)
        transaction_copy = copy.deepcopy(transaction)
        for report in future_reports:
            report.pull_forward_debt(transaction_copy)

    def update_in_future_reports(self, transaction: Transaction, validated_data: dict):
        future_reports = super().get_future_in_progress_reports(transaction.report)

        transaction_data = get_model_data(validated_data, Transaction)
        del transaction_data['id']
        transactions_to_update = Transaction.objects.filter(
            transaction_id=transaction.transaction_id,
            report_id__in=models.Subquery(
                future_reports.values('id')
            )
        )
        transactions_to_update.update(**transaction_data)

        schedule_d_data = get_model_data(validated_data, ScheduleD)
        del schedule_d_data['id']
        if "incurred_amount" in schedule_d_data:
            del schedule_d_data['incurred_amount']
        schedule_ds_to_update = ScheduleD.objects.filter(
            transaction__schedule_d_id__in=models.Subquery(
                transactions_to_update.values('schedule_d_id')
            )
        )
        schedule_ds_to_update.update(**schedule_d_data)

    receipt_line_number = CharField(required=False, allow_null=True)
    receipt_line_number = CharField(required=False, allow_null=True)
    creditor_organization_name = CharField(required=False, allow_null=True)
    creditor_last_name = CharField(required=False, allow_null=True)
    creditor_first_name = CharField(required=False, allow_null=True)
    creditor_middle_name = CharField(required=False, allow_null=True)
    creditor_prefix = CharField(required=False, allow_null=True)
    creditor_suffix = CharField(required=False, allow_null=True)
    creditor_street_1 = CharField(required=False, allow_null=True)
    creditor_street_2 = CharField(required=False, allow_null=True)
    creditor_city = CharField(required=False, allow_null=True)
    creditor_state = CharField(required=False, allow_null=True)
    creditor_zip = CharField(required=False, allow_null=True)
    purpose_of_debt_or_obligation = CharField(required=False, allow_null=True)
    beginning_balance = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2, read_only=True
    )
    incurred_amount = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    payment_amount = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2, read_only=True
    )
    balance_at_close = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2, read_only=True
    )

    class Meta(TransactionSerializerBase.Meta):
        fields = (
            TransactionSerializerBase.Meta.get_fields()
            + [
                f.name
                for f in ScheduleD._meta.get_fields()
                if f.name not in ["transaction"]
            ]
            + ["beginning_balance", "payment_amount", "balance_at_close"]
        )
