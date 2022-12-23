import logging

from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.contacts.serializers import (
    ContactSerializer,
    LinkedContactSerializerMixin,
)
from fecfiler.memo_text.serializers import MemoTextSerializer
from fecfiler.validation import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    BooleanField,
    UUIDField,
    CharField,
)

logger = logging.getLogger(__name__)
MISSING_TRANSACTION_TYPE_ERROR = ValidationError(
    {"transaction_type_identifier": ["No transaction_type_identifier provided"]}
)


class TransactionSerializerBase(
    LinkedContactSerializerMixin,
    serializers.FecSchemaValidatorSerializerMixin,
    CommitteeOwnedSerializer,
):
    """id must be explicitly configured in order to have it in validated_data
    https://github.com/encode/django-rest-framework/issues/2320#issuecomment-67502474"""

    id = UUIDField(required=False)
    transaction_id = CharField(required=False, allow_null=True)
    report_id = UUIDField(required=True, allow_null=False)
    # maybe we can factor these out on the front end since we send the whole contact/memo_text object
    contact_id = UUIDField(required=False, allow_null=False)
    memo_text_id = UUIDField(required=False, allow_null=True)

    contact = ContactSerializer(allow_null=True, required=False)
    memo_text = MemoTextSerializer(allow_null=True, required=False)

    itemized = BooleanField(read_only=True)

    def get_schema_name(self, data):
        transaction_type = data.get("transaction_type_identifier", None)
        if not transaction_type:
            raise MISSING_TRANSACTION_TYPE_ERROR
        return transaction_type

    class Meta:
        abstract = True

        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
