from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_f.models import ScheduleF
from fecfiler.transactions.utils import (
    filter_queryset_for_previous_transactions_in_aggregation,
)  # noqa: E501

from django.db.models import Q
import structlog


logger = structlog.get_logger(__name__)


def process_aggregation_for_debts(transaction_instance):
    transaction_view = Transaction.objects.transaction_view().filter(
        committee_account_id=transaction_instance.committee_account_id
    )
    # Get the transaction out of the queryset in order to populate annotated fields
    transaction = transaction_view.filter(id=transaction_instance.id).first()
    if transaction is None:
        return

    given_debt = transaction if transaction.schedule_d is not None else transaction.debt
    if given_debt is None:
        return

    original_debt_trans_id = given_debt.transaction_id
    if given_debt.parent_transaction is not None:
        original_debt_trans_id = given_debt.parent_transaction.transaction_id

    original_debt = transaction_view.filter(
        committee_account_id=given_debt.committee_account_id,
        transaction_id=original_debt_trans_id
    ).first()

    child_debts = transaction_view.filter(
        schedule_d__isnull=False,
        committee_account_id=given_debt.committee_account_id,
        back_reference_tran_id_number=original_debt_trans_id
    ).order_by("schedule_d__report_coverage_from_date")

    incurred_prior = 0
    repayed_amount = 0
    schedule_ds = []
    for debt in [original_debt, *child_debts]:
        debt.schedule_d.incurred_prior = incurred_prior
        incurred_prior += debt.schedule_d.incurred_amount

        debt.schedule_d.payment_prior = repayed_amount
        debt.schedule_d.beginning_balance = (
            debt.schedule_d.incurred_prior - repayed_amount
        )

        repayed_during = 0
        repayments = transaction_view.filter(
            schedule_d__isnull=True,
            debt__id=debt.id,
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
            "balance_at_close"
        ],
        batch_size=64
    )


def process_aggregation_by_payee_candidate(transaction_instance):
    # Get the transaction out of the queryset in order to populate annotated fields
    transaction_view = Transaction.objects.transaction_view()
    transaction = transaction_view.filter(id=transaction_instance.id).first()

    if transaction is None:
        return

    queryset = transaction_view.filter(
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

    to_update = shared_entity_transactions.filter(
        Q(id=transaction.id)
        | Q(date__gt=transaction.date)
        | Q(Q(date=transaction.date) & Q(created__gt=transaction.created))
    ).order_by("date", "created")

    previous_transaction = previous_transactions.first()
    updated_schedule_fs = []
    for trans in to_update:
        previous_aggregate = 0
        if previous_transaction:
            previous_aggregate = (
                previous_transaction.schedule_f.aggregate_general_elec_expended
            )

        trans.schedule_f.aggregate_general_elec_expended = (
            trans.schedule_f.expenditure_amount + previous_aggregate
        )
        updated_schedule_fs.append(trans.schedule_f)
        previous_transaction = trans

    ScheduleF.objects.bulk_update(
        updated_schedule_fs, ["aggregate_general_elec_expended"], batch_size=64
    )


def recalculate_aggregation_for_debt_chain(original_debt_ids):
    """
    Handles the batching of aggregation processing to avoid redundant operations
    when multiple transactions reference the same debt chain.

    Args:
        original_debt_ids: An iterable (set, list) of original debt transaction IDs
    """
    for original_debt_id in original_debt_ids:
        try:
            original_debt = Transaction.objects.get(id=original_debt_id)
            process_aggregation_for_debts(original_debt)
        except Transaction.DoesNotExist:
            # Debt may have been deleted in cascade
            pass
