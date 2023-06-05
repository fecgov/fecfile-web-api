from django.db import models
from django.core.exceptions import ValidationError
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.f3x_summaries.models import ReportMixin
from fecfiler.shared.utilities import generate_fec_uid
from fecfiler.transactions.managers import TransactionManager, Schedule
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
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
    parent_transaction = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True
    )

    form_type = models.TextField(null=True, blank=True)
    transaction_id = models.TextField(
        null=False, blank=False, unique=True, default=generate_fec_uid,
    )
    entity_type = models.TextField(null=True, blank=True)
    memo_code = models.BooleanField(null=True, blank=True, default=False)
    force_itemized = models.BooleanField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    contact = models.ForeignKey("contacts.Contact", on_delete=models.CASCADE, null=True)
    memo_text = models.ForeignKey(
        "memo_text.MemoText", on_delete=models.CASCADE, null=True
    )

    schedule_a = models.ForeignKey(
        ScheduleA, on_delete=models.CASCADE, null=True, blank=True
    )
    schedule_b = models.ForeignKey(
        ScheduleB, on_delete=models.CASCADE, null=True, blank=True
    )
    schedule_c = models.ForeignKey(
        ScheduleC, on_delete=models.CASCADE, null=True, blank=True
    )
    schedule_c1 = models.ForeignKey(
        ScheduleC1, on_delete=models.CASCADE, null=True, blank=True
    )
    schedule_c2 = models.ForeignKey(
        ScheduleC2, on_delete=models.CASCADE, null=True, blank=True
    )

    objects = TransactionManager()

    @property
    def children(self):
        return self.transaction_set.all()

    def get_schedule_name(self):
        schedule_map = {
            "schedule_a": Schedule.A,
            "schedule_b": Schedule.B,
            "schedule_c": Schedule.C,
            "schedule_c1": Schedule.C1,
            "schedule_c2": Schedule.C2,
        }
        for schedule_key in schedule_map:
            if getattr(self, schedule_key, None):
                return schedule_map[schedule_key]
        return None

    def get_schedule(self):
        for schedule_key in [
            "schedule_a",
            "schedule_b",
            "schedule_c",
            "schedule_c1",
            "schedule_c2",
        ]:
            if getattr(self, schedule_key, None):
                return getattr(self, schedule_key)

    def get_date(self):
        return self.get_schedule().get_date()

    def save(self, *args, **kwargs):
        if self.memo_text:
            self.memo_text.transaction_uuid = self.id
            self.memo_text.save()
        try:
            super(Transaction, self).validate_unique()
        except ValidationError:  # try using a new fec id if collision
            self.transaction_id = generate_fec_uid()
        super(Transaction, self).save(*args, **kwargs)

    class Meta:
        indexes = [models.Index(fields=["form_type"])]
