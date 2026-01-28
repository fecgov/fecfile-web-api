from django.db import models
from django.db.models import Q
from django.contrib.postgres.fields import ArrayField
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.shared.utilities import generate_fec_uid
from fecfiler.transactions.managers import (
    TransactionManager,
    Schedule,
    AGGREGATE_SCHEDULES,
)
from fecfiler.transactions.utils_aggregation_prep import (
    create_old_snapshot,
    calculate_effective_amount,
)
from fecfiler.transactions.utils_aggregation_service import (
    update_aggregates_for_affected_transactions,
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
CONTACT = "contacts.Contact"


class Transaction(SoftDeleteModel, CommitteeOwnedModel):

    def __str__(self):
        return f"Transaction {self.id} - agg {self.aggregate}"

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

    itemized = models.BooleanField(db_default=False)

    force_itemized = models.BooleanField(null=True, blank=True)
    force_unaggregated = models.BooleanField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    contact_1: Contact = models.ForeignKey(
        CONTACT,
        on_delete=models.CASCADE,
        related_name="contact_1_transaction_set",
        null=True,
    )
    contact_2: Contact = models.ForeignKey(
        CONTACT,
        on_delete=models.CASCADE,
        related_name="contact_2_transaction_set",
        null=True,
    )
    contact_3: Contact = models.ForeignKey(
        CONTACT,
        on_delete=models.CASCADE,
        related_name="contact_3_transaction_set",
        null=True,
    )
    contact_4: Contact = models.ForeignKey(
        CONTACT,
        on_delete=models.CASCADE,
        related_name="contact_4_transaction_set",
        null=True,
    )
    contact_5: Contact = models.ForeignKey(
        CONTACT,
        on_delete=models.CASCADE,
        related_name="contact_5_transaction_set",
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

    def get_date(self):
        schedule = self.get_schedule()
        if schedule is not None:
            return schedule.get_date()

    def is_loan_repayment(self):
        return self.loan is not None and self.schedule_c is None

    def is_debt_repayment(self):
        return self.debt is not None and self.schedule_d is None

    def _get_snapshot_related_fields(self, schedule):
        related_map = {
            Schedule.A: ["schedule_a"],
            "A": ["schedule_a"],
            Schedule.B: ["schedule_b"],
            "B": ["schedule_b"],
            Schedule.E: ["schedule_e", "contact_2"],
            "E": ["schedule_e", "contact_2"],
            Schedule.F: ["schedule_f", "contact_2"],
            "F": ["schedule_f", "contact_2"],
        }
        return related_map.get(schedule, [])

    def _get_old_snapshot(self, schedule, is_internal_update, passed_old_snapshot):
        # Use passed_old_snapshot if available, otherwise query DB
        if passed_old_snapshot is not None:
            return passed_old_snapshot

        if (
            schedule not in AGGREGATE_SCHEDULES
            and schedule not in ["A", "B", "E"]
            and schedule not in [Schedule.F, "F"]
        ):
            return None

        if is_internal_update or self.pk is None:
            return None

        try:
            related_fields = self._get_snapshot_related_fields(schedule)
            queryset = Transaction.objects
            if related_fields:
                queryset = queryset.select_related(*related_fields)
            old = queryset.get(pk=self.pk)
        except Transaction.DoesNotExist:
            return None

        eff = calculate_effective_amount(old)
        return create_old_snapshot(old, eff)

    def _handle_service_aggregation(self, schedule, is_create, old_snapshot):
        # Only schedules A, B, and E participate in aggregates.
        if schedule in AGGREGATE_SCHEDULES or schedule in ["A", "B", "E"]:
            action = "create" if is_create else "update"
            update_aggregates_for_affected_transactions(
                Transaction, self, action, old_snapshot
            )

    def _handle_schedule_f_aggregation(self, schedule, old_snapshot):
        if schedule not in [Schedule.F, "F"]:
            return

        from fecfiler.transactions.aggregation import (
            process_aggregation_by_payee_candidate,
        )

        # Handle broken chain: if election_year changed, recalculate old chain
        if old_snapshot and old_snapshot.get("election_year"):
            old_election_year = old_snapshot.get("election_year")
            current_election_year = (
                self.schedule_f.general_election_year
                if self.schedule_f else None
            )

            if old_election_year != current_election_year:
                # Find first transaction in old election year chain to
                # recalculate
                old_chain_first = Transaction.objects.filter(
                    ~Q(id=self.id),
                    contact_2_id=old_snapshot.get("contact_2_id"),
                    schedule_f__isnull=False,
                    schedule_f__general_election_year=old_election_year,
                ).order_by("date", "created").first()

                if old_chain_first:
                    process_aggregation_by_payee_candidate(
                        old_chain_first, None
                    )

        # Always recalculate current transaction's chain
        # Note: This handles date leapfrogging by recalculating
        # all transactions with date >= this transaction's date
        process_aggregation_by_payee_candidate(self, old_snapshot)

    def _handle_entity_aggregation(self, schedule, old_snapshot):
        if schedule not in [Schedule.A, Schedule.B, "A", "B"] or not old_snapshot:
            return

        from fecfiler.transactions.aggregation import (
            process_aggregation_for_entity_contact,
        )

        old_contact_id = old_snapshot.get("contact_1_id")
        old_date = old_snapshot.get("date")
        old_group = old_snapshot.get("aggregation_group")
        new_date = self.get_date()

        if (
            old_contact_id == self.contact_1_id
            and old_date == new_date
            and old_group == self.aggregation_group
        ):
            return

        # Determine if we need to recalculate old chain (contact changed)
        if old_contact_id and old_contact_id != self.contact_1_id:
            process_aggregation_for_entity_contact(
                self.committee_account_id,
                self.aggregation_group,
                old_contact_id,
                old_date if old_date else self.get_date(),
            )

        # Calculate earliest date for current chain
        if old_date:
            earliest_date = min(self.get_date(), old_date)
        else:
            earliest_date = self.get_date()

        # Recalculate current contact's chain
        process_aggregation_for_entity_contact(
            self.committee_account_id,
            self.aggregation_group,
            self.contact_1_id,
            earliest_date,
        )

    def _handle_debt_aggregation(self):
        if self.is_debt_repayment() or self.schedule_d is not None:
            from fecfiler.transactions.aggregation import (
                process_aggregation_for_debts,
            )

            process_aggregation_for_debts(self)

    def save(self, *args, **kwargs):
        # Check if old_snapshot was passed from view (for Schedule A, B, F)
        # This is needed because schedule is saved before transaction,
        # so DB already has new values
        passed_old_snapshot = getattr(self, '_passed_old_snapshot', None)

        # Avoid recursion when service adjusts fields via save(update_fields=...)
        update_fields = kwargs.get("update_fields")
        is_internal_update = update_fields is not None

        # Capture old snapshot for updates IMMEDIATELY, before any other modifications
        # Use passed_old_snapshot if available (for Schedule F), otherwise query DB
        schedule = self.get_schedule_name()
        is_create = self.pk is None
        old_snapshot = self._get_old_snapshot(
            schedule, is_internal_update, passed_old_snapshot
        )

        # Handle memo_text after snapshot is captured
        if self.memo_text:
            if self.memo_text.text4000 is None or self.memo_text.text4000 == "":
                self.memo_text.hard_delete()
                self.memo_text = None
            else:
                self.memo_text.transaction_uuid = self.id
                self.memo_text.save()

        super(Transaction, self).save(*args, **kwargs)

        # Invoke service after save for create/update
        if not is_internal_update:
            try:
                self._handle_service_aggregation(
                    schedule, is_create, old_snapshot
                )
            except Exception as e:
                # Do not raise to avoid breaking save on service failure; log instead
                logger.error(
                    "Failed to update aggregates via service on save",
                    transaction_id=self.id,
                    error=str(e),
                    exc_info=True,
                )

            # Handle Schedule F (payee-candidate) aggregation
            try:
                self._handle_schedule_f_aggregation(schedule, old_snapshot)
            except Exception as e:
                logger.error(
                    "Failed to process Schedule F aggregation on save",
                    transaction_id=self.id,
                    error=str(e),
                    exc_info=True,
                )

            # Handle entity aggregation for schedules with contact_1 changes
            # This covers edge cases like date changes and contact changes
            try:
                self._handle_entity_aggregation(schedule, old_snapshot)
            except Exception as e:
                logger.error(
                    "Failed to process entity aggregation on save",
                    transaction_id=self.id,
                    error=str(e),
                    exc_info=True,
                )

            # Handle debt aggregation for Schedule D and debt repayments
            try:
                self._handle_debt_aggregation()
            except Exception as e:
                logger.error(
                    "Failed to process debt aggregation on save",
                    transaction_id=self.id,
                    error=str(e),
                    exc_info=True,
                )

    def delete(self):
        if not self.can_delete:
            raise AttributeError("Transaction cannot be deleted")
        if not self.deleted:
            # Mark as deleted first so aggregation queries can filter it out
            super(Transaction, self).delete()

            try:
                # Only schedules A, B, and E participate in aggregates
                schedule = self.get_schedule_name()
                if schedule in AGGREGATE_SCHEDULES:
                    # Capture snapshot and apply delete delta after marking deleted
                    eff = calculate_effective_amount(self)
                    old_snapshot = create_old_snapshot(self, eff)
                    update_aggregates_for_affected_transactions(
                        Transaction, self, "delete", old_snapshot
                    )
            except Exception:
                logger.error(
                    "Failed to update aggregates via service on delete",
                    transaction_id=self.id,
                )

            # Handle debt aggregation after marking deleted
            try:
                if self.is_debt_repayment():
                    from fecfiler.transactions.aggregation import (
                        process_aggregation_for_debts,
                    )

                    process_aggregation_for_debts(self.debt)
                elif self.schedule_d is not None:
                    from fecfiler.transactions.aggregation import (
                        process_aggregation_for_debts,
                    )

                    process_aggregation_for_debts(self)
            except Exception as e:
                logger.error(
                    "Failed to process debt aggregation on delete",
                    transaction_id=self.id,
                    error=str(e),
                    exc_info=True,
                )
            self.delete_children()
            self.delete_debts()
            self.delete_loans()
            self.delete_reattribution_redesigntations()
            self.delete_coupled_transactions()
            if self.memo_text:
                self.memo_text.delete()

    def delete_children(self):
        child_transactions = Transaction.objects.filter(parent_transaction=self)
        for child in child_transactions:
            child.delete()

    # transactions related to this debt
    # delete any carry forwards or repayments related to this debt
    def delete_debts(self):
        debt_carry_forwards_and_repayments = Transaction.objects.filter(debt=self)
        for carry_forward_or_repayment in debt_carry_forwards_and_repayments:
            carry_forward_or_repayment.delete()

    # transactions related to a loan
    # delete any carry forwards or repayments related to this loan
    def delete_loans(self):
        loan_carry_forwards_and_repayments = Transaction.objects.filter(loan=self)
        for carry_forward_or_repayment in loan_carry_forwards_and_repayments:
            carry_forward_or_repayment.delete()

    # REATTRIBUTION/REDESIGNATION
    # If this is a reattribution/redesignation 'from' transaction,
    # delete the 'to' transaction
    def delete_reattribution_redesigntations(self):
        if (
            self.schedule_a
            and self.schedule_a.reattribution_redesignation_tag == "REATTRIBUTED_FROM"
        ) or (
            self.schedule_b
            and self.schedule_b.reattribution_redesignation_tag == "REDESIGNATED_FROM"
        ):
            # Refresh parent's state from DB before calling delete
            parent = self.parent_transaction
            parent.refresh_from_db(fields=["deleted"])
            parent.delete()

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
            # Refresh reatt_redes' state from DB before calling delete
            reatt_redes = self.reatt_redes
            reatt_redes.refresh_from_db(fields=["deleted"])
            reatt_redes.delete()

        # Delete any reattribution/redesignation transactions
        # related to this transaction (copy/from/to)"
        reatributions_and_redesignations = Transaction.objects.filter(reatt_redes=self)
        for reatribuiton_or_redesignation in reatributions_and_redesignations:
            reatribuiton_or_redesignation.delete()

    def delete_coupled_transactions(self):
        if (
            self.parent_transaction
            and self.transaction_type_identifier in COUPLED_TRANSACTION_TYPES
        ):
            # Refresh parent's state from DB before calling delete
            # to ensure we have the current deleted status
            parent = self.parent_transaction
            parent.refresh_from_db(fields=["deleted"])
            parent.delete()

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
