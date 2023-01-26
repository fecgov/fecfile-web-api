import logging

from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.contacts.serializers import LinkedContactSerializerMixin
from fecfiler.memo_text.serializers import LinkedMemoTextSerializerMixin
from fecfiler.validation import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    BooleanField,
    UUIDField,
    CharField,
)

logger = logging.getLogger(__name__)
MISSING_SCHEMA_NAME_ERROR = ValidationError(
    {"schema_name": ["No schema_name provided"]}
)


class TransactionSerializerBase(
    LinkedContactSerializerMixin,
    LinkedMemoTextSerializerMixin,
    serializers.FecSchemaValidatorSerializerMixin,
    CommitteeOwnedSerializer,
):
    """id must be explicitly configured in order to have it in validated_data
    https://github.com/encode/django-rest-framework/issues/2320#issuecomment-67502474"""

    id = UUIDField(required=False)
    transaction_id = CharField(required=False, allow_null=True)
    report_id = UUIDField(required=True, allow_null=False)

    itemized = BooleanField(read_only=True)

    def get_schema_name(self, data):
        schema_name = data.get("schema_name", None)
        if not schema_name:
            raise MISSING_SCHEMA_NAME_ERROR
        return schema_name

    class Meta:
        abstract = True

        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
