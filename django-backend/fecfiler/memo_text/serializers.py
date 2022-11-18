from .models import MemoText
from fecfiler.validation import serializers
from rest_framework.serializers import UUIDField, SerializerMethodField
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
            if f.name not in ["report", "deleted", "schatransaction"]
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
        if (transaction):
            return transaction.transaction_id
