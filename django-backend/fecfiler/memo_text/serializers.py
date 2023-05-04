from .models import MemoText
from django.db import transaction
from fecfiler.validation import serializers
from rest_framework.serializers import UUIDField, ModelSerializer
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
import logging

logger = logging.getLogger(__name__)


class MemoTextSerializer(
    serializers.FecSchemaValidatorSerializerMixin, CommitteeOwnedSerializer
):
    schema_name = "Text"
    report_id = UUIDField(required=True, allow_null=False)

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
                "transaction",
            ]
        ] + [
            "report_id",
            "fields_to_validate",
        ]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]

    def validate(self, data):
        self.context["fields_to_ignore"] = self.context.get(
            "fields_to_ignore",
            [
                "filer_committee_id_number",
                "back_reference_sched_form_name",
                "back_reference_tran_id_number",
            ],
        )
        return super().validate(data)


class LinkedMemoTextSerializerMixin(ModelSerializer):
    memo_text = MemoTextSerializer(allow_null=True, required=False)
    memo_text_id = UUIDField(required=False, allow_null=True)

    def create(self, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_memo(validated_data)
            return super().create(validated_data)

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_memo(validated_data)
            return super().update(instance, validated_data)

    def create_or_update_memo(self, validated_data: dict):
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
