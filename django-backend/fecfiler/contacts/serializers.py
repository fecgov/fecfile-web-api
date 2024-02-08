import structlog

from django.db.models import Q
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.shared.utilities import get_model_data
from fecfiler.validation import serializers
from rest_framework.serializers import (
    IntegerField,
    UUIDField,
)
from rest_framework.exceptions import ValidationError

from .models import Contact

logger = structlog.get_logger(__name__)


def create_or_update_contact(validated_data: dict, contact_key, user_committee_id):

    if not user_committee_id:
        raise Exception('Tried to save contact without user_committee_id')

    contact_data = validated_data.pop(contact_key, None)
    contact_id = validated_data.get(contact_key + "_id", None)
    contact = None

    if contact_data:
        contact_data = get_model_data(contact_data, Contact)
        contact_data["committee_account_id"] = user_committee_id
        contact_data.pop("committee_account", None)

        if contact_id:
            Contact.objects.filter(id=contact_id).update(**contact_data)
            contact = Contact.objects.get(id=contact_id)
        else:
            contact = Contact.objects.create(**contact_data)
            validated_data[contact_key + "_id"] = contact.id

    return contact


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
                "contact_affiliated_transaction_set",
                "contact_candidate_I_transaction_set",
                "contact_candidate_II_transaction_set",
                "contact_candidate_III_transaction_set",
                "contact_candidate_IV_transaction_set",
                "contact_candidate_V_transaction_set",
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
