"""
Itemization calculation for transactions.

Determines whether a transaction should be itemized based on:
1. force_itemized value if set
2. Negative aggregates (always itemized)
3. Schedule A/B transaction type and aggregate threshold ($200)
4. Default to itemized=True for all other cases (including Schedule E)
5. Parent/child relationships: itemized children cause parents to be itemized

Only Schedule A/B over_two_hundred_types have the $200 threshold.
Schedule E transactions are always itemized.
"""

from typing import List
from uuid import UUID
from .managers import (
    schedule_a_over_two_hundred_types,
    schedule_b_over_two_hundred_types,
    Schedule,
    ITEMIZATION_THRESHOLD,
)
import structlog

logger = structlog.get_logger(__name__)


def has_itemized_children(transaction) -> bool:
    """
    Check if a transaction has any itemized children.

    Args:
        transaction: Transaction instance

    Returns:
        Boolean indicating if any children are itemized
    """
    from .models import Transaction

    return Transaction.objects.filter(
        parent_transaction_id=transaction.id,
        deleted__isnull=True,
        itemized=True
    ).exists()


def get_all_children_ids(transaction_id: UUID) -> List[UUID]:
    """
    Recursively get all child and grandchild transaction IDs.

    Args:
        transaction_id: UUID of parent transaction

    Returns:
        List of UUIDs of all descendants
    """
    from .models import Transaction

    all_children = []
    max_depth = 10  # Prevent infinite loops

    def _recurse(parent_id, depth):
        if depth >= max_depth:
            return

        direct_children = Transaction.objects.filter(
            parent_transaction_id=parent_id,
            deleted__isnull=True
        ).values_list('id', flat=True)

        for child_id in direct_children:
            all_children.append(child_id)
            _recurse(child_id, depth + 1)

    _recurse(transaction_id, 0)
    return all_children


def get_all_parent_ids(transaction) -> List[UUID]:
    """
    Get all parent and grandparent transaction IDs up the chain.

    Args:
        transaction: Transaction instance

    Returns:
        List of UUIDs of all ancestors
    """
    all_parents = []
    current = transaction
    max_depth = 10  # Prevent infinite loops
    depth = 0

    while current.parent_transaction_id and depth < max_depth:
        all_parents.append(current.parent_transaction_id)
        current = current.parent_transaction
        if not current:
            break
        depth += 1

    return all_parents


def _cascade_itemization_generic(
    transaction, direction: str, target_value: bool
) -> None:
    """
    Generic cascade function for itemization changes.

    Args:
        transaction: Starting transaction
        direction: 'up' for parents, 'down' for children
        target_value: True for itemized, False for unitemized
    """
    # Only cascade if transaction is in the appropriate state
    if direction == 'up' and not transaction.itemized:
        return
    if direction == 'down' and transaction.itemized:
        return

    # Get related transaction IDs
    related_ids = (
        get_all_parent_ids(transaction) if direction == 'up'
        else get_all_children_ids(transaction.id)
    )

    if not related_ids:
        return

    from .models import Transaction
    related = Transaction.objects.filter(
        id__in=related_ids, deleted__isnull=True
    )

    from .signals import set_in_cascade
    set_in_cascade(True)
    try:
        for related_txn in related:
            # Skip if parent has force_itemized=False when cascading up
            if direction == 'up' and related_txn.force_itemized is False:
                continue

            if related_txn.itemized != target_value:
                related_txn.itemized = target_value
                related_txn.save(update_fields=['itemized'])
                direction_name = 'parent' if direction == 'up' else 'child'
                action = '' if target_value else 'un'
                logger.debug(
                    f"Cascaded {action}itemization to "
                    f"{direction_name} {related_txn.id}"
                )
    finally:
        set_in_cascade(False)


def calculate_itemization(transaction) -> bool:
    """
    Calculate whether a transaction should be itemized.

    Args:
        transaction: Transaction instance w/ aggregate/_calendar_ytd_per_election_office
            and force_itemized set

    Returns:
        Boolean indicating if transaction should be itemized
    """
    if transaction.force_itemized is not None:
        return transaction.force_itemized

    schedule = transaction.get_schedule_name()
    if schedule == Schedule.E:
        agg_value = transaction._calendar_ytd_per_election_office
    else:
        agg_value = transaction.aggregate

    if agg_value is not None and agg_value < 0:
        return True

    a_b_over_two_hundred_types = (
        schedule_a_over_two_hundred_types
        + schedule_b_over_two_hundred_types
    )

    if transaction.transaction_type_identifier in a_b_over_two_hundred_types:
        if agg_value is not None:
            is_itemized = agg_value > ITEMIZATION_THRESHOLD
        else:
            is_itemized = False

        if not is_itemized and has_itemized_children(transaction):
            is_itemized = True

        return is_itemized

    return True


def update_itemization(transaction) -> bool:
    """
    Update the itemized field on a transaction based on calculated value.

    Args:
        transaction: Transaction instance to update

    Returns:
        Boolean indicating if the transaction was updated
    """
    new_itemized = calculate_itemization(transaction)

    if transaction.itemized != new_itemized:
        transaction.itemized = new_itemized
        return True

    return False


def cascade_itemization_to_parents(transaction) -> None:
    """
    When a child becomes itemized, ensure all parents are also itemized.

    Args:
        transaction: Transaction instance that was just itemized
    """
    _cascade_itemization_generic(transaction, 'up', True)


def cascade_unitemization_to_children(transaction) -> None:
    """
    When a parent becomes unitemized, ensure all children are also unitemized.

    Args:
        transaction: Transaction instance that became unitemized
    """
    _cascade_itemization_generic(transaction, 'down', False)
