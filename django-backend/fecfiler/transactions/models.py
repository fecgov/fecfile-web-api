from django.db import models
from django.contrib.postgres.fields import ArrayField
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.shared.utilities import generate_fec_uid
from fecfiler.transactions.managers import (
    TransactionManager,
    Schedule,
)
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_e.models import ScheduleE
from fecfiler.transactions.schedule_f.models import ScheduleF
from fecfiler.contacts.models import Contact

import uuid
import structlog

logger = structlog.get_logger(__name__)


class Transaction(SoftDeleteModel, CommitteeOwnedModel):
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
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
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
    reatt_redes = models.ForeignKey(  # reattribution/redesignation
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reatt_redes_associations",
    )
    reports = models.ManyToManyField(
        "reports.Report",
        through="reports.ReportTransaction",
        through_fields=["transaction", "report"],
        related_name="transactions",
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

    itemized = models.BooleanField(db_default=True)

    force_itemized = models.BooleanField(null=True, blank=True)
    force_unaggregated = models.BooleanField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    contact_1: Contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_1_transaction_set",
        null=True,
    )
    contact_2: Contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_2_transaction_set",
        null=True,
    )
    contact_3: Contact = models.ForeignKey(
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
    schedule_f = models.ForeignKey(
        ScheduleF, on_delete=models.CASCADE, null=True, blank=True
    )

    # Calculated fields
    aggregate = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    _calendar_ytd_per_election_office = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    loan_payment_to_date = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    # report ids of reports that have been submitted
    # and in doing so have blocked this transaction from being deleted
    blocking_reports = ArrayField(models.UUIDField(), blank=False, default=list)

    objects = TransactionManager()

    def get_schedule_name(self):
        for schedule_key in TABLE_TO_SCHEDULE:
            if getattr(self, schedule_key, None):
                return TABLE_TO_SCHEDULE[schedule_key]
        return None

    def get_transaction_family(self):
        return [
            self,
            *self.get_ancestor_transactions(),
            *self.get_descendant_transactions(),
        ]

    def get_ancestor_transactions(self):
        if self.parent_transaction is None:
            return []
        else:
            return [
                self.parent_transaction,
                *self.parent_transaction.get_ancestor_transactions(),
            ]

    def get_descendant_transactions(self):
        if len(self.children) == 0:
            return []
        else:
            grandchildren = []
            for child in self.children:
                grandchildren += child.get_descendant_transactions()
            return [*self.children, *grandchildren]

    @property
    def children(self):
        return self.transaction_set.all()

    @property
    def can_delete(self):
        return len(self.blocking_reports) == 0

    @property
    def filer_committee_id_number(self):
        if not self.committee_account:
            return None

        return self.committee_account.committee_id

    def get_schedule(self):
        for schedule_key in TABLE_TO_SCHEDULE.keys():
            if getattr(self, schedule_key, None):
                return getattr(self, schedule_key)

    def is_loan_repayment(self):
        return self.loan is not None and self.schedule_c is None

    def is_debt_repayment(self):
        return self.debt is not None and self.schedule_d is None

    def save(self, *args, **kwargs):
        if self.memo_text:
            self.memo_text.transaction_uuid = self.id
            self.memo_text.save()
        super(Transaction, self).save(*args, **kwargs)

    def delete(self):
        if not self.can_delete:
            raise Exception("Transaction cannot be deleted")
        if not self.deleted:
            super(Transaction, self).delete()

            # child transactions
            child_transactions = Transaction.objects.filter(parent_transaction=self)
            for child in child_transactions:
                child.delete()

            # transactions related to this debt
            # delete any carry forwards or repayments related to this debt
            debt_carry_forwards_and_repayments = Transaction.objects.filter(debt=self)
            for carry_forward_or_repayment in debt_carry_forwards_and_repayments:
                carry_forward_or_repayment.delete()

            # transactions related to a loan
            # delete any carry forwards or repayments related to this loan
            loan_carry_forwards_and_repayments = Transaction.objects.filter(loan=self)
            for carry_forward_or_repayment in loan_carry_forwards_and_repayments:
                carry_forward_or_repayment.delete()

            """
            REATTRIBUTION/REDESIGNATION
            """
            # If this is a reattribution/redesignation 'from' transaction,
            # delete the 'to' transaction
            if (
                self.schedule_a
                and self.schedule_a.reattribution_redesignation_tag == "REATTRIBUTED_FROM"
            ) or (
                self.schedule_b
                and self.schedule_b.reattribution_redesignation_tag == "REDESIGNATED_FROM"
            ):
                self.parent_transaction.delete()

            # If this reattribution/redesignation is tied to a copy of
            # the original transaction, delete the copy
            if self.reatt_redes and (
                (
                    self.reatt_redes.schedule_a
                    and self.reatt_redes.schedule_a.reattribution_redesignation_tag
                    == "REATTRIBUTED"
                )
                or (
                    self.reatt_redes.schedule_b
                    and self.reatt_redes.schedule_b.reattribution_redesignation_tag
                    == "REDESIGNATED"
                )
            ):
                self.reatt_redes.delete()

            # Delete any reattribution/redesignation transactions
            # related to this transaction (copy/from/to)"
            reatributions_and_redesignations = Transaction.objects.filter(
                reatt_redes=self
            )
            for reatribuiton_or_redesignation in reatributions_and_redesignations:
                reatribuiton_or_redesignation.delete()

            # coupled transactions
            if (
                self.parent_transaction
                and self.transaction_type_identifier in COUPLED_TRANSACTION_TYPES
            ):
                self.parent_transaction.delete()

    class Meta:
        indexes = [models.Index(fields=["_form_type"])]


TABLE_TO_SCHEDULE = {
    "schedule_a": Schedule.A,
    "schedule_b": Schedule.B,
    "schedule_c": Schedule.C,
    "schedule_c1": Schedule.C1,
    "schedule_c2": Schedule.C2,
    "schedule_d": Schedule.D,
    "schedule_e": Schedule.E,
    "schedule_f": Schedule.F,
}

SCHEDULE_TO_TABLE = {
    Schedule.A: "schedule_a",
    Schedule.B: "schedule_b",
    Schedule.C: "schedule_c",
    Schedule.C1: "schedule_c1",
    Schedule.C2: "schedule_c2",
    Schedule.D: "schedule_d",
    Schedule.E: "schedule_e",
    Schedule.F: "schedule_f",
}

COUPLED_TRANSACTION_TYPES = [
    # EARMARK MEMOS
    "EARMARK_MEMO",
    "EARMARK_MEMO_CONVENTION_ACCOUNT",
    "EARMARK_MEMO_HEADQUARTERS_ACCOUNT",
    "EARMARK_MEMO_RECOUNT_ACCOUNT",
    "PAC_EARMARK_MEMO",
    # CONDUIT EARMARK OUTS
    "CONDUIT_EARMARK_OUT_DEPOSITED",
    "CONDUIT_EARMARK_OUT_UNDEPOSITED",
    "PAC_CONDUIT_EARMARK_OUT_DEPOSITED",
    "PAC_CONDUIT_EARMARK_OUT_UNDEPOSITED",
    # IN KIND OUTS
    "IN_KIND_OUT",
    "PAC_IN_KIND_OUT",
    "PARTY_IN_KIND_OUT",
    # LOAN
    "LOAN_MADE",
    "LOAN_RECEIVED_FROM_BANK_RECEIPT",
    "LOAN_RECEIVED_FROM_INDIVIDUAL_RECEIPT",
    "C1_LOAN_AGREEMENT",
]


class OverTwoHundredTypesScheduleA(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    type = models.TextField()

    class Meta:
        db_table = "over_two_hundred_types_schedulea"
        indexes = [models.Index(fields=["type"])]


class OverTwoHundredTypesScheduleB(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    type = models.TextField()

    class Meta:
        db_table = "over_two_hundred_types_scheduleb"
        indexes = [models.Index(fields=["type"])]
