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
MISSING_TRANSACTION_TYPE_ERROR = ValidationError(
    {"transaction_type_identifier": ["No transaction_type_identifier provided"]}
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
        transaction_type = data.get("transaction_type_identifier", None)
        if not transaction_type:
            raise MISSING_TRANSACTION_TYPE_ERROR
        return transaction_type

    def to_internal_value(self, data):
        # We are not saving report or parent_transaction objects so
        # we need to ensure their object properties are UUIDs and not objects
        def insert_foreign_keys(transaction):
            transaction["report"] = transaction["report_id"]
            if "parent_transaction_object_id" in transaction:
                transaction["parent_transaction"] = transaction[
                    "parent_transaction_object_id"
                ]
            return transaction

        if "children" in data:
            data["children"] = list(map(insert_foreign_keys, data["children"]))
        return super().to_internal_value(data)

    class Meta:
        abstract = True

        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
