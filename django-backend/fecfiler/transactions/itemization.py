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

from enum import Enum
from typing import List
from uuid import UUID
from .managers import (
    schedule_a_over_two_hundred_types,
    schedule_b_over_two_hundred_types,
    Schedule,
)
from .constants import ITEMIZATION_THRESHOLD
import structlog

logger = structlog.get_logger(__name__)

# List of transaction types that use the $200 itemization threshold
A_B_OVER_TWO_HUNDRED_TYPES = (
    schedule_a_over_two_hundred_types + schedule_b_over_two_hundred_types
)


class CascadeDirection(Enum):
    """Direction for cascading itemization changes."""
    TO_PARENTS = 'up'
    TO_CHILDREN = 'down'


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
    Get all child and grandchild transaction IDs using recursive CTE.

    Uses a single SQL recursive query instead of O(depth) Python queries.

    Args:
        transaction_id: UUID of parent transaction

    Returns:
        List of UUIDs of all descendants
    """
    from django.db import connection

    # Use recursive CTE for efficient tree traversal
    query = """
    WITH RECURSIVE descendants AS (
        SELECT id FROM transactions_transaction
        WHERE parent_transaction_id = %s AND deleted IS NULL

        UNION ALL

        SELECT t.id FROM transactions_transaction t
        INNER JOIN descendants d ON t.parent_transaction_id = d.id
        WHERE t.deleted IS NULL
    )
    SELECT id FROM descendants;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [transaction_id])
        return [row[0] for row in cursor.fetchall()]


def get_all_parent_ids(transaction) -> List[UUID]:
    """
    Get all parent and grandparent transaction IDs using recursive CTE.

    Uses a single SQL recursive query for efficient tree traversal.

    Args:
        transaction: Transaction instance

    Returns:
        List of UUIDs of all ancestors
    """
    from django.db import connection

    if not transaction.parent_transaction_id:
        return []

    # Use recursive query for more efficient tree traversal up the parent chain
    query = """
    WITH RECURSIVE ancestors AS (
        SELECT id, parent_transaction_id FROM transactions_transaction
        WHERE id = %s AND deleted IS NULL

        UNION ALL

        SELECT t.id, t.parent_transaction_id
        FROM transactions_transaction t
        INNER JOIN ancestors a ON t.id = a.parent_transaction_id
        WHERE t.deleted IS NULL
    )
    SELECT id FROM ancestors WHERE id != %s;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [transaction.parent_transaction_id, transaction.id])
        return [row[0] for row in cursor.fetchall()]


def _cascade_itemization_generic(
    transaction,
    direction: CascadeDirection,
    should_be_itemized: bool
) -> None:
    """
    Generic cascade function for itemization changes.

    Args:
        transaction: Starting transaction
        direction: CascadeDirection.TO_PARENTS or CascadeDirection.TO_CHILDREN
        should_be_itemized: True for itemized, False for unitemized
    """
    # Only cascade if transaction is in the appropriate state
    if direction == CascadeDirection.TO_PARENTS and not transaction.itemized:
        return
    if direction == CascadeDirection.TO_CHILDREN and transaction.itemized:
        return

    # Get related transaction IDs
    related_ids = (
        get_all_parent_ids(transaction) if direction == CascadeDirection.TO_PARENTS
        else get_all_children_ids(transaction.id)
    )

    if not related_ids:
        return

    from .models import Transaction

    # Build query for transactions that need updating
    base_query = Transaction.objects.filter(
        id__in=related_ids,
        deleted__isnull=True
    )

    # For cascading to parents, exclude those with force_itemized=False
    if direction == CascadeDirection.TO_PARENTS:
        base_query = base_query.exclude(force_itemized=False)

    # Only include transactions that need updating (different from target state)
    query_to_update = base_query.filter(itemized=not should_be_itemized)

    # Perform bulk update
    query_to_update.update(itemized=should_be_itemized)


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

    if transaction.transaction_type_identifier in A_B_OVER_TWO_HUNDRED_TYPES:
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
    _cascade_itemization_generic(transaction, CascadeDirection.TO_PARENTS, True)


def cascade_unitemization_to_children(transaction) -> None:
    """
    When a parent becomes unitemized, ensure all children are also unitemized.

    Args:
        transaction: Transaction instance that became unitemized
    """
    _cascade_itemization_generic(transaction, CascadeDirection.TO_CHILDREN, False)
