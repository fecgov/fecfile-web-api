import logging

from django.db import transaction
from django.db.models import Q
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
    id = UUIDField(required=False)
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

    def validate(self, data):
        matches = (
            Contact.objects.exclude(id=data.get("id"))
            .filter(committee_account=data.get("committee_account"))
            .filter(
                Q(candidate_id=data.get("candidate_id"), candidate_id__isnull=False)
                | Q(committee_id=data.get("committee_id"), committee_id__isnull=False)
            )
            .count()
        )
        if matches != 0:
            raise ValidationError({"fec_id": ["FEC Ids must be unique"]})
        return super().validate(data)

    class Meta:
        model = Contact
        fields = [
            f.name
            for f in Contact._meta.get_fields()
            if f.name
            not in [
                "deleted",
                "transaction",
                "contact_1_transaction_set",
                "contact_2_transaction_set",
                "contact_3_transaction_set",
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
    contact_3 = ContactSerializer(allow_null=True, required=False)
    contact_3_id = UUIDField(required=False, allow_null=True)

    def create(self, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact(validated_data, "contact_1")
            if validated_data.get("contact_2") or validated_data.get("contact_2_id"):
                self.create_or_update_contact(validated_data, "contact_2")
            if validated_data.get("contact_3") or validated_data.get("contact_3_id"):
                self.create_or_update_contact(validated_data, "contact_3")
            return super().create(validated_data)

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact(validated_data, "contact_1")
            if validated_data.get("contact_2") or validated_data.get("contact_2_id"):
                self.create_or_update_contact(validated_data, "contact_2")
            if validated_data.get("contact_3") or validated_data.get("contact_3_id"):
                self.create_or_update_contact(validated_data, "contact_3")
            return super().update(instance, validated_data)

    def create_or_update_contact(self, validated_data: dict, contact_key):
        contact_data = validated_data.pop(contact_key, None)
        contact_id = validated_data.get(contact_key + "_id", None)

        if not contact_id:
            if not contact_data:
                raise ValidationError(
                    {"contact_id": ["No contact or contact id provided"]}
                )
            contact: Contact = Contact.objects.create(**contact_data)
            validated_data[contact_key + "_id"] = contact.id
        elif contact_data:
            Contact.objects.filter(id=contact_id).update(**contact_data)
