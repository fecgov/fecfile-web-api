"""Logs Transaction events and triggers aggregate recalculation

We use signals to log deletes rather than overwriting delete()
to handle bulk delete cases
https://docs.djangoproject.com/en/dev/topics/db/models/#overriding-predefined-model-methods

We use signals to log saves to be consistent with delete logging

We also use signals to trigger aggregate recalculation when transactions are
created, updated, or deleted, replacing the previous database trigger approach.

We also trigger itemization calculation after aggregates are set, including
parent/child itemization cascading.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from typing import Optional
from .models import Transaction
from .aggregate_service import recalculate_aggregates_for_transaction
from .managers import (
    schedule_a_over_two_hundred_types,
    schedule_b_over_two_hundred_types,
)
from .constants import ITEMIZATION_THRESHOLD
import structlog
import threading

logger = structlog.get_logger(__name__)

# List of transaction types that use the $200 itemization threshold
A_B_OVER_TWO_HUNDRED_TYPES = (
    schedule_a_over_two_hundred_types + schedule_b_over_two_hundred_types
)

# Thread-local storage for tracking cascade operations
_thread_locals = threading.local()


def is_in_cascade():
    """Check if we're currently in a cascade operation"""
    return getattr(_thread_locals, 'in_cascade', False)


def set_in_cascade(value):
    """Set the cascade operation flag"""
    _thread_locals.in_cascade = value


def _log_transaction_action(instance, created: bool) -> None:
    """Log the transaction action."""
    action = "created" if created else ("deleted" if instance.deleted else "updated")
    schedule = instance.get_schedule_name()
    logger.info(
        f"{schedule} Transaction: {instance.id} "
        f"({instance.transaction_id}) was {action}"
    )


def _should_cascade_unitemization(
    instance, old_aggregate: Optional[Decimal], uses_itemization_threshold: bool
) -> bool:
    """
    Determine if unitemization should cascade to children.

    This happens when:
    1. Aggregate dropped below threshold (from above to below), OR
    2. Aggregate changed to ≤ threshold and has itemized children

    Args:
        instance: Transaction instance
        old_aggregate: Previous aggregate value
        uses_itemization_threshold: Whether this transaction type uses $200 threshold

    Returns:
        Boolean indicating if unitemization should cascade
    """
    from .itemization import has_itemized_children

    if not uses_itemization_threshold or instance.force_itemized is not None:
        return False

    if old_aggregate is None or instance.aggregate is None:
        return False

    # Aggregate dropped below threshold
    aggregate_dropped_below = (
        old_aggregate > ITEMIZATION_THRESHOLD
        and instance.aggregate <= ITEMIZATION_THRESHOLD
    )

    # Aggregate changed while at or below threshold and has itemized children
    aggregate_changed_at_or_below = (
        old_aggregate != instance.aggregate
        and instance.aggregate <= ITEMIZATION_THRESHOLD
        and has_itemized_children(instance)
    )

    return aggregate_dropped_below or aggregate_changed_at_or_below


def _handle_itemization_update(
    instance, created: bool, old_aggregate: Optional[Decimal],
    uses_itemization_threshold: bool
) -> None:
    """
    Handle itemization calculation and cascading.

    Args:
        instance: Transaction instance
        created: Boolean indicating if transaction was just created
        old_aggregate: Previous aggregate value
        uses_itemization_threshold: Whether this transaction type uses $200 threshold
    """
    from .itemization import (
        get_all_children_ids,
        update_itemization,
        cascade_itemization_to_parents,
        cascade_unitemization_to_children,
    )

    # Track if itemization changed
    old_itemized = instance.itemized

    # For newly created transactions, set itemized=False temporarily
    # so that calculate_itemization will properly trigger cascade
    # logic if the transaction should be itemized. (The db_default
    # sets itemized=True initially, but we want to recalculate based
    # on aggregate)
    if created:
        old_itemized = False
        instance.itemized = False

    # Determine if we should cascade unitemization to children
    if _should_cascade_unitemization(instance, old_aggregate, uses_itemization_threshold):
        child_ids = get_all_children_ids(instance.id)
        if child_ids:
            Transaction.objects.filter(
                id__in=child_ids,
                deleted__isnull=True
            ).update(itemized=False)

    # Update itemization based on aggregate
    itemization_changed = update_itemization(instance)

    if itemization_changed:
        instance.save(update_fields=["itemized"])

        # If transaction became itemized, cascade to parents
        if instance.itemized and not old_itemized:
            cascade_itemization_to_parents(instance)
        # If transaction became unitemized, cascade to children
        elif not instance.itemized and old_itemized:
            cascade_unitemization_to_children(instance)


def _update_parent_itemization(instance) -> None:
    """
    Update parent transaction itemization when child changes.

    Args:
        instance: Transaction instance (the child)
    """
    from .itemization import (
        update_itemization,
        cascade_itemization_to_parents,
        cascade_unitemization_to_children,
    )

    parent = instance.parent_transaction
    if not parent:
        return

    parent.refresh_from_db()
    parent_old_itemized = parent.itemized

    # First try standard itemization update based on parent's aggregate
    parent_changed_by_aggregate = update_itemization(parent)

    # If parent is not itemized, check if it should be itemized
    # because child is itemized
    if not parent.itemized and instance.itemized:
        parent.itemized = True
        parent_changed_by_aggregate = True

    if parent_changed_by_aggregate:
        # Clear force_itemized so it doesn't retain stale values
        parent.force_itemized = None
        parent.save(update_fields=["itemized", "force_itemized"])
        parent.refresh_from_db()

        # If parent became itemized, cascade to grandparents
        if parent.itemized and not parent_old_itemized:
            cascade_itemization_to_parents(parent)
        # If parent became unitemized, cascade to children
        elif not parent.itemized and parent_old_itemized:
            cascade_unitemization_to_children(parent)


@receiver(post_save, sender=Transaction)
def log_post_save(sender, instance, created, **kwargs):
    """Handle post-save actions: logging, aggregates, and itemization."""
    _log_transaction_action(instance, created)

    # Save the old aggregate value BEFORE recalculating
    # This allows us to detect if aggregate dropped below threshold
    old_aggregate = instance.aggregate

    # Recalculate aggregates for the transaction
    recalculate_aggregates_for_transaction(instance)

    # Refresh the instance to get the updated aggregate from the database
    instance.refresh_from_db()

    # Skip itemization logic if we're in a cascade operation
    # (to prevent infinite recursion when cascading itemization to children/parents)
    if is_in_cascade():
        return

    uses_itemization_threshold = (
        instance.transaction_type_identifier in A_B_OVER_TWO_HUNDRED_TYPES
    )

    # Handle itemization updates and cascading
    _handle_itemization_update(
        instance, created, old_aggregate, uses_itemization_threshold
    )

    # Always check if parent needs to be updated when a child has a
    # parent_transaction. This handles cases where child's parent
    # relationship affects parent's itemization
    if instance.parent_transaction_id and not is_in_cascade():
        _update_parent_itemization(instance)


@receiver(post_delete, sender=Transaction)
def log_post_delete(sender, instance, **kwargs):
    schedule = instance.get_schedule_name()
    logger.info(
        f"{schedule} Transaction: {instance.id} "
        f"({instance.transaction_id}) was deleted"
    )
