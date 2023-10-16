from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.reports.models import ReportMixin
from fecfiler.shared.utilities import generate_fec_uid
from django.db import models
import uuid
import logging


logger = logging.getLogger(__name__)


class MemoText(SoftDeleteModel, CommitteeOwnedModel, ReportMixin):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    rec_type = models.TextField(null=True, blank=True)
    is_report_level_memo = models.BooleanField(null=False, blank=False, default=True)
    transaction_id_number = models.TextField(null=True, blank=True)
    transaction_uuid = models.TextField(null=True, blank=True)
    text4000 = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "memo_text"

    # This is intended to be useable without instantiating a transaction object
    @staticmethod
    def check_for_uid_conflicts(uid, report_id):  # noqa
        return (
            len(MemoText.objects.filter(transaction_id_number=uid, report_id=report_id))
            > 0
        )

    def generate_report_id(self):
        report_memos = MemoText.objects.filter(
            report_id=self.report_id, transaction_uuid=None
        )
        return "REPORT_MEMO_TEXT" + str(len(report_memos) + 1)

    def generate_unique_transaction_id(self):
        id_generator = generate_fec_uid
        if self.is_report_level_memo:
            id_generator = self.generate_report_id
        unique_id = id_generator()

        attempts = 0
        while MemoText.check_for_uid_conflicts(unique_id, self.report_id):
            unique_id = id_generator()
            attempts += 1
            logger.info("Transaction unique ID generation: collision detected")
            if attempts > 5:
                logger.info("Unique ID generation failed: Over 5 conflicts in a row")
                return ""
        return unique_id

    def save(self, *args, **kwargs):
        if not self.transaction_id_number:
            self.transaction_id_number = self.generate_unique_transaction_id()

        super(MemoText, self).save(*args, **kwargs)
