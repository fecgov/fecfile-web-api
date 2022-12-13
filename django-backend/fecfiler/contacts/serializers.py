import logging

from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation import serializers

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
            ]
        ]
        read_only_fields = [
            "uuid",
            "deleted",
            "created",
            "updated",
        ]
