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

from decimal import Decimal
from .managers import (
    schedule_a_over_two_hundred_types,
    schedule_b_over_two_hundred_types,
    Schedule,
)
import structlog

logger = structlog.get_logger(__name__)


def has_itemized_children(transaction):
    """
    Check if a transaction has any itemized children.

    Args:
        transaction: Transaction instance

    Returns:
        Boolean indicating if any children are itemized
    """
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM transactions_transaction
                WHERE parent_transaction_id = %s
                AND deleted IS NULL
                AND itemized = true
            )
        """, [str(transaction.id)])
        result = cursor.fetchone()[0]

    return result


def get_all_children_ids(transaction_id):
    """
    Recursively get all child and grandchild transaction IDs.

    Args:
        transaction_id: UUID of parent transaction

    Returns:
        List of UUIDs of all descendants
    """
    from .models import Transaction

    all_children = []
    direct_children = Transaction.objects.filter(
        parent_transaction_id=transaction_id,
        deleted__isnull=True
    ).values_list('id', flat=True)

    for child_id in direct_children:
        all_children.append(child_id)
        # Recursively get grandchildren
        all_children.extend(get_all_children_ids(child_id))

    return all_children


def get_all_parent_ids(transaction):
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


def calculate_itemization(transaction):
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
            is_itemized = agg_value > Decimal(200)
        else:
            is_itemized = False

        if not is_itemized and has_itemized_children(transaction):
            is_itemized = True

        return is_itemized

    return True


def update_itemization(transaction):
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


def cascade_itemization_to_parents(transaction):
    """
    When a child becomes itemized, ensure all parents are also itemized.

    Args:
        transaction: Transaction instance that was just itemized
    """
    from .models import Transaction

    if not transaction.itemized:
        return

    parent_ids = get_all_parent_ids(transaction)
    if not parent_ids:
        return

    parents = Transaction.objects.filter(
        id__in=parent_ids,
        deleted__isnull=True
    )

    from .signals import set_in_cascade
    set_in_cascade(True)
    try:
        for parent in parents:
            if parent.force_itemized is False:
                continue

            if not parent.itemized:
                parent.itemized = True
                parent.save(update_fields=['itemized'])
                logger.debug(f"Cascaded itemization to parent {parent.id}")
    finally:
        set_in_cascade(False)


def cascade_unitemization_to_children(transaction):
    """
    When a parent becomes unitemized, ensure all children are also unitemized.

    Args:
        transaction: Transaction instance that became unitemized
    """
    from .models import Transaction

    if transaction.itemized:
        return

    child_ids = get_all_children_ids(transaction.id)
    if not child_ids:
        return

    transaction.refresh_from_db()

    children = Transaction.objects.filter(
        id__in=child_ids,
        deleted__isnull=True
    )

    from .signals import set_in_cascade
    set_in_cascade(True)
    try:
        for child in children:
            if child.itemized:
                child.itemized = False
                child.save(update_fields=['itemized'])
                logger.debug(f"Cascaded unitemization to child {child.id}")
    finally:
        set_in_cascade(False)
