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
                child["parent_transaction_id"] = parent.id
                self.create(child)
            return parent

    def update(self, instance: SchATransaction, validated_data: dict):
        with transaction.atomic():
            children = validated_data.pop("children", [])

            existing_children = SchATransaction.objects.filter(
                parent_transaction_id=instance.id
            ).all()
            children_to_delete = [child.id for child in existing_children]
            for child in children:
                try:
                    # this will not make multiple db calls because the existing_children queryset is cached
                    existing_child = existing_children.get(id=child.get("id", None))
                    children_to_delete.remove(existing_child.get("id", None))
                    self.update(existing_child, child)
                except SchATransaction.DoesNotExist:
                    self.create(child)
            print(f"children to delete: {children_to_delete}")
            SchATransaction.objects.filter(id__in=children_to_delete).delete()
            return super().update(instance, validated_data)

    class Meta(SchATransactionSerializer.Meta):
        fields = [
            f.name
            for f in SchATransaction._meta.get_fields()
            if f.name not in ["deleted", "schatransaction"]
        ] + ["parent_transaction_id", "report_id", "children"]
