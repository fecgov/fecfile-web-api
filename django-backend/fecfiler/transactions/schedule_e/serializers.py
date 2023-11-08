import logging

from django.db import transaction
from fecfiler.transactions.schedule_e.models import ScheduleE
from fecfiler.transactions.serializers import TransactionSerializerBase
from fecfiler.shared.utilities import get_model_data
from rest_framework.fields import DecimalField, CharField, DateField

logger = logging.getLogger(__name__)


class ScheduleETransactionSerializer(TransactionSerializerBase):
    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        transaction = TransactionSerializerBase(context=self.context).to_internal_value(
            data
        )
        internal.update(transaction)
        return internal

    def validate(self, data):
        """Adds stub aggregate_amount to pass validation"""
        validated_data = super().validate(data)
        return validated_data

    def create(self, validated_data: dict):
        with transaction.atomic():
            schedule_e_data = get_model_data(validated_data, ScheduleE)
            schedule_e = ScheduleE.objects.create(**schedule_e_data)
            transaction_data = validated_data.copy()
            transaction_data["schedule_e_id"] = schedule_e.id
            for key in schedule_e_data.keys():
                if key != "id":
                    del transaction_data[key]

            schedule_e_transaction = super().create(transaction_data)
            return schedule_e_transaction

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.schedule_e, attr, value)
            instance.schedule_e.save()
            return super().update(instance, validated_data)

    payee_organization_name = CharField(required=False, allow_null=True)
    payee_last_name = CharField(required=False, allow_null=True)
    payee_first_name = CharField(required=False, allow_null=True)
    payee_middle_name = CharField(required=False, allow_null=True)
    payee_prefix = CharField(required=False, allow_null=True)
    payee_suffix = CharField(required=False, allow_null=True)
    payee_street_1 = CharField(required=False, allow_null=True)
    payee_street_2 = CharField(required=False, allow_null=True)
    payee_city = CharField(required=False, allow_null=True)
    payee_state = CharField(required=False, allow_null=True)
    payee_zip = CharField(required=False, allow_null=True)
    election_code = CharField(required=False, allow_null=True)
    election_other_description = CharField(required=False, allow_null=True)
    dissemination_date = DateField(required=False, allow_null=True)
    expenditure_amount = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    disbursement_date = DateField(required=False, allow_null=True)
    calendar_ytd_per_election_office = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    expenditure_purpose_descrip = CharField(required=False, allow_null=True)
    category_code = CharField(required=False, allow_null=True)
    payee_cmtte_fec_id_number = CharField(required=False, allow_null=True)
    support_oppose_code = CharField(required=False, allow_null=True)
    so_candidate_id_number = CharField(required=False, allow_null=True)
    so_candidate_last_name = CharField(required=False, allow_null=True)
    so_candidate_first_name = CharField(required=False, allow_null=True)
    so_candidate_middle_name = CharField(required=False, allow_null=True)
    so_candidate_prefix = CharField(required=False, allow_null=True)
    so_candidate_suffix = CharField(required=False, allow_null=True)
    so_candidate_office = CharField(required=False, allow_null=True)
    so_candidate_district = CharField(required=False, allow_null=True)
    so_candidate_state = CharField(required=False, allow_null=True)
    completing_last_name = CharField(required=False, allow_null=True)
    completing_first_name = CharField(required=False, allow_null=True)
    completing_middle_name = CharField(required=False, allow_null=True)
    completing_prefix = CharField(required=False, allow_null=True)
    completing_suffix = CharField(required=False, allow_null=True)
    date_signed = DateField(required=False, allow_null=True)
    memo_text_description = CharField(required=False, allow_null=True)

    class Meta(TransactionSerializerBase.Meta):
        fields = TransactionSerializerBase.Meta.get_fields() + [
            f.name
            for f in ScheduleE._meta.get_fields()
            if f.name not in ["transaction"]
        ]
