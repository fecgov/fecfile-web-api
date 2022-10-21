import logging

from django.db import transaction
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.contacts.models import Contact
from fecfiler.contacts.serializers import ContactSerializer
from fecfiler.validation import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (BooleanField, DecimalField,
                                        ListSerializer, UUIDField)

from .models import SchATransaction

logger = logging.getLogger(__name__)


class SchATransactionSerializer(
    serializers.FecSchemaValidatorSerializerMixin, CommitteeOwnedSerializer
):
    parent_transaction_id = UUIDField(required=False, allow_null=True)

    report_id = UUIDField(required=True, allow_null=False)

    contact_id = UUIDField(required=False, allow_null=False)

    contact = ContactSerializer(write_only=True, allow_null=True, required=False)

    contribution_aggregate = DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )

    itemized = BooleanField(read_only=True)

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

    def validate(self, attrs):
        """Adds stub contribution_aggregate to pass validation"""
        attrs["contribution_aggregate"] = 0
        data = super().validate(attrs)
        del data["contribution_aggregate"]
        return data

    class Meta:
        model = SchATransaction
        fields = [
            f.name
            for f in SchATransaction._meta.get_fields()
            if f.name not in ["deleted", "schatransaction"]
        ] + [
            "parent_transaction_id",
            "report_id",
            "contact_id",
            "contribution_aggregate",
            "itemized",
            "fields_to_validate",
        ]

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
            self.create_or_update_contact(validated_data)
            children = validated_data.pop("children", [])
            parent = super().create(validated_data)
            for child in children:
                child["parent_transaction_id"] = parent.id
                self.create(child)
            return parent

    def update(self, instance: SchATransaction, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact(validated_data)
            children = validated_data.pop("children", [])

            existing_children = SchATransaction.objects.filter(
                parent_transaction_id=instance.id
            ).all()
            children_to_delete = [child.id for child in existing_children]
            for child in children:
                try:
                    """this will not make multiple db calls because
                    the existing_children queryset is cached
                    """
                    existing_child = existing_children.get(id=child.get("id", None))
                    children_to_delete.remove(existing_child.get("id", None))
                    self.update(existing_child, child)
                except SchATransaction.DoesNotExist:
                    self.create(child)
            print(f"children to delete: {children_to_delete}")
            SchATransaction.objects.filter(id__in=children_to_delete).delete()
            return super().update(instance, validated_data)

    def create_or_update_contact(self, validated_data: dict):
        contact_data = validated_data.pop("contact", None)
        tran_contact_id = validated_data.get("contact_id", None)
        if not tran_contact_id:
            if not contact_data:
                raise ValidationError(
                    {"contact_id": ["No transaction contact or contact id provided"]}
                )
            contact: Contact = Contact.objects.create(**contact_data)
            validated_data["contact_id"] = contact.id
        else:
            Contact.objects.update(**contact_data)

    class Meta(SchATransactionSerializer.Meta):
        fields = [
            f.name
            for f in SchATransaction._meta.get_fields()
            if f.name not in ["deleted", "schatransaction"]
        ] + [
            "parent_transaction_id",
            "report_id",
            "contact_id",
            "children",
            "contribution_aggregate",
            "itemized",
            "fields_to_validate",
        ]
