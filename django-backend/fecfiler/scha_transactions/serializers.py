import logging

from django.db import transaction
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.contacts.models import Contact
from fecfiler.contacts.serializers import ContactSerializer
from fecfiler.validation import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    BooleanField,
    DecimalField,
    ListSerializer,
    UUIDField,
)

from .models import SchATransaction

logger = logging.getLogger(__name__)


class SchATransactionSerializer(
    CommitteeOwnedSerializer, serializers.FecSchemaValidatorSerializerMixin
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
            contact = Contact.objects.get(id=tran_contact_id)
        changes = self.update_contact_for_transaction(contact, validated_data)
        if changes:
            contact.save()

    def update_contact_for_transaction(self, contact: Contact, transaction: dict):
        changes = False
        if contact and transaction:
            if (contact.type == Contact.ContactType.INDIVIDUAL) and (
                transaction["entity_type"] == "IND"
            ):
                if self.update_ind_contact_for_transaction(contact, transaction):
                    changes = True
            elif (contact.type == Contact.ContactType.COMMITTEE) and (
                transaction["entity_type"] == "COM"
            ):
                if self.update_com_contact_for_transaction(contact, transaction):
                    changes = True
            elif (contact.type == Contact.ContactType.ORGANIZATION) and (
                transaction["entity_type"] == "ORG"
            ):
                if self.update_org_contact_for_transaction(contact, transaction):
                    changes = True
            if self.update_contact_for_transaction_shared_fields(contact, transaction):
                changes = True
        return changes

    def update_ind_contact_for_transaction(self, contact: Contact, transaction: dict):
        changes = False
        contributor_last_name = transaction.get("contributor_last_name")
        if contact.last_name != contributor_last_name:
            contact.last_name = contributor_last_name
            changes = True
        contributor_first_name = transaction.get("contributor_first_name")
        if contact.first_name != contributor_first_name:
            contact.first_name = contributor_first_name
            changes = True
        contributor_middle_name = transaction.get("contributor_middle_name")
        if contact.middle_name != contributor_middle_name:
            contact.middle_name = contributor_middle_name
            changes = True
        contributor_prefix = transaction.get("contributor_prefix")
        if contact.prefix != contributor_prefix:
            contact.prefix = contributor_prefix
            changes = True
        contributor_suffix = transaction.get("contributor_suffix")
        if contact.suffix != contributor_suffix:
            contact.suffix = contributor_suffix
            changes = True
        contributor_employer = transaction.get("contributor_employer")
        if contact.employer != contributor_employer:
            contact.employer = contributor_employer
            changes = True
        contributor_occupation = transaction.get("contributor_occupation")
        if contact.occupation != contributor_occupation:
            contact.occupation = contributor_occupation
            changes = True
        return changes

    def update_com_contact_for_transaction(self, contact: Contact, transaction: dict):
        changes = False
        donor_committee_fec_id = transaction.get("donor_committee_fec_id")
        if contact.committee_id != donor_committee_fec_id:
            contact.committee_id = donor_committee_fec_id
            changes = True
        contributor_organization_name = transaction.get("contributor_organization_name")
        if contact.name != contributor_organization_name:
            contact.name = contributor_organization_name
            changes = True
        return changes

    def update_org_contact_for_transaction(self, contact: Contact, transaction: dict):
        changes = False
        contributor_organization_name = transaction.get("contributor_organization_name")
        if contact.name != contributor_organization_name:
            contact.name = contributor_organization_name
            changes = True
        return changes

    def update_contact_for_transaction_shared_fields(
        self, contact: Contact, transaction: dict
    ):
        changes = False
        contributor_street_1 = transaction.get("contributor_street_1")
        if contact.street_1 != contributor_street_1:
            contact.street_1 = contributor_street_1
            changes = True
        contributor_street_2 = transaction.get("contributor_street_2")
        if contact.street_2 != contributor_street_2:
            contact.street_2 = contributor_street_2
            changes = True
        contributor_city = transaction.get("contributor_city")
        if contact.city != contributor_city:
            contact.city = contributor_city
            changes = True
        contributor_state = transaction.get("contributor_state")
        if contact.state != contributor_state:
            contact.state = contributor_state
            changes = True
        contributor_zip = transaction.get("contributor_zip")
        if contact.zip != contributor_zip:
            contact.zip = contributor_zip
            changes = True
        return changes

    class Meta(SchATransactionSerializer.Meta):
        fields = [
            f.name
            for f in SchATransaction._meta.get_fields()
            if f.name not in ["deleted", "schatransaction"]
        ] + ["parent_transaction_id", "report_id", "contact_id", "children"]
