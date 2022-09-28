from .models import SchATransaction
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation import serializers
from django.db import transaction
from rest_framework.serializers import UUIDField, ListSerializer
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class SchATransactionSerializer(
    CommitteeOwnedSerializer, serializers.FecSchemaValidatorSerializerMixin
):
    parent_transaction_id = UUIDField(required=False, allow_null=True)

    report_id = UUIDField(required=True, allow_null=False)

    def get_schema_name(self, data):
        transaction_type = data.get("transaction_type_identifier", None)
        if not transaction_type:
            raise ValidationError(
                {
                    "transaction_type_identifier": [
                        "No transaction_type_identifier provided"
                    ]
                }
            )
        return transaction_type

    class Meta:
        model = SchATransaction
        fields = [
            f.name
            for f in SchATransaction._meta.get_fields()
            if f.name not in ["deleted", "schatransaction"]
        ] + ["parent_transaction_id", "report_id"]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]


class SchATransactionParentSerializer(SchATransactionSerializer):
    children = ListSerializer(
        child=SchATransactionSerializer(),
        write_only=True,
        allow_null=True,
        allow_empty=True,
        required=False,
    )

    def create(self, validated_data: dict):
        with transaction.atomic():
            children = validated_data.pop("children", [])
            parent = super().create(validated_data)
            for child in children:
                logger.error(children)
                child.parent_transaction_id = parent.id
                super().create(child)
            return parent

    # def update(self, instance: SchATransaction, validated_data: dict):
    #     with transaction.atomic():
    #         children = validated_data.pop("children", [])
    #         super().update(instance, validated_data)

    class Meta(SchATransactionSerializer.Meta):
        fields = [
            f.name
            for f in SchATransaction._meta.get_fields()
            if f.name not in ["deleted", "schatransaction"]
        ] + ["parent_transaction_id", "report_id", "children"]
