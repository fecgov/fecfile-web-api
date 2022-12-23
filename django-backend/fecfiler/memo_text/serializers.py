from .models import MemoText
from django.db import transaction
from fecfiler.validation import serializers
from rest_framework.serializers import UUIDField, SerializerMethodField, Serializer
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.shared.transactions import get_from_sched_tables_by_uuid
import logging

logger = logging.getLogger(__name__)


class MemoTextSerializer(
    serializers.FecSchemaValidatorSerializerMixin, CommitteeOwnedSerializer
):
    schema_name = "Text"
    report_id = UUIDField(required=True, allow_null=False)

    back_reference_tran_id_number = SerializerMethodField()

    class Meta:
        model = MemoText
        fields = [
            f.name
            for f in MemoText._meta.get_fields()
            if f.name
            not in [
                "report",
                "deleted",
                "schatransaction",
                "scheduleatransaction",
                "schedulebtransaction",
            ]
        ] + ["report_id"]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
            "back_reference_tran_id_number",
        ]

    def get_back_reference_tran_id_number(self, memo_text_obj):
        transaction = get_from_sched_tables_by_uuid(memo_text_obj.transaction_uuid)
        if transaction:
            return transaction.transaction_id


class LinkedMemoTextSerializerMixin(Serializer):
    def create(self, validated_data: dict):
        with transaction.atomic():
            self.create_or_update(validated_data)
            return super().create(validated_data)

    def update(self, validated_data: dict):
        with transaction.atomic():
            self.create_or_update(validated_data)
            return super().update(validated_data)

    def create_or_update(self, validated_data: dict):
        memo_data = validated_data.pop("memo_text", None)
        memo_text_id = validated_data.get("memo_text_id", None)
        if memo_data:
            memo_text, _ = MemoText.objects.update_or_create(
                id=memo_text_id,
                defaults={
                    "is_report_level_memo": False,
                    "report_id": validated_data.get("report_id", None),
                    **memo_data,
                },
            )
            validated_data["memo_text_id"] = memo_text.id
        elif memo_text_id:
            memo_object = MemoText.objects.get(id=memo_text_id)
            memo_object.delete()
            validated_data["memo_text_id"] = None
