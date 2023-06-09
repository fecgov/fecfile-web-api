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
                "contact_1_transaction_set",
                "contact_2_transaction_set",
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
        # Remove the transaction_count because it is an annotated field
        # delivered to the front end.
        if "transaction_count" in data:
            del data["transaction_count"]
        return super().to_internal_value(data)


class LinkedContactSerializerMixin(ModelSerializer):
    contact_1 = ContactSerializer(allow_null=True, required=False)
    contact_1_id = UUIDField(required=False, allow_null=False)
    contact_2 = ContactSerializer(allow_null=True, required=False)
    contact_2_id = UUIDField(required=False, allow_null=True)

    def create(self, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact(validated_data, "contact_1")
            if validated_data.get("contact_2") or validated_data.get("contact_2_id"):
                self.create_or_update_contact(validated_data, "contact_2")
            return super().create(validated_data)

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact(validated_data, "contact_1")
            if validated_data.get("contact_2") or validated_data.get("contact_2_id"):
                self.create_or_update_contact(validated_data, "contact_2")
            return super().update(instance, validated_data)

    def create_or_update_contact(self, validated_data: dict, contact_key):
        print(f"AHOY: {validated_data}")
        contact_data = validated_data.pop(contact_key, None)
        contact_id = validated_data.get(contact_key + "_id", None)
        if not contact_id:
            if not contact_data:
                raise ValidationError(
                    {"contact_id": ["No contact or contact id provided"]}
                )
            contact: Contact = Contact.objects.create(**contact_data)
            validated_data[contact_key + "_id"] = contact.id
        else:
            Contact.objects.filter(id=contact_id).update(**contact_data)
