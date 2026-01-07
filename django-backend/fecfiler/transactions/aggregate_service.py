"""
Functions for calculating and updating transaction aggregates.

These functions handles the calculation of aggregates for Schedule A and Schedule B
transactions that are grouped by entity (contact, calendar year, and aggregation group),
as well as aggregates for Schedule E transactions grouped by election office.

Previously, these calculations were done in database triggers. This moves
that logic into Django code for better maintainability and testability.
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID
from django.db.models import Q, F, Value
from django.db.models.fields import DecimalField
from .models import Transaction
from .managers import Schedule, TransactionManager
import structlog

logger = structlog.get_logger(__name__)


def _update_aggregate_running_sum(
    transactions, aggregate_field_name: str, log_context: str
) -> int:
    """
    Calculate and update running sum aggregates for transactions.

    Calculates running sum of effective amounts for transactions and updates
    the specified aggregate field.

    Args:
        transactions: QuerySet of transactions to aggregate (ordered)
        aggregate_field_name: Name of field to update ('aggregate' or
            '_calendar_ytd_per_election_office')
        log_context: String with logging context info

    Returns:
        Number of transactions updated
    """
    if not transactions.exists():
        logger.debug(f"No transactions found for aggregation: {log_context}")
        return 0

    # Annotate running sums in the database (window function), then bulk update
    txn_manager = TransactionManager()
    window_clause = (
        txn_manager.ENTITY_AGGREGATE_CLAUSE()
        if aggregate_field_name == "aggregate"
        else txn_manager.ELECTION_AGGREGATE_CLAUSE()
    )

    annotated = transactions.annotate(
        amount=txn_manager.AMOUNT_CLAUSE,
        effective_amount=txn_manager.EFFECTIVE_AMOUNT_CLAUSE,
        sub_agg=window_clause,
    )

    updates = [
        Transaction(id=row.id, **{aggregate_field_name: row.sub_agg})
        for row in annotated
    ]

    Transaction.objects.bulk_update(updates, [aggregate_field_name])
    update_count = len(updates)

    logger.info(
        f"Updated {update_count} transactions for aggregation: {log_context}"
    )
    return update_count


def calculate_entity_aggregates(
    contact_1_id: UUID, year: int, aggregation_group: str
) -> int:
    """
    Calculate and update aggregate values for Schedule A/B transactions.

    Aggregates are calculated as a running sum of effective amounts for all
    transactions matching the given entity (contact, calendar year, aggregation group),
    ordered by date and creation time.

    Args:
        contact_1_id: UUID of the contact (entity)
        year: Calendar year for aggregation
        aggregation_group: Aggregation group identifier

    Returns:
        Number of transactions updated
    """
    # Get all matching transactions ordered by date and created
    # Exclude force_unaggregated transactions as they don't get aggregated
    transactions = Transaction.objects.filter(
        contact_1_id=contact_1_id,
        date__year=year,
        aggregation_group=aggregation_group,
        deleted__isnull=True,
        force_unaggregated__isnull=True,
    ).filter(
        Q(schedule_a__isnull=False) | Q(schedule_b__isnull=False)
    ).order_by("date", "created").select_related("schedule_a", "schedule_b")

    log_context = f"contact_1={contact_1_id}, year={year}, group={aggregation_group}"
    return _update_aggregate_running_sum(transactions, "aggregate", log_context)


def calculate_calendar_ytd_per_election_office(
    election_code: str,
    candidate_office: str,
    candidate_state: Optional[str],
    candidate_district: Optional[str],
    year: int,
    aggregation_group: str,
    committee_account_id: Optional[UUID] = None
) -> int:
    """
    Calculate and update calendar YTD aggregates for Schedule E transactions.

    Aggregates are calculated as a running sum of effective amounts for all
    Schedule E transactions matching the given election office criteria,
    ordered by date and creation time.

    Args:
        election_code: Election code identifier
        candidate_office: Candidate office (e.g., 'P', 'S', 'H')
        candidate_state: Candidate state (may be None or empty string)
        candidate_district: Candidate district (may be None or empty string)
        year: Calendar year for aggregation
        aggregation_group: Aggregation group identifier

    Returns:
        Number of transactions updated
    """
    # Handle None/empty string values for state and district
    state_filter = Q(contact_2__candidate_state=candidate_state)
    if not candidate_state:
        state_filter = Q(contact_2__candidate_state__isnull=True) | Q(
            contact_2__candidate_state=""
        )

    district_filter = Q(contact_2__candidate_district=candidate_district)
    if not candidate_district:
        district_filter = Q(contact_2__candidate_district__isnull=True) | Q(
            contact_2__candidate_district=""
        )

    # Get all matching Schedule E transactions ordered by date and created
    # Exclude force_unaggregated transactions as they don't get aggregated
    query_filters = {
        "schedule_e__election_code": election_code,
        "contact_2__candidate_office": candidate_office,
        "date__year": year,
        "aggregation_group": aggregation_group,
        "deleted__isnull": True,
        "schedule_e__isnull": False,
        "force_unaggregated__isnull": True,
    }

    # Filter by committee_account_id if provided
    if committee_account_id:
        query_filters["committee_account_id"] = committee_account_id

    transactions = Transaction.objects.filter(
        **query_filters
    ).filter(state_filter, district_filter).order_by(
        "date", "created"
    ).select_related("schedule_e", "contact_2")

    log_context = (
        f"election_code={election_code}, office={candidate_office}, "
        f"state={candidate_state}, district={candidate_district}, year={year}"
    )
    return _update_aggregate_running_sum(
        transactions, "_calendar_ytd_per_election_office", log_context
    )


def _get_schedule_amount(transaction) -> Optional[Decimal]:
    """
    Extract the base amount from related schedule.

    Args:
        transaction: Transaction instance

    Returns:
        Decimal amount from the transaction's schedule, or None if not found
    """
    schedule_map = {
        "schedule_a": "contribution_amount",
        "schedule_b": "expenditure_amount",
        "schedule_c2": "guaranteed_amount",
        "schedule_d": "incurred_amount",
        "schedule_e": "expenditure_amount",
        "schedule_f": "expenditure_amount",
    }

    for schedule_name, amount_field in schedule_map.items():
        schedule = getattr(transaction, schedule_name, None)
        if schedule:
            return getattr(schedule, amount_field, None)

    if transaction.debt and transaction.debt.schedule_d:
        return transaction.debt.schedule_d.incurred_amount

    return None


def calculate_effective_amount(transaction) -> Decimal:
    """
    Calculate the effective amount for a transaction.

    The effective amount is used for aggregation calculations and differs from
    the transaction amount for certain transaction types (e.g., refunds are
    negated) and for certain schedules (e.g., Schedule C has no effective amount).

    Args:
        transaction: Transaction instance

    Returns:
        Decimal: The effective amount for aggregation
    """
    from .constants import SCHEDULE_B_REFUND_TYPES

    # Schedule C transactions have no effective amount for aggregation
    if transaction.schedule_c_id is not None:
        return Decimal(0)

    # Get the base amount from related schedule
    amount = _get_schedule_amount(transaction)

    if amount is None:
        return Decimal(0)

    # Ensure Decimal type for downstream arithmetic before any operations
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    # Refunds are negated
    if transaction.transaction_type_identifier in SCHEDULE_B_REFUND_TYPES:
        amount = amount * Decimal(-1)

    return amount


def _get_calendar_year_from_date(date_obj) -> int:
    """
    Parse calendar year from date object or date string in YYYY-MM-DD format.

    Args:
        date_obj: Date object with .year attribute or date string

    Returns:
        Integer year value
    """
    return date_obj.year if hasattr(date_obj, 'year') else int(str(date_obj)[:4])


def _update_suffix_delta(
    base_qs,
    aggregate_field_name: str,
    key_date,
    key_created,
    delta: Decimal,
    include_self: bool,
) -> int:
    """
    Apply a delta to aggregates for the suffix of a partition.

    Updates rows with date > key_date, and rows with date == key_date and
    created >= key_created (or >, based on include_self) by adding `delta` to
    the specified aggregate field.

    Args:
        base_qs: Partition-filtered queryset
        aggregate_field_name: Field name to update ('aggregate' or election YTD)
        key_date: Date anchor for suffix selection
        key_created: Created timestamp anchor for suffix selection
        delta: Decimal delta to add (can be negative)
        include_self: Whether to include the anchor row itself in the update

    Returns:
        Number of rows updated (sum of both updates)
    """
    if delta == 0:
        return 0

    op_equal = "created__gte" if include_self else "created__gt"

    # Update all rows strictly after the anchor date
    updated_after = base_qs.filter(date__gt=key_date).update(
        **{aggregate_field_name: F(aggregate_field_name) + Value(
            delta, output_field=DecimalField()
        )}
    )

    # Update rows on the same date and at/after the anchor creation time
    updated_same_day = base_qs.filter(date=key_date).filter(
        **{op_equal: key_created}
    ).update(
        **{aggregate_field_name: F(aggregate_field_name) + Value(
            delta, output_field=DecimalField()
        )}
    )

    return int(updated_after) + int(updated_same_day)


def _get_previous_aggregate_value(
    base_qs,
    aggregate_field_name: str,
    key_date,
    key_created,
) -> Decimal:
    """
    Get the aggregate value from the row immediately preceding the anchor.

    Args:
        base_qs: Partition-filtered queryset
        aggregate_field_name: Field name to read
        key_date: Anchor date
        key_created: Anchor created timestamp

    Returns:
        Decimal previous aggregate value (0 if none)
    """
    prev = (
        base_qs.filter(Q(date__lt=key_date) | Q(date=key_date, created__lt=key_created))
        .order_by("-date", "-created")
        .values_list(aggregate_field_name, flat=True)
        .first()
    )
    return prev if isinstance(prev, Decimal) else Decimal(prev or 0)


def apply_delta_aggregates(
    transaction_instance, old_state: Optional[Dict[str, Any]], created: bool
) -> None:
    """
    Apply efficient delta-based updates to aggregates for a single change.

    Handles create, update, and partition moves by adjusting only the suffix
    within affected partitions using set-based updates.

    Args:
        transaction_instance: The saved Transaction instance
        old_state: Snapshot dict of prior key fields and effective amount
        created: Whether this is a creation event
    """
    if transaction_instance.deleted:
        return

    schedule = transaction_instance.get_schedule_name()
    transaction_date = transaction_instance.get_date()
    if not transaction_date:
        return

    new_created = transaction_instance.created

    if schedule in [Schedule.A, Schedule.B]:
        # Build new partition queryset
        year = _get_calendar_year_from_date(transaction_date)
        new_qs = (
            Transaction.objects.filter(
                contact_1_id=transaction_instance.contact_1_id,
                date__year=year,
                aggregation_group=transaction_instance.aggregation_group,
                deleted__isnull=True,
                force_unaggregated__isnull=True,
            )
            .filter(Q(schedule_a__isnull=False) | Q(schedule_b__isnull=False))
        )

        new_eff = calculate_effective_amount(transaction_instance)
        new_force_unagg = transaction_instance.force_unaggregated is not None
        new_eff_contrib = Decimal(0) if new_force_unagg else (new_eff or Decimal(0))

        # If created, set this row's aggregate explicitly and bump suffix
        if created or not old_state:
            base = _get_previous_aggregate_value(
                new_qs, "aggregate", transaction_date, new_created
            )
            if not new_force_unagg:
                new_value = base + new_eff_contrib
                if transaction_instance.aggregate != new_value:
                    transaction_instance.aggregate = new_value
                    transaction_instance.save(update_fields=["aggregate"])
            _update_suffix_delta(
                new_qs, "aggregate", transaction_date, new_created,
                new_eff_contrib, include_self=False
            )
            return

        # Update with delta or handle partition move
        old_year = _get_calendar_year_from_date(
            old_state["date"]
        ) if old_state.get("date") else year

        same_partition = (
            old_state.get("contact_1_id") == transaction_instance.contact_1_id
            and old_year == year
            and old_state.get("aggregation_group")
            == transaction_instance.aggregation_group
        )

        old_eff = old_state.get("effective_amount", Decimal(0))
        old_force_unagg = old_state.get("force_unaggregated") is not None
        old_eff_contrib = Decimal(0) if old_force_unagg else (
            old_eff or Decimal(0)
        )
        delta = new_eff_contrib - old_eff_contrib

        moved = (
            old_state.get("date") != transaction_date
            or old_state.get("created") != new_created
        )

        # Derive expected anchor value at new position regardless of snapshot
        derived_base = _get_previous_aggregate_value(
            new_qs, "aggregate", transaction_date, new_created
        )

        if same_partition and not moved:
            if delta != 0:
                _update_suffix_delta(
                    new_qs, "aggregate", transaction_date, new_created,
                    delta, include_self=True
                )
            else:
                # If aggregate does not match expected, recompute partition
                expected = derived_base + new_eff_contrib
                if transaction_instance.aggregate != expected:
                    recompute_qs = new_qs.order_by(
                        "date", "created"
                    ).select_related("schedule_a", "schedule_b")
                    _update_aggregate_running_sum(
                        recompute_qs, "aggregate",
                        "entity derive-mismatch"
                    )
            return

        if same_partition and moved:
            # Fallback: recompute entire partition when ordering changes
            recompute_qs = new_qs.order_by(
                "date", "created"
            ).select_related("schedule_a", "schedule_b")
            _update_aggregate_running_sum(
                recompute_qs, "aggregate", "entity move"
            )
            return

        # Partition changed: subtract from old partition suffix, then add to new
        old_qs = (
            Transaction.objects.filter(
                contact_1_id=old_state.get("contact_1_id"),
                date__year=old_year,
                aggregation_group=old_state.get("aggregation_group"),
                deleted__isnull=True,
                force_unaggregated__isnull=True,
            )
            .filter(Q(schedule_a__isnull=False) | Q(schedule_b__isnull=False))
        )
        _update_suffix_delta(
            old_qs,
            "aggregate",
            old_state.get("date"),
            old_state.get("created"),
            -old_eff_contrib,
            include_self=False,
        )

        # Set new row aggregate explicitly based on previous agg in new partition
        base = _get_previous_aggregate_value(
            new_qs, "aggregate", transaction_date, new_created
        )
        if not new_force_unagg:
            new_value = base + new_eff_contrib
            if transaction_instance.aggregate != new_value:
                transaction_instance.aggregate = new_value
                transaction_instance.save(update_fields=["aggregate"])
        _update_suffix_delta(
            new_qs, "aggregate", transaction_date, new_created,
            new_eff_contrib, include_self=False
        )
        return

    elif schedule == Schedule.E:
        schedule_e = transaction_instance.schedule_e
        contact_2 = transaction_instance.contact_2
        if not schedule_e or not contact_2:
            return

        year = _get_calendar_year_from_date(transaction_date)

        state_filter = Q(contact_2__candidate_state=contact_2.candidate_state)
        if not contact_2.candidate_state:
            state_filter = (
                Q(contact_2__candidate_state__isnull=True)
                | Q(contact_2__candidate_state="")
            )

        district_filter = Q(
            contact_2__candidate_district=contact_2.candidate_district
        )
        if not contact_2.candidate_district:
            district_filter = (
                Q(contact_2__candidate_district__isnull=True)
                | Q(contact_2__candidate_district="")
            )

        base_filters = dict(
            schedule_e__election_code=schedule_e.election_code,
            contact_2__candidate_office=contact_2.candidate_office,
            date__year=year,
            aggregation_group=transaction_instance.aggregation_group,
            deleted__isnull=True,
            schedule_e__isnull=False,
            force_unaggregated__isnull=True,
        )
        if transaction_instance.committee_account_id:
            base_filters["committee_account_id"] = (
                transaction_instance.committee_account_id
            )
        new_qs = Transaction.objects.filter(**base_filters).filter(
            state_filter, district_filter
        )

        new_eff = calculate_effective_amount(transaction_instance)
        new_force_unagg = transaction_instance.force_unaggregated is not None
        new_eff_contrib = Decimal(0) if new_force_unagg else (new_eff or Decimal(0))

        if created or not old_state:
            base = _get_previous_aggregate_value(
                new_qs, "_calendar_ytd_per_election_office", transaction_date, new_created
            )
            if not new_force_unagg:
                new_value = base + new_eff_contrib
                if transaction_instance._calendar_ytd_per_election_office != new_value:
                    transaction_instance._calendar_ytd_per_election_office = new_value
                    transaction_instance.save(
                        update_fields=["_calendar_ytd_per_election_office"]
                    )
            _update_suffix_delta(
                new_qs,
                "_calendar_ytd_per_election_office",
                transaction_date,
                new_created,
                new_eff_contrib,
                include_self=False,
            )
            return

        old_year = _get_calendar_year_from_date(
            old_state["date"]
        ) if old_state.get("date") else year

        same_partition = (
            old_state.get("election_code") == schedule_e.election_code
            and old_state.get("candidate_office") == contact_2.candidate_office
            and old_state.get("candidate_state") == contact_2.candidate_state
            and old_state.get("candidate_district") == contact_2.candidate_district
            and old_year == year
            and old_state.get("aggregation_group")
            == transaction_instance.aggregation_group
            and old_state.get("committee_account_id")
            == transaction_instance.committee_account_id
        )

        old_eff = old_state.get("effective_amount", Decimal(0))
        old_force_unagg = old_state.get("force_unaggregated") is not None
        old_eff_contrib = Decimal(0) if old_force_unagg else (old_eff or Decimal(0))
        delta = new_eff_contrib - old_eff_contrib

        moved = (
            old_state.get("date") != transaction_date
            or old_state.get("created") != new_created
        )

        if same_partition and not moved:
            if delta != 0:
                _update_suffix_delta(
                    new_qs,
                    "_calendar_ytd_per_election_office",
                    transaction_date,
                    new_created,
                    delta,
                    include_self=True,
                )
            return

        # Handle partition move: subtract from old partition, then add in new
        old_state_state = old_state.get("candidate_state")
        old_state_filter = Q(contact_2__candidate_state=old_state_state)
        if not old_state_state:
            old_state_filter = (
                Q(contact_2__candidate_state__isnull=True)
                | Q(contact_2__candidate_state="")
            )

        old_district = old_state.get("candidate_district")
        old_district_filter = Q(contact_2__candidate_district=old_district)
        if not old_district:
            old_district_filter = (
                Q(contact_2__candidate_district__isnull=True)
                | Q(contact_2__candidate_district="")
            )

        old_base_filters = dict(
            schedule_e__election_code=old_state.get("election_code"),
            contact_2__candidate_office=old_state.get("candidate_office"),
            date__year=old_year,
            aggregation_group=old_state.get("aggregation_group"),
            deleted__isnull=True,
            schedule_e__isnull=False,
            force_unaggregated__isnull=True,
        )
        if old_state.get("committee_account_id"):
            old_base_filters["committee_account_id"] = old_state.get(
                "committee_account_id"
            )
        old_qs = Transaction.objects.filter(
            **old_base_filters
        ).filter(old_state_filter, old_district_filter)

        _update_suffix_delta(
            old_qs,
            "_calendar_ytd_per_election_office",
            old_state.get("date"),
            old_state.get("created"),
            -old_eff_contrib,
            include_self=False,
        )

        base = _get_previous_aggregate_value(
            new_qs, "_calendar_ytd_per_election_office", transaction_date, new_created
        )
        if not new_force_unagg:
            new_value = base + new_eff_contrib
            if transaction_instance._calendar_ytd_per_election_office != new_value:
                transaction_instance._calendar_ytd_per_election_office = new_value
                transaction_instance.save(
                    update_fields=["_calendar_ytd_per_election_office"]
                )
        _update_suffix_delta(
            new_qs,
            "_calendar_ytd_per_election_office",
            transaction_date,
            new_created,
            new_eff_contrib,
            include_self=False,
        )
        return


def apply_delete_delta_aggregates(old_state: Dict[str, Any]) -> None:
    """
    Apply a negative delta for a deleted transaction to downstream aggregates.

    Uses the snapshot of the deleted row to subtract its effective amount from
    the suffix of the appropriate partition.
    """
    if not old_state:
        return

    schedule = old_state.get("schedule")
    old_date = old_state.get("date")
    old_created = old_state.get("created")
    if not old_date or not old_created:
        return

    if schedule in [Schedule.A, Schedule.B]:
        old_year = _get_calendar_year_from_date(old_date)
        old_qs = (
            Transaction.objects.filter(
                contact_1_id=old_state.get("contact_1_id"),
                date__year=old_year,
                aggregation_group=old_state.get("aggregation_group"),
                deleted__isnull=True,
                force_unaggregated__isnull=True,
            )
            .filter(Q(schedule_a__isnull=False) | Q(schedule_b__isnull=False))
        )
        old_eff = old_state.get("effective_amount", Decimal(0))
        _update_suffix_delta(
            old_qs, "aggregate", old_date, old_created,
            -(old_eff or Decimal(0)),
            include_self=False
        )
        return

    if schedule == Schedule.E:
        old_year = _get_calendar_year_from_date(old_date)

        old_state_state = old_state.get("candidate_state")
        old_state_filter = Q(contact_2__candidate_state=old_state_state)
        if not old_state_state:
            old_state_filter = (
                Q(contact_2__candidate_state__isnull=True)
                | Q(contact_2__candidate_state="")
            )

        old_district = old_state.get("candidate_district")
        old_district_filter = Q(contact_2__candidate_district=old_district)
        if not old_district:
            old_district_filter = (
                Q(contact_2__candidate_district__isnull=True)
                | Q(contact_2__candidate_district="")
            )

        old_qs = (
            Transaction.objects.filter(
                schedule_e__election_code=old_state.get("election_code"),
                contact_2__candidate_office=old_state.get("candidate_office"),
                date__year=old_year,
                aggregation_group=old_state.get("aggregation_group"),
                deleted__isnull=True,
                schedule_e__isnull=False,
                force_unaggregated__isnull=True,
                committee_account_id=old_state.get("committee_account_id"),
            )
            .filter(old_state_filter, old_district_filter)
        )
        old_eff = old_state.get("effective_amount", Decimal(0))
        _update_suffix_delta(
            old_qs,
            "_calendar_ytd_per_election_office",
            old_date,
            old_created,
            -(old_eff or Decimal(0)),
            include_self=False,
        )
        return


def calculate_loan_payment_to_date(loan_id: UUID) -> int:
    """
    Calculate the cumulative loan payment to date for a given loan.

    Sums all LOAN_REPAYMENT_MADE transactions associated with the loan,
    ordered by date and creation time. For carried forward loans, also includes
    repayments from the parent loan chain.

    Args:
        loan_id: UUID of the loan transaction

    Returns:
        Number of loan transactions updated (the loan itself)
    """
    from .models import Transaction

    # Get the loan transaction
    try:
        loan = Transaction.objects.select_related('loan', 'loan__schedule_c').get(
            id=loan_id, deleted__isnull=True
        )
    except Transaction.DoesNotExist:
        logger.warning(f"Loan transaction {loan_id} not found")
        return 0

    # Collect all loan IDs in the parent chain (for carried forward loans)
    # Carried forward loans reference their parent via the 'loan' field
    loan_ids = [loan_id]
    current_loan = loan

    # Walk up the loan chain to find the original loan
    max_depth = 10  # Prevent infinite loops
    depth = 0
    while current_loan.loan_id and depth < max_depth:
        parent_loan = current_loan.loan
        if parent_loan and parent_loan.schedule_c:
            loan_ids.append(parent_loan.id)
            current_loan = parent_loan
            depth += 1
        else:
            break

    # Get all loan repayment transactions for all loans in the chain
    repayments = Transaction.objects.filter(
        loan_id__in=loan_ids,
        transaction_type_identifier="LOAN_REPAYMENT_MADE",
        deleted__isnull=True,
        schedule_b__isnull=False,
    ).order_by("date", "created").select_related("schedule_b")

    # Calculate the cumulative payment amount
    total_payment = Decimal(0)
    for repayment in repayments:
        if repayment.schedule_b and repayment.schedule_b.expenditure_amount:
            total_payment += repayment.schedule_b.expenditure_amount

    # Update the loan transaction's loan_payment_to_date field
    if loan.loan_payment_to_date != total_payment:
        loan.loan_payment_to_date = total_payment
        loan.save(update_fields=["loan_payment_to_date"])
        logger.info(
            f"Updated loan_payment_to_date for loan {loan_id}: {total_payment}"
        )
        # Propagate updated totals to any carried-forward child loans
        child_loans = Transaction.objects.filter(
            loan_id=loan_id,
            deleted__isnull=True,
        ).exclude(id=loan_id).values_list("id", flat=True)
        for child_loan_id in child_loans:
            calculate_loan_payment_to_date(child_loan_id)
        return 1

    return 0


def recalculate_aggregates_for_transaction(transaction_instance) -> None:
    """
    Recalculate aggregates for a transaction and any affected related transactions.

    This function determines which aggregates need to be recalculated based on the
    transaction's schedule type and then calls the appropriate aggregate calculation
    function.

    Args:
        transaction_instance: Transaction model instance
    """
    if transaction_instance.deleted:
        # Skip calculations for deleted transactions
        return

    schedule = transaction_instance.get_schedule_name()
    transaction_date = transaction_instance.get_date()

    # If there's no transaction date, we can't aggregate
    if not transaction_date:
        return

    try:
        if schedule in [Schedule.A, Schedule.B]:
            # If this is a loan repayment, recalculate loan_payment_to_date
            if (transaction_instance.transaction_type_identifier == "LOAN_REPAYMENT_MADE"
                    and transaction_instance.loan_id):
                calculate_loan_payment_to_date(transaction_instance.loan_id)

        elif schedule == Schedule.E:
            schedule_e = transaction_instance.schedule_e
            contact_2 = transaction_instance.contact_2

            if schedule_e and contact_2:
                # Election aggregates handled by delta updates in signals
                pass
    except Exception as e:
        logger.error(
            f"Error recalculating aggregates for transaction "
            f"{transaction_instance.id}: {e}",
            exc_info=True,
        )
        raise
