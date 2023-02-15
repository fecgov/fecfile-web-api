import logging

from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.contacts.serializers import LinkedContactSerializerMixin
from fecfiler.memo_text.serializers import LinkedMemoTextSerializerMixin
from fecfiler.f3x_summaries.serializers import F3XSummarySerializer
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    BooleanField,
    UUIDField,
    CharField,
    DateField,
    ModelSerializer,
    DecimalField,
)
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB


logger = logging.getLogger(__name__)
MISSING_SCHEMA_NAME_ERROR = ValidationError(
    {"schema_name": ["No schema_name provided"]}
)


class ScheduleASerializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ScheduleA._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ]
        model = ScheduleA


class ScheduleBSerializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ScheduleB._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ]
        model = ScheduleB


class TransactionSerializerBase(
    LinkedContactSerializerMixin,
    LinkedMemoTextSerializerMixin,
    FecSchemaValidatorSerializerMixin,
    CommitteeOwnedSerializer,
):
    """id must be explicitly configured in order to have it in validated_data
    https://github.com/encode/django-rest-framework/issues/2320#issuecomment-67502474"""

    id = UUIDField(required=False)
    parent_transaction_id = UUIDField(required=False, allow_null=True)
    transaction_id = CharField(required=False, allow_null=True)
    report_id = UUIDField(required=True, allow_null=False)
    report = F3XSummarySerializer(read_only=True)
    itemized = BooleanField(read_only=True)
    date = DateField(read_only=True)
    amount = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    aggregate = DecimalField(max_digits=11, decimal_places=2, read_only=True)

    schedule_a = ScheduleASerializer(required=False)
    schedule_b = ScheduleBSerializer(required=False)

    def get_schema_name(self, data):
        schema_name = data.get("schema_name", None)
        if not schema_name:
            raise MISSING_SCHEMA_NAME_ERROR
        return schema_name

    def to_representation(self, instance, depth=0):
        representation = super().to_representation(instance)
        schedule_a = representation.pop("schedule_a") or []
        schedule_b = representation.pop("schedule_b") or []
        if depth < 1:
            if instance.parent_transaction:
                representation["parent_transaction"] = self.to_representation(
                    instance.parent_transaction, depth + 1
                )
            children = instance.transaction_set.all()
            if children:
                representation["children"] = [
                    self.to_representation(child, depth + 1) for child in children
                ]

        if schedule_a:
            representation["contribution_aggregate"] = representation.get("aggregate")
            for property in schedule_a:
                if not representation.get(property):
                    representation[property] = schedule_a[property]
        if schedule_b:
            representation["aggregate_amount"] = representation.get("aggregate")
            for property in schedule_b:
                if not representation.get(property):
                    representation[property] = schedule_b[property]
        return representation

    def to_internal_value(self, data):
        return super().to_internal_value(data)

    class Meta:
        model = Transaction

        def get_fields():
            return [
                f.name
                for f in Transaction._meta.get_fields()
                if f.name not in ["deleted", "transaction"]
            ] + [
                "parent_transaction_id",
                "report_id",
                "contact_id",
                "memo_text_id",
                "itemized",
                "fields_to_validate",
                "schema_name",
                "date",
                "amount",
                "aggregate",
                "schedule_a",
                "schedule_b",
            ]

        fields = get_fields()
        read_only_fields = ["parent_transaction"]


TransactionSerializerBase.parent_transaction = TransactionSerializerBase(
    allow_null=True, required=False, read_only="True"
)
