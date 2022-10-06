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
                contributor_last_name = transaction.get("contributor_last_name")
                if (contact.last_name != contributor_last_name):
                    contact.last_name = contributor_last_name
                contributor_first_name = transaction.get("contributor_first_name")
                if (contact.first_name != contributor_first_name):
                    contact.first_name = contributor_first_name
                contributor_middle_name = transaction.get("contributor_middle_name")
                if (contact.middle_name != contributor_middle_name):
                    contact.middle_name = contributor_middle_name
                contributor_prefix = transaction.get("contributor_prefix")
                if (contact.prefix != contributor_prefix):
                    contact.prefix = contributor_prefix
                contributor_suffix = transaction.get("contributor_suffix")
                if (contact.suffix != contributor_suffix):
                    contact.suffix = contributor_suffix
                contributor_employer = transaction.get("contributor_employer")
                if (contact.employer != contributor_employer):
                    contact.employer = contributor_employer
                contributor_occupation = transaction.get("contributor_occupation")
                if (contact.occupation != contributor_occupation):
                    contact.occupation = contributor_occupation
            elif ((contact.type == Contact.ContactType.COMMITTEE)
                  and (transaction["entity_type"] == "COM")):
                donor_committee_fec_id = transaction.get("donor_committee_fec_id")
                if (contact.committee_id != donor_committee_fec_id):
                    contact.committee_id = donor_committee_fec_id
                contributor_organization_name = transaction.get(
                    "contributor_organization_name")
                if (contact.name != contributor_organization_name):
                    contact.name = contributor_organization_name
            elif ((contact.type == Contact.ContactType.ORGANIZATION)
                  and (transaction["entity_type"] == "ORG")):
                contributor_organization_name = transaction.get(
                    "contributor_organization_name")
                if (contact.name != contributor_organization_name):
                    contact.name = contributor_organization_name
            contributor_street_1 = transaction.get("contributor_street_1")
            if (contact.street_1 != contributor_street_1):
                contact.street_1 = contributor_street_1
            contributor_street_2 = transaction.get("contributor_street_2")
            if (contact.street_2 != contributor_street_2):
                contact.street_2 = contributor_street_2
            contributor_city = transaction.get("contributor_city")
            if (contact.city != contributor_city):
                contact.city = contributor_city
            contributor_zip = transaction.get("contributor_zip")
            if (contact.zip != contributor_zip):
                contact.zip = contributor_zip
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
