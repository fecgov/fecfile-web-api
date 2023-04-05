import logging

from django.db import transaction
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.serializers import TransactionSerializerBase
from rest_framework.fields import DecimalField, CharField, DateField
from rest_framework.serializers import ListSerializer

logger = logging.getLogger(__name__)

transaction_contact_attributes = [
    'payee_organization_name',
    'payee_last_name',
    'payee_first_name',
    'payee_middle_name',
    'payee_prefix',
    'payee_suffix',
    'payee_street_1',
    'payee_street_2',
    'payee_city',
    'payee_state',
    'payee_zip',
    'beneficiary_committee_fec_id',
    'beneficiary_committee_fec_id',
    'beneficiary_committee_name',
]

transaction_date_attribute_name = 'expenditure_date'


def get_model_data(data, model):
    return {
        field.name: data[field.name]
        for field in model._meta.get_fields()
        if field.name in data
    }


class ScheduleBTransactionSerializerBase(TransactionSerializerBase):

    aggregate_amount = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    parent_transaction = TransactionSerializerBase(
        allow_null=True, required=False, read_only="True"
    )

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        transaction = TransactionSerializerBase(context=self.context).to_internal_value(
            data
        )
        internal.update(transaction)
        return internal

    def validate(self, data):
        """Adds stub aggregate_amount to pass validation"""
        data["aggregate_amount"] = 0
        validated_data = super().validate(data)
        del validated_data["aggregate_amount"]
        return validated_data

    class Meta(TransactionSerializerBase.Meta):
        fields = (
            TransactionSerializerBase.Meta.get_fields()
            + [
                f.name
                for f in ScheduleB._meta.get_fields()
                if f.name not in ["transaction"]
            ]
            + ["aggregate_amount"]
        )

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

    expenditure_date = DateField(required=False, allow_null=True)
    expenditure_amount = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )

    expenditure_purpose_descrip = CharField(required=False, allow_null=True)

    election_code = CharField(required=False, allow_null=True)
    election_other_description = CharField(required=False, allow_null=True)
    conduit_name = CharField(required=False, allow_null=True)
    conduit_street_1 = CharField(required=False, allow_null=True)
    conduit_street_2 = CharField(required=False, allow_null=True)
    conduit_city = CharField(required=False, allow_null=True)
    conduit_state = CharField(required=False, allow_null=True)
    conduit_zip = CharField(required=False, allow_null=True)

    category_code = CharField(required=False, allow_null=True)

    beneficiary_committee_fec_id = CharField(required=False, allow_null=True)
    beneficiary_committee_name = CharField(required=False, allow_null=True)
    beneficiary_candidate_fec_id = CharField(required=False, allow_null=True)
    beneficiary_candidate_last_name = CharField(required=False, allow_null=True)
    beneficiary_candidate_first_name = CharField(required=False, allow_null=True)
    beneficiary_candidate_middle_name = CharField(required=False, allow_null=True)
    beneficiary_candidate_prefix = CharField(required=False, allow_null=True)
    beneficiary_candidate_suffix = CharField(required=False, allow_null=True)
    beneficiary_candidate_office = CharField(required=False, allow_null=True)
    beneficiary_candidate_state = CharField(required=False, allow_null=True)
    beneficiary_candidate_district = CharField(required=False, allow_null=True)

    memo_text_description = CharField(required=False, allow_null=True)
    reference_to_si_or_sl_system_code_that_identifies_the_account = CharField(
        required=False, allow_null=True
    )


class ScheduleBTransactionSerializer(ScheduleBTransactionSerializerBase):

    children = ListSerializer(
        child=ScheduleBTransactionSerializerBase(),
        allow_null=True,
        allow_empty=True,
        required=False,
    )

    def create(self, validated_data: dict):
        with transaction.atomic():
            schedule_b_data = get_model_data(validated_data, ScheduleB)
            schedule_b = ScheduleB.objects.create(**schedule_b_data)
            transaction_data = validated_data.copy()
            transaction_data["schedule_b_id"] = schedule_b.id
            for key in schedule_b_data.keys():
                if key != "id":
                    del transaction_data[key]

            children = transaction_data.pop("children", [])
            parent = super().create(transaction_data)
            for child in children:
                child["parent_transaction_id"] = parent.id
                self.create(child)
            super().update_future_schedule_contacts_if_needed(
                validated_data.get('contact_id'),
                schedule_b,
                transaction_contact_attributes,
                schedule_b_data,
                transaction_date_attribute_name
            )
            return parent

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            schedule_b_data = get_model_data(validated_data, ScheduleB)
            children = validated_data.pop("children", [])

            for child in children:
                try:
                    existing_child = instance.children.get(id=child.get("id", None))
                    self.update(existing_child, child)
                except Transaction.DoesNotExist:
                    self.create(child)

            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.schedule_b, attr, value)
            instance.schedule_b.save()
            updated = super().update(instance, validated_data)
            super().update_future_schedule_contacts_if_needed(
                validated_data.get('contact_id'),
                instance.schedule_b,
                transaction_contact_attributes,
                schedule_b_data,
                transaction_date_attribute_name
            )
            return updated

    class Meta(TransactionSerializerBase.Meta):
        fields = (
            TransactionSerializerBase.Meta.get_fields()
            + [
                f.name
                for f in ScheduleB._meta.get_fields()
                if f.name not in ["transaction"]
            ]
            + ["aggregate_amount", "children"]
        )
