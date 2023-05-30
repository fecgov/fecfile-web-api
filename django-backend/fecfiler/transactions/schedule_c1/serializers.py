import logging

from django.db import transaction
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.serializers import TransactionSerializerBase
from rest_framework.fields import DecimalField, CharField, DateField, BooleanField

logger = logging.getLogger(__name__)


def get_model_data(data, model):
    return {
        field.name: data[field.name]
        for field in model._meta.get_fields()
        if field.name in data
    }


class ScheduleC1TransactionSerializer(TransactionSerializerBase):
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
            schedule_c1_data = get_model_data(validated_data, ScheduleC1)
            schedule_c1 = ScheduleC1.objects.create(**schedule_c1_data)
            transaction_data = validated_data.copy()
            transaction_data["schedule_c1_id"] = schedule_c1.id
            for key in schedule_c1_data.keys():
                if key != "id":
                    del transaction_data[key]

            schedule_c1_transaction = super().create(transaction_data)
            return schedule_c1_transaction

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.schedule_c1, attr, value)
            instance.schedule_c1.save()
            return super().update(instance, validated_data)

    lender_organization_name = CharField(required=False, allow_null=True)
    lender_street_1 = CharField(required=False, allow_null=True)
    lender_street_2 = CharField(required=False, allow_null=True)
    lender_city = CharField(required=False, allow_null=True)
    lender_state = CharField(required=False, allow_null=True)
    lender_zip = CharField(required=False, allow_null=True)
    loan_amount = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    loan_interest_rate = DecimalField(
        required=False, allow_null=True, max_digits=14, decimal_places=14
    )
    loan_incurred_date = DateField(required=False, allow_null=True)
    loan_due_date = DateField(required=False, allow_null=True)
    loan_restructured = BooleanField(required=False, allow_null=True, default=False)
    loan_originally_incurred_date = DateField(required=False, allow_null=True)
    credit_amount_this_draw = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    total_balance = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    others_liable = BooleanField(required=False, allow_null=True, default=False)
    collateral = BooleanField(required=False, allow_null=True, default=False)
    desc_collateral = CharField(required=False, allow_null=True)
    collateral_value_amount = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    perfected_interest = BooleanField(required=False, allow_null=True, default=False)
    future_income = BooleanField(required=False, allow_null=True, default=False)
    desc_specification_of_the_above = CharField(required=False, allow_null=True)
    estimated_value = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    depository_account_established_date = DateField(required=False, allow_null=True)
    ind_name_account_location = CharField(required=False, allow_null=True)
    account_street_1 = CharField(required=False, allow_null=True)
    account_street_2 = CharField(required=False, allow_null=True)
    account_city = CharField(required=False, allow_null=True)
    account_state = CharField(required=False, allow_null=True)
    account_zip = CharField(required=False, allow_null=True)
    dep_acct_auth_date_presidential = DateField(required=False, allow_null=True)
    basis_of_loan_description = CharField(required=False, allow_null=True)
    treasurer_last_name = CharField(required=False, allow_null=True)
    treasurer_first_name = CharField(required=False, allow_null=True)
    treasurer_middle_name = CharField(required=False, allow_null=True)
    treasurer_prefix = CharField(required=False, allow_null=True)
    treasurer_suffix = CharField(required=False, allow_null=True)
    treasurer_date_signed = DateField(required=False, allow_null=True)
    authorized_last_name = CharField(required=False, allow_null=True)
    authorized_first_name = CharField(required=False, allow_null=True)
    authorized_middle_name = CharField(required=False, allow_null=True)
    authorized_prefix = CharField(required=False, allow_null=True)
    authorized_suffix = CharField(required=False, allow_null=True)
    authorized_title = CharField(required=False, allow_null=True)
    authorized_date_signed = DateField(required=False, allow_null=True)

    class Meta(TransactionSerializerBase.Meta):
        fields = TransactionSerializerBase.Meta.get_fields() + [
            f.name
            for f in ScheduleC1._meta.get_fields()
            if f.name not in ["transaction"]
        ]
