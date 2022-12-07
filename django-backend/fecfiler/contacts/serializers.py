import logging

from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation import serializers
from rest_framework.serializers import IntegerField

from .models import Contact

logger = logging.getLogger(__name__)


class ContactSerializer(
    serializers.FecSchemaValidatorSerializerMixin, CommitteeOwnedSerializer
):
    contact_value = dict(
        COM="Committee", IND="Individual", ORG="Organization", CAN="Candidate",
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
            if f.name not in ["deleted", "schatransaction"]
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
        # delivered to the front end.
        if "transaction_count" in data:
            del data["transaction_count"]
        return super().to_internal_value(data)
