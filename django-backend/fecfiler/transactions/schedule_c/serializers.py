import logging

from django.db import transaction
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.serializers import TransactionSerializerBase
from fecfiler.shared.utilities import get_model_data
from rest_framework.fields import DecimalField, CharField, DateField, BooleanField

logger = logging.getLogger(__name__)


class ScheduleCTransactionSerializer(TransactionSerializerBase):
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
            schedule_c_data = get_model_data(validated_data, ScheduleC)
            schedule_c = ScheduleC.objects.create(**schedule_c_data)
            transaction_data = validated_data.copy()
            transaction_data["schedule_c_id"] = schedule_c.id
            for key in schedule_c_data.keys():
                if key != "id":
                    del transaction_data[key]

            schedule_c_transaction = super().create(transaction_data)
            return schedule_c_transaction

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.schedule_c, attr, value)
            instance.schedule_c.save()
            return super().update(instance, validated_data)

    receipt_line_number = CharField(required=False, allow_null=True)
    lender_organization_name = CharField(required=False, allow_null=True)
    lender_last_name = CharField(required=False, allow_null=True)
    lender_first_name = CharField(required=False, allow_null=True)
    lender_middle_name = CharField(required=False, allow_null=True)
    lender_prefix = CharField(required=False, allow_null=True)
    lender_suffix = CharField(required=False, allow_null=True)
    lender_street_1 = CharField(required=False, allow_null=True)
    lender_street_2 = CharField(required=False, allow_null=True)
    lender_city = CharField(required=False, allow_null=True)
    lender_state = CharField(required=False, allow_null=True)
    lender_zip = CharField(required=False, allow_null=True)
    election_code = CharField(required=False, allow_null=True)
    election_other_description = CharField(required=False, allow_null=True)
    loan_amount = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    loan_payment_to_date = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    loan_balance = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    loan_incurred_date = DateField(required=False, allow_null=True)
    loan_due_date = CharField(required=False, allow_null=True)
    loan_interest_rate = CharField(required=False, allow_null=True)
    secured = BooleanField(required=False, allow_null=True, default=False)
    personal_funds = BooleanField(required=False, allow_null=True, default=False)
    lender_committee_id_number = CharField(required=False, allow_null=True)
    lender_candidate_id_number = CharField(required=False, allow_null=True)
    lender_candidate_last_name = CharField(required=False, allow_null=True)
    lender_candidate_first_name = CharField(required=False, allow_null=True)
    lender_candidate_middle_name = CharField(required=False, allow_null=True)
    lender_candidate_prefix = CharField(required=False, allow_null=True)
    lender_candidate_suffix = CharField(required=False, allow_null=True)
    lender_candidate_office = CharField(required=False, allow_null=True)
    lender_candidate_state = CharField(required=False, allow_null=True)
    lender_candidate_district = CharField(required=False, allow_null=True)
    memo_text_description = CharField(required=False, allow_null=True)

    class Meta(TransactionSerializerBase.Meta):
        fields = (
            TransactionSerializerBase.Meta.get_fields()
            + [
                f.name
                for f in ScheduleC._meta.get_fields()
                if f.name not in ["transaction"]
            ]
            + ["loan_balance", "loan_payment_to_date"]
        )
