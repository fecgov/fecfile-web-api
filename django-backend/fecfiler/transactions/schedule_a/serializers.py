import logging
from uuid import UUID

from django.db import transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.tasks import update_future_transaction_contacts
from fecfiler.transactions.serializers import TransactionSerializerBase
from rest_framework.fields import DecimalField, CharField, DateField
from rest_framework.serializers import ListSerializer

logger = logging.getLogger(__name__)


def get_model_data(data, model):
    return {
        field.name: data[field.name]
        for field in model._meta.get_fields()
        if field.name in data
    }


class ScheduleATransactionSerializerBase(TransactionSerializerBase):

    contribution_aggregate = DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )
    parent_transaction = TransactionSerializerBase(
        allow_null=True, required=False, read_only="True"
    )

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        transaction = TransactionSerializerBase(context=self.context).to_internal_value(
            data
        )
        print(f"internal {internal}")
        print(f"transaction {transaction}")
        internal.update(transaction)
        return internal

    def validate(self, data):
        """Adds stub contribution_aggregate to pass validation"""
        data["contribution_aggregate"] = 0
        validated_data = super().validate(data)
        del validated_data["contribution_aggregate"]
        return validated_data

    class Meta(TransactionSerializerBase.Meta):
        fields = (
            TransactionSerializerBase.Meta.get_fields()
            + [
                f.name
                for f in ScheduleA._meta.get_fields()
                if f.name not in ["transaction"]
            ]
            + ["contribution_aggregate"]
        )

    contributor_organization_name = CharField(required=False, allow_null=True)
    contributor_last_name = CharField(required=False, allow_null=True)
    contributor_first_name = CharField(required=False, allow_null=True)
    contributor_middle_name = CharField(required=False, allow_null=True)
    contributor_prefix = CharField(required=False, allow_null=True)
    contributor_suffix = CharField(required=False, allow_null=True)
    contributor_street_1 = CharField(required=False, allow_null=True)
    contributor_street_2 = CharField(required=False, allow_null=True)
    contributor_city = CharField(required=False, allow_null=True)
    contributor_state = CharField(required=False, allow_null=True)
    contributor_zip = CharField(required=False, allow_null=True)

    contribution_date = DateField(required=False, allow_null=True)
    contribution_amount = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )

    contribution_purpose_descrip = CharField(required=False, allow_null=True)
    contributor_employer = CharField(required=False, allow_null=True)
    contributor_occupation = CharField(required=False, allow_null=True)
    donor_committee_fec_id = CharField(required=False, allow_null=True)
    donor_committee_name = CharField(required=False, allow_null=True)
    donor_candidate_fec_id = CharField(required=False, allow_null=True)
    donor_candidate_last_name = CharField(required=False, allow_null=True)
    donor_candidate_first_name = CharField(required=False, allow_null=True)
    donor_candidate_middle_name = CharField(required=False, allow_null=True)
    donor_candidate_prefix = CharField(required=False, allow_null=True)
    donor_candidate_suffix = CharField(required=False, allow_null=True)
    donor_candidate_office = CharField(required=False, allow_null=True)
    donor_candidate_state = CharField(required=False, allow_null=True)
    donor_candidate_district = CharField(required=False, allow_null=True)

    election_code = CharField(required=False, allow_null=True)
    election_other_description = CharField(required=False, allow_null=True)
    conduit_name = CharField(required=False, allow_null=True)
    conduit_street_1 = CharField(required=False, allow_null=True)
    conduit_street_2 = CharField(required=False, allow_null=True)
    conduit_city = CharField(required=False, allow_null=True)
    conduit_state = CharField(required=False, allow_null=True)
    conduit_zip = CharField(required=False, allow_null=True)

    memo_text_description = CharField(required=False, allow_null=True)
    reference_to_si_or_sl_system_code_that_identifies_the_account = CharField(
        required=False, allow_null=True
    )


class ScheduleATransactionSerializer(ScheduleATransactionSerializerBase):

    children = ListSerializer(
        child=ScheduleATransactionSerializerBase(),
        allow_null=True,
        allow_empty=True,
        required=False,
    )

    def create(self, validated_data: dict):
        with transaction.atomic():
            schedule_a_data = get_model_data(validated_data, ScheduleA)
            schedule_a = ScheduleA.objects.create(**schedule_a_data)
            transaction_data = validated_data.copy()
            transaction_data["schedule_a_id"] = schedule_a.id
            for key in schedule_a_data.keys():
                if key != "id":
                    del transaction_data[key]

            children = transaction_data.pop("children", [])
            parent = super().create(transaction_data)
            for child in children:
                child["parent_transaction_id"] = parent.id
                self.create(child)

            if hasattr(self, 'contact_updated') and self.contact_updated:
                self.execute_update_future_transaction_contacts_task(
                    validated_data.get('contact_id'), schedule_a_data
                )
            return parent

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            schedule_a_data = get_model_data(validated_data, ScheduleA)
            children = validated_data.pop("children", [])

            for child in children:
                try:
                    existing_child = instance.children.get(id=child.get("id", None))
                    self.update(existing_child, child)
                except Transaction.DoesNotExist:
                    self.create(child)

            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.schedule_a, attr, value)
            instance.schedule_a.save()
            updated = super().update(instance, validated_data)
            if hasattr(self, 'contact_updated') and self.contact_updated:
                self.execute_update_future_transaction_contacts_task(
                    validated_data.get('contact_id'), schedule_a_data
                )
            return updated

    def execute_update_future_transaction_contacts_task(self, contact_id: UUID, scha_transaction: dict):
        update_future_transaction_contacts.s(contact_id, scha_transaction).apply_async(retry=False)

    class Meta(TransactionSerializerBase.Meta):
        fields = (
            TransactionSerializerBase.Meta.get_fields()
            + [
                f.name
                for f in ScheduleA._meta.get_fields()
                if f.name not in ["transaction"]
            ]
            + ["contribution_aggregate", "children"]
        )
