import logging

from django.db import transaction
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.serializers import TransactionSerializerBase
from fecfiler.shared.utilities import get_model_data
from rest_framework.fields import DecimalField, CharField

logger = logging.getLogger(__name__)


class ScheduleC2TransactionSerializer(TransactionSerializerBase):
    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        transaction = TransactionSerializerBase(context=self.context).to_internal_value(
            data
        )
        internal.update(transaction)
        return internal

    def validate(self, data):
        self._context = self.context.copy()
        self._context["fields_to_ignore"] = self._context.get(
            "fields_to_ignore",
            ["filer_committee_id_number", "back_reference_tran_id_number"],
        )
        return super().validate(data)

    def create(self, validated_data: dict):
        with transaction.atomic():
            schedule_c2_data = get_model_data(validated_data, ScheduleC2)
            schedule_c2 = ScheduleC2.objects.create(**schedule_c2_data)
            transaction_data = validated_data.copy()
            transaction_data["schedule_c2_id"] = schedule_c2.id
            for key in schedule_c2_data.keys():
                if key != "id":
                    del transaction_data[key]

            schedule_c2_transaction = super().create(transaction_data)
            return schedule_c2_transaction

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.schedule_c2, attr, value)
            instance.schedule_c2.save()
            return super().update(instance, validated_data)

    guarantor_last_name = CharField(required=False, allow_null=True)
    guarantor_first_name = CharField(required=False, allow_null=True)
    guarantor_middle_name = CharField(required=False, allow_null=True)
    guarantor_prefix = CharField(required=False, allow_null=True)
    guarantor_suffix = CharField(required=False, allow_null=True)
    guarantor_street_1 = CharField(required=False, allow_null=True)
    guarantor_street_2 = CharField(required=False, allow_null=True)
    guarantor_city = CharField(required=False, allow_null=True)
    guarantor_state = CharField(required=False, allow_null=True)
    guarantor_zip = CharField(required=False, allow_null=True)
    guarantor_employer = CharField(required=False, allow_null=True)
    guarantor_occupation = CharField(required=False, allow_null=True)
    guaranteed_amount = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )

    class Meta(TransactionSerializerBase.Meta):
        fields = TransactionSerializerBase.Meta.get_fields() + [
            f.name
            for f in ScheduleC2._meta.get_fields()
            if f.name not in ["transaction"]
        ]
