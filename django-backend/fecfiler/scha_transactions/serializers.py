import logging

from django.db import transaction
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.contacts.models import Contact
from fecfiler.validation import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import CharField, UUIDField

from .models import SchATransaction

logger = logging.getLogger(__name__)


class SchATransactionSerializer(
    CommitteeOwnedSerializer, serializers.FecSchemaValidatorSerializerMixin
):
    parent_transaction_id = UUIDField(required=False, allow_null=True)
    transaction_id = CharField(
        required=True, max_length=20, allow_blank=False, allow_null=True
    )

    report_id = UUIDField(required=True, allow_null=False)

    contact_id = UUIDField(required=False)

    def create(self, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact_for_transaction(validated_data)
            return super().create(validated_data)

    def update(self, instance: Contact, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact_for_transaction(validated_data)
            return super().update(instance, validated_data)

    def create_or_update_contact_for_transaction(self, transaction: dict):
        contact_id = transaction.get("contact_id")
        if contact_id:
            contact = Contact.objects.get(id=contact_id)
        else:
            contact = Contact(
                type=transaction['entity_type'],
                country="USA",  # TODO confirm
            )
        self.update_contact_for_transaction(contact, transaction)

    def update_contact_for_transaction(self, contact: Contact, transaction: dict):
        if contact and transaction:
            if ((contact.type == Contact.ContactType.INDIVIDUAL)
                    and (transaction["entity_type"] == "IND")):
                if contact.last_name != transaction["contributor_last_name"]:
                    contact.last_name = transaction["contributor_last_name"]
                if contact.first_name != transaction["contributor_first_name"]:
                    contact.first_name = transaction["contributor_first_name"]
                if contact.middle_name != transaction["contributor_middle_name"]:
                    contact.middle_name = transaction["contributor_middle_name"]
                if contact.prefix != transaction["contributor_prefix"]:
                    contact.prefix = transaction["contributor_prefix"]
                if contact.suffix != transaction["contributor_suffix"]:
                    contact.suffix = transaction["contributor_suffix"]
                if contact.employer != transaction["contributor_employer"]:
                    contact.employer = transaction["contributor_employer"]
                if contact.occupation != transaction["contributor_occupation"]:
                    contact.occupation = transaction["contributor_occupation"]
            elif ((contact.type == Contact.ContactType.COMMITTEE)
                  and (transaction["entity_type"] == "COM")):
                if contact.committee_id != transaction.get("donor_committee_fec_id", None):
                    contact.committee_id = transaction.get("donor_committee_fec_id", None)
                if contact.name != transaction["contributor_organization_name"]:
                    contact.name = transaction["contributor_organization_name"]
            elif ((contact.type == Contact.ContactType.ORGANIZATION)
                  and (transaction["entity_type"] == "ORG")):
                if contact.name != transaction["contributor_organization_name"]:
                    contact.name = transaction["contributor_organization_name"]

            if contact.street_1 != transaction["contributor_street_1"]:
                contact.street_1 = transaction["contributor_street_1"]
            if contact.street_2 != transaction["contributor_street_2"]:
                contact.street_2 = transaction["contributor_street_2"]
            if contact.city != transaction["contributor_city"]:
                contact.city = transaction["contributor_city"]
            if contact.state != transaction["contributor_state"]:
                contact.state = transaction["contributor_state"]
            if contact.zip != transaction["contributor_zip"]:
                contact.zip = transaction["contributor_zip"]
            contact.save()
            transaction["contact_id"] = contact.id

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
        ] + ["parent_transaction_id", "report_id", "contact_id"]

        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
