import logging

from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.contacts.serializers import LinkedContactSerializerMixin
from fecfiler.memo_text.serializers import LinkedMemoTextSerializerMixin
from fecfiler.f3x_summaries.serializers import F3XSummarySerializer
from fecfiler.validation import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import BooleanField, UUIDField, CharField, DateField
from fecfiler.transactions.models import Transaction

logger = logging.getLogger(__name__)
MISSING_TRANSACTION_TYPE_ERROR = ValidationError(
    {"transaction_type_identifier": ["No transaction_type_identifier provided"]}
)


class TransactionBaseSerializer(
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

    class Meta:
        abstract = True

        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]


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
    report = F3XSummarySerializer(read_only=True)
    itemized = BooleanField(read_only=True)
    action_date = DateField(read_only=True)

    def get_schema_name(self, data):
        transaction_type = data.get("transaction_type_identifier", None)
        if not transaction_type:
            raise MISSING_TRANSACTION_TYPE_ERROR
        return transaction_type

    class Meta:
        model = Transaction

        fields = [
            f.name
            for f in Transaction._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ] + [
            "report_id",
            "contact_id",
            "memo_text_id",
            "itemized",
            "fields_to_validate",
            "action_date",
        ]
