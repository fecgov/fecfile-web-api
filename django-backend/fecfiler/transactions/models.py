from django.db import models
from django.core.exceptions import ValidationError
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.f3x_summaries.models import ReportMixin
from fecfiler.shared.utilities import generate_fec_uid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid
import logging


logger = logging.getLogger(__name__)


class Transaction(SoftDeleteModel, CommitteeOwnedModel, ReportMixin):

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    transaction_type_identifier = models.TextField(null=True, blank=True)
    aggregation_group = models.TextField(null=True, blank=True)

    parent_transaction_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    parent_transaction_object_id = models.UUIDField(null=True, blank=True)
    parent_transaction = GenericForeignKey(
        "parent_transaction_content_type", "parent_transaction_object_id"
    )

    form_type = models.TextField(null=True, blank=True)
    # TODO remove from model after refactoring .fec services
    filer_committee_id_number = models.TextField(null=True, blank=True)
    transaction_id = models.TextField(
        null=False,
        blank=False,
        unique=True,
        default=generate_fec_uid,
    )
    # TODO remove from model after refactoring .fec services
    back_reference_tran_id_number = models.TextField(null=True, blank=True)
    # TODO remove from model after refactoring .fec services
    back_reference_sched_name = models.TextField(null=True, blank=True)
    entity_type = models.TextField(null=True, blank=True)
    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    conduit_name = models.TextField(null=True, blank=True)
    conduit_street_1 = models.TextField(null=True, blank=True)
    conduit_street_2 = models.TextField(null=True, blank=True)
    conduit_city = models.TextField(null=True, blank=True)
    conduit_state = models.TextField(null=True, blank=True)
    conduit_zip = models.TextField(null=True, blank=True)
    memo_code = models.BooleanField(null=True, blank=True, default=False)
    memo_text_description = models.TextField(null=True, blank=True)
    reference_to_si_or_sl_system_code_that_identifies_the_account = models.TextField(
        null=True, blank=True
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    contact = models.ForeignKey("contacts.Contact", on_delete=models.CASCADE, null=True)
    memo_text = models.ForeignKey(
        "memo_text.MemoText", on_delete=models.CASCADE, null=True
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.memo_text:
            self.memo_text.transaction_uuid = self.id
            self.memo_text.save()
        try:
            super(Transaction, self).validate_unique()
        except ValidationError:  # try using a new fec id if collision
            self.transaction_id = generate_fec_uid()
        super(Transaction, self).save(*args, **kwargs)
