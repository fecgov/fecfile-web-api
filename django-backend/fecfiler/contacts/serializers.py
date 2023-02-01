import logging

from django.db import transaction
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation import serializers
from rest_framework.serializers import (
    IntegerField,
    UUIDField,
    ModelSerializer,
)
from rest_framework.exceptions import ValidationError

from .models import Contact

logger = logging.getLogger(__name__)


class ContactSerializer(
    serializers.FecSchemaValidatorSerializerMixin, CommitteeOwnedSerializer
):
    contact_value = dict(
        COM="Committee",
        IND="Individual",
        ORG="Organization",
        CAN="Candidate",
    )

    # Contains the number of transactions linked to the contact
    transaction_count = IntegerField(required=False)

    def get_schema_name(self, data):
        return f"Contact_{self.contact_value[data.get('type', None)]}"

    class Meta:
        model = Contact
        fields = [
            f.name
            for f in Contact._meta.get_fields()
            if f.name
            not in [
                "deleted",
                "schatransaction",
                "scheduleatransaction",
                "schedulebtransaction",
                "transaction",
            ]
        ]
        fields.append("transaction_count")
        read_only_fields = [
            "uuid",
            "deleted",
            "created",
            "updated",
            "transaction_count",
        ]

    def to_internal_value(self, data):
        # Remove the transactin_count because it is an annotated field
        if "transaction_count" in data:
            del data["transaction_count"]
        return super().to_internal_value(data)


class LinkedContactSerializerMixin(ModelSerializer):
    contact = ContactSerializer(allow_null=True, required=False)
    contact_id = UUIDField(required=False, allow_null=False)

    def create(self, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact(validated_data)
            return super().create(validated_data)

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact(validated_data)
            return super().update(instance, validated_data)

    def create_or_update_contact(self, validated_data: dict):
        contact_data = validated_data.pop("contact", None)
        contact_id = validated_data.get("contact_id", None)
        if not contact_id:
            if not contact_data:
                raise ValidationError(
                    {"contact_id": ["No contact or contact id provided"]}
                )
            contact: Contact = Contact.objects.create(**contact_data)
            validated_data["contact_id"] = contact.id
        else:
            Contact.objects.filter(id=contact_id).update(**contact_data)
