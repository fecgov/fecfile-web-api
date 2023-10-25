from django.db import models
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.reports.models import ReportMixin
from fecfiler.shared.utilities import generate_fec_uid
from fecfiler.transactions.managers import TransactionManager, Schedule
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_e.models import ScheduleE
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
    debt = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="debt_associations",
    )
    loan = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="loan_associations",
    )

    # The _form_type value in the db may or may not be correct based on whether
    # the transaction is itemized or not. For some transactions, the form_type
    # value depends on its itemization status (e.g. SA11AI/SA11AII). The
    # db _form_type value for these transactions holds the "is itemized" line
    # number which is then dynamically updated to its true value in the manager
    # query in a Just-In-Time fashion.
    _form_type = models.TextField(null=True, blank=True)

    @property
    def form_type(self):
        return self._form_type

    @form_type.setter
    def form_type(self, value):
        self._form_type = value

    transaction_id = models.TextField(
        null=False, blank=False, unique=False, default=generate_fec_uid
    )
    entity_type = models.TextField(null=True, blank=True)
    memo_code = models.BooleanField(null=True, blank=True, default=False)
    force_itemized = models.BooleanField(null=True, blank=True)
    force_unaggregated = models.BooleanField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    contact_1 = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_1_transaction_set",
        null=True,
    )
    contact_2 = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_2_transaction_set",
        null=True,
    )
    contact_3 = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_3_transaction_set",
        null=True,
    )
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
    schedule_d = models.ForeignKey(
        ScheduleD, on_delete=models.CASCADE, null=True, blank=True
    )
    schedule_e = models.ForeignKey(
        ScheduleE, on_delete=models.CASCADE, null=True, blank=True
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
            "schedule_d": Schedule.D,
            "schedule_e": Schedule.E,
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
            "schedule_d",
            "schedule_e",
        ]:
            if getattr(self, schedule_key, None):
                return getattr(self, schedule_key)

    def get_date(self):
        return self.get_schedule().get_date()

    def save(self, *args, **kwargs):
        if self.memo_text:
            self.memo_text.transaction_uuid = self.id
            self.memo_text.save()
        super(Transaction, self).save(*args, **kwargs)

    class Meta:
        indexes = [models.Index(fields=["_form_type"])]
