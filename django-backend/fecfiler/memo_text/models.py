from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.f3x_summaries.models import ReportMixin
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
    filer_committee_id_number = models.TextField(null=True, blank=True)
    transaction_id_number = models.TextField(null=True, blank=True)
    transaction_uuid = models.TextField(null=True, blank=True)
    back_reference_tran_id_number = models.TextField(null=True, blank=True)
    back_reference_sched_form_name = models.TextField(null=True, blank=True)
    text4000 = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "memo_text"

    # This is intended to be useable without instantiating a transaction object
    @staticmethod
    def check_for_uid_conflicts(uid):  # noqa
        return len(MemoText.objects.filter(transaction_id_number=uid)) > 0

    def generate_uid(self):
        unique_id = uuid.uuid4()
        hex_id = unique_id.hex.upper()
        # Take 20 characters from the end, skipping over the 20th char from the right,
        # which is the version number (uuid4 -> "4")
        return hex_id[-21] + hex_id[-19:]

    def generate_unique_transaction_id(self):
        unique_id = self.generate_uid()

        attempts = 0
        while MemoText.check_for_uid_conflicts(unique_id):
            unique_id = self.generate_uid()
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
