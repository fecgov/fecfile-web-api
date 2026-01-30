from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_f.models import ScheduleF
from fecfiler.transactions.utils_aggregation_queries import (
    filter_queryset_for_previous_transactions_in_aggregation,
)  # noqa: E501
from fecfiler.transactions.utils_aggregation_prep import _get_calendar_year_from_date

from django.db.models import Q
import structlog


logger = structlog.get_logger(__name__)


def process_aggregation_for_debts(transaction_instance):
    transactions = Transaction.objects.filter(
        committee_account_id=transaction_instance.committee_account_id
    )
    # Get the transaction out of the queryset in order to populate annotated fields
    transaction = transactions.filter(id=transaction_instance.id).first()
    if transaction is None:
        return

    given_debt = transaction if transaction.schedule_d is not None else transaction.debt
    if given_debt is None:
        return

    debt_transaction_id = given_debt.transaction_id

    debt_chain = transactions.filter(
        schedule_d__isnull=False,
        committee_account_id=given_debt.committee_account_id,
        transaction_id=debt_transaction_id,
    ).order_by("schedule_d__report_coverage_from_date")

    incurred_prior = 0
    repayed_amount = 0
    schedule_ds = []
    for debt in debt_chain:
        debt.schedule_d.incurred_prior = incurred_prior
        incurred_prior += debt.schedule_d.incurred_amount

        debt.schedule_d.payment_prior = repayed_amount
        debt.schedule_d.beginning_balance = (
            debt.schedule_d.incurred_prior - repayed_amount
        )

        repayed_during = 0
        repayments = transactions.filter(
            schedule_d__isnull=True,
            debt__id=debt.id,
            deleted__isnull=True,
        )
        for repayment in repayments:
            repayed_during += repayment.amount

        debt.schedule_d.payment_amount = repayed_during
        debt.schedule_d.balance_at_close = (
            debt.schedule_d.beginning_balance
            + debt.schedule_d.incurred_amount
            - repayed_during
        )
        repayed_amount += repayed_during

        schedule_ds.append(debt.schedule_d)

    ScheduleD.objects.bulk_update(
        schedule_ds,
        [
            "incurred_prior",
            "payment_prior",
            "payment_amount",
            "beginning_balance",
            "balance_at_close",
        ],
        batch_size=64,
    )


def process_aggregation_by_payee_candidate(transaction_instance, old_snapshot=None):
    # Get the transaction out of the queryset in order to populate annotated fields
    transaction = Transaction.objects.filter(id=transaction_instance.id).first()

    if transaction is None:
        return

    queryset = Transaction.objects.filter(
        committee_account_id=transaction_instance.committee_account_id
    )

    shared_entity_transactions = queryset.filter(
        date__year=transaction.date.year,
        contact_2=transaction.contact_2,
        aggregation_group=transaction.aggregation_group,
        schedule_f__isnull=False,
        schedule_f__general_election_year=transaction.schedule_f.general_election_year,  # noqa: E501
    )

    previous_transactions = filter_queryset_for_previous_transactions_in_aggregation(
        shared_entity_transactions,
        transaction.date,
        transaction.aggregation_group,
        transaction.id,
        None,
        transaction.contact_2_id,
        None,
        transaction.schedule_f.general_election_year,
    )

    # Identify all transactions to recalculate
    # When date changes, recalculate all transactions from first affected date
    # Otherwise, recalculate current transaction and all future-dated transactions
    old_date = old_snapshot.get("date") if old_snapshot else None
    date_changed = old_date and old_date != transaction.date

    if date_changed:
        # Date changed: recalculate all transactions from the earliest affected date
        earliest_affected_date = min(old_date, transaction.date)
        to_update = shared_entity_transactions.filter(
            date__gte=earliest_affected_date
        ).order_by("date", "created")
    else:
        # No date change: recalculate current transaction and all future-dated
        to_update = shared_entity_transactions.filter(
            Q(id=transaction.id)
            | Q(date__gt=transaction.date)
            | Q(Q(date=transaction.date) & Q(created__gt=transaction.created))
        ).order_by("date", "created")

    previous_transaction = previous_transactions.first()
    updated_schedule_fs = []
    previous_aggregate_value = 0

    # When date changes, all transactions are recalculated together,
    # so we start from 0 instead of using previous_transaction's aggregate
    if not date_changed and previous_transaction:
        previous_aggregate_value = (
            previous_transaction.schedule_f.aggregate_general_elec_expended
        )

    for trans in to_update:
        trans.schedule_f.aggregate_general_elec_expended = (
            trans.schedule_f.expenditure_amount + previous_aggregate_value
        )
        updated_schedule_fs.append(trans.schedule_f)
        # Use the newly calculated aggregate for the next iteration, not DB value
        previous_aggregate_value = trans.schedule_f.aggregate_general_elec_expended
        previous_transaction = trans

    ScheduleF.objects.bulk_update(
        updated_schedule_fs, ["aggregate_general_elec_expended"], batch_size=64
    )


def process_aggregation_for_entity_contact(
    committee_account_id,
    aggregation_group,
    contact_1_id,
    earliest_date=None,
):
    query_filter = {
        "committee_account_id": committee_account_id,
        "aggregation_group": aggregation_group,
        "contact_1_id": contact_1_id,
        "force_unaggregated__isnull": True,
    }

    all_transactions = (
        Transaction.objects.filter(**query_filter)
        .order_by("date", "created")
        .annotate(agg=Transaction.objects.ENTITY_AGGREGATE_CLAUSE())
    )

    # If earliest_date specified, only update transactions >= that date
    if earliest_date is not None:
        transactions_to_update = [
            t for t in all_transactions if t.date >= earliest_date
        ]
    else:
        transactions_to_update = list(all_transactions)

    for transaction in transactions_to_update:
        transaction.aggregate = transaction.agg

    if transactions_to_update:
        Transaction.objects.bulk_update(transactions_to_update, ["aggregate"])


def process_aggregation_for_entity(transaction_instance, earliest_date=None):
    process_aggregation_for_entity_contact(
        transaction_instance.committee_account_id,
        transaction_instance.aggregation_group,
        transaction_instance.contact_1_id,
        earliest_date,
    )


def process_aggregation_for_election(transaction_instance, earliest_date=None):
    """
    Recalculate election aggregates for Schedule E transactions.

    Updates _calendar_ytd_per_election_office for all transactions in the same
    election partition (election_code, candidate_office, state, district, year).

    Args:
        transaction_instance: The Schedule E transaction instance
        earliest_date: If specified, only update transactions on or after this date
    """
    if not transaction_instance.schedule_e:
        return

    if not transaction_instance.contact_2:
        return

    schedule_e = transaction_instance.schedule_e
    contact_2 = transaction_instance.contact_2

    # Get the date - handle both date objects and date strings
    transaction_date = transaction_instance.get_date()
    if not transaction_date:
        return

    year = _get_calendar_year_from_date(transaction_date)

    # Build query filter for the election partition
    # Query ALL transactions (no date filter) so window function has complete history
    query_filter = {
        "committee_account_id": transaction_instance.committee_account_id,
        "aggregation_group": transaction_instance.aggregation_group,
        "schedule_e__election_code": schedule_e.election_code,
        "contact_2__candidate_office": contact_2.candidate_office,
        "date__year": year,
        "force_unaggregated__isnull": True,
        "deleted__isnull": True,
    }

    # Handle optional state/district fields
    if contact_2.candidate_state:
        query_filter["contact_2__candidate_state"] = contact_2.candidate_state
    else:
        query_filter["contact_2__candidate_state__isnull"] = True

    if contact_2.candidate_district:
        query_filter["contact_2__candidate_district"] = contact_2.candidate_district

    # Get ALL transactions in this election partition and annotate with running sum
    all_transactions = (
        Transaction.objects.filter(**query_filter)
        .order_by("date", "created")
        .annotate(election_agg=Transaction.objects.ELECTION_AGGREGATE_CLAUSE())
    )

    # If earliest_date specified, only update transactions >= that date
    if earliest_date is not None:
        transactions_to_update = [
            t for t in all_transactions if t.date >= earliest_date
        ]
    else:
        transactions_to_update = list(all_transactions)

    # Update transactions with their calculated aggregates
    for trans in transactions_to_update:
        trans._calendar_ytd_per_election_office = trans.election_agg

    if transactions_to_update:
        Transaction.objects.bulk_update(
            transactions_to_update,
            ["_calendar_ytd_per_election_office"],
            batch_size=64
        )
