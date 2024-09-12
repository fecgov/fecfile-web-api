from datetime import datetime
from django.db import models
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.shared.utilities import generate_fec_uid
from fecfiler.transactions.managers import (
    TransactionManager,
    TransactionViewManager,
    Schedule,
)
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_e.models import ScheduleE

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

    can_delete = models.BooleanField(default=True)

    objects = TransactionManager()

    def get_schedule_name(self):
        for schedule_key in TABLE_TO_SCHEDULE:
            if getattr(self, schedule_key, None):
                return TABLE_TO_SCHEDULE[schedule_key]
        return None

    @property
    def children(self):
        return self.transaction_set.all()

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

    def save(self, *args, **kwargs):
        if self.memo_text:
            self.memo_text.transaction_uuid = self.id
            self.memo_text.save()

        super(Transaction, self).save(*args, **kwargs)

    def delete(self):
        if self.can_delete and not self.deleted:
            self.deleted = datetime.now()
            self.save()

            if not self.reatt_redes:
                # If deleted parent transaction to a reattribution/redesignation
                # delete the two child transactions
                reatt_redes_transactions = Transaction.objects.filter(reatt_redes=self)
                for child in reatt_redes_transactions:
                    if not child.deleted:
                        child.deleted = datetime.now()
                        child.save()

                # If earmark delete corresponding earmark
                if self.transaction_type_identifier == "EARMARK_RECEIPT":
                    earmark_memo = Transaction.objects.filter(
                        parent_transaction=self
                    ).first()
                    earmark_memo.deleted = datetime.now()
                    earmark_memo.save()
                elif self.transaction_type_identifier == "EARMARK_MEMO":
                    earmark_receipt = Transaction.objects.get(
                        id=self.parent_transaction.id
                    )
                    earmark_receipt.deleted = datetime.now()
                    earmark_receipt.save()
                    reatt_redes_transactions = Transaction.objects.filter(
                        reatt_redes=earmark_receipt
                    )
                    for child in reatt_redes_transactions:
                        if not child.deleted:
                            child.deleted = datetime.now()
                            child.save()

                # Handle debts
                debts = Transaction.objects.filter(debt=self)
                for debt in debts:
                    if not debt.deleted:
                        debt.deleted = datetime.now()
                        debt.save()

                # Handle Loans
                if (
                    "LOAN" in self.transaction_type_identifier
                    and "LOAN_REPAYMENT_MADE" != self.transaction_type_identifier
                ):
                    # If deleting the receipt, also delete the whole loan
                    if (
                        "LOAN_MADE" == self.transaction_type_identifier
                        or "RECEIPT" in self.transaction_type_identifier
                    ):
                        self.parent_transaction.deleted = datetime.now()
                        self.parent_transaction.save()
                        loan = self.parent_transaction
                    else:
                        loan = self
                    self.delete_loans(loan)

                child_transactions = Transaction.objects.filter(parent_transaction=self)
                for child in child_transactions:
                    if not child.deleted:
                        child.deleted = datetime.now()
                        child.save()
            # If deleting a reattribution/redesignation transaction,
            # delete the paired reattribution/redesignation but don't delete the parent
            else:
                reatt_redes_transactions = Transaction.objects.filter(
                    reatt_redes=self.reatt_redes
                )
                for child in reatt_redes_transactions:
                    if not child.deleted:
                        child.deleted = datetime.now()
                        child.save()

    def delete_loans(self, loan):
        loan_transactions = Transaction.objects.filter(loan_id=loan.id)
        for child in loan_transactions:
            if not child.deleted:
                child.deleted = datetime.now()
                child.save()
                self.delete_loans(child)
        loan_transactions = Transaction.objects.filter(parent_transaction_id=loan.id)
        for child in loan_transactions:
            if not child.deleted:
                child.deleted = datetime.now()
                child.save()
                self.delete_loans(child)
        if loan.loan:
            loan.loan.deleted = datetime.now()
            loan.loan.save()
            self.delete_loans(loan.loan)

    class Meta:
        indexes = [models.Index(fields=["_form_type"])]


def get_read_model(committee_uuid):

    committee_transaction_view = get_committee_view_name(committee_uuid)

    class T(Transaction):
        view_parent_transaction = models.ForeignKey(
            "self",
            db_column="parent_transaction_id",
            on_delete=models.CASCADE,
            null=True,
            blank=True,
        )
        schedule = models.TextField()
        _itemized = models.BooleanField()
        amount = models.DecimalField()
        date = models.DateField()
        form_type = models.TextField()
        effective_amount = models.DecimalField()
        back_reference_tran_id_number = models.TextField()
        loan_key = models.TextField()
        incurred_prior = models.DecimalField()
        payment_prior = models.DecimalField()
        payment_amount = models.DecimalField()
        name = models.TextField()

        objects = TransactionViewManager()

        class Meta:
            db_table = committee_transaction_view
            app_label = committee_transaction_view

    return T


def get_committee_view_name(committee_uuid):
    return f"transaction_view__{str(committee_uuid).replace('-','_')}"


TABLE_TO_SCHEDULE = {
    "schedule_a": Schedule.A,
    "schedule_b": Schedule.B,
    "schedule_c": Schedule.C,
    "schedule_c1": Schedule.C1,
    "schedule_c2": Schedule.C2,
    "schedule_d": Schedule.D,
    "schedule_e": Schedule.E,
}

SCHEDULE_TO_TABLE = {
    Schedule.A: "schedule_a",
    Schedule.B: "schedule_b",
    Schedule.C: "schedule_c",
    Schedule.C1: "schedule_c1",
    Schedule.C2: "schedule_c2",
    Schedule.D: "schedule_d",
    Schedule.E: "schedule_e",
}
