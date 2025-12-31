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
from .models import Transaction
from .aggregate_service import recalculate_aggregates_for_transaction
from .itemization import (
    update_itemization,
    cascade_itemization_to_parents,
    cascade_unitemization_to_children,
)
import structlog
import threading

logger = structlog.get_logger(__name__)

# Thread-local storage for tracking cascade operations
_thread_locals = threading.local()


def is_in_cascade():
    """Check if we're currently in a cascade operation"""
    return getattr(_thread_locals, 'in_cascade', False)


def set_in_cascade(value):
    """Set the cascade operation flag"""
    _thread_locals.in_cascade = value


@receiver(post_save, sender=Transaction)
def log_post_save(sender, instance, created, **kwargs):
    action = "updated"
    if created:
        action = "created"
    elif instance.deleted:
        action = "deleted"
    schedule = instance.get_schedule_name()
    logger.info(
        f"{schedule} Transaction: {instance.id} "
        f"({instance.transaction_id}) was {action}"
    )

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

    # Track if itemization changed
    old_itemized = instance.itemized

    # For newly created transactions, set itemized=False temporarily
    # so that calculate_itemization will properly trigger cascade
    # logic if the transaction should be itemized. (The db_default
    # sets itemized=True initially, but we want to recalculate based
    # on aggregate)
    if created:
        old_itemized = False
        # Reset to False so calculate_itemization changes it to proper value
        instance.itemized = False

    # Calculate what the new itemization should be
    from fecfiler.transactions.managers import (
        schedule_a_over_two_hundred_types,
        schedule_b_over_two_hundred_types,
    )
    a_b_over_two_hundred_types = (
        schedule_a_over_two_hundred_types
        + schedule_b_over_two_hundred_types
    )

    # Check if this is a Schedule A/B type where we need to handle the threshold logic
    schedule = instance.get_schedule_name()
    is_threshold_type = instance.transaction_type_identifier in a_b_over_two_hundred_types

    # Determine if we should cascade unitemization to children
    # This happens when:
    # 1. Aggregate DROPPED below $200 (from above to below), OR
    # 2. Aggregate is ≤ $200 and CHANGED (and was previously > $200
    #    or non-None) and we have itemized children
    from .itemization import get_all_children_ids, has_itemized_children

    should_cascade_unitemization = False

    if is_threshold_type and instance.force_itemized is None:
        # Check if aggregate dropped below threshold (from explicitly above to below)
        if (old_aggregate is not None and old_aggregate > Decimal('200') and
            instance.aggregate is not None and instance.aggregate <= Decimal('200')):
            should_cascade_unitemization = True

        # Check if aggregate is ≤ $200 and CHANGED (but not from None)
        # and we have itemized children
        # This handles when a parent's amount changes after children are added
        elif (old_aggregate is not None and  # Had a previous non-None aggregate
              old_aggregate != instance.aggregate and  # Aggregate actually changed
              instance.aggregate is not None and instance.aggregate <= Decimal('200')):
            has_itemized = has_itemized_children(instance)
            if has_itemized:
                should_cascade_unitemization = True

    if should_cascade_unitemization:
        child_ids = get_all_children_ids(instance.id)
        if child_ids:
            # Update children's itemized to False directly to avoid their signals
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
        if not instance.itemized and old_itemized:
            cascade_unitemization_to_children(instance)

    # Always check if parent needs to be updated when a child has a
    # parent_transaction. This handles cases where child's parent
    # relationship affects parent's itemization
    if instance.parent_transaction_id and not is_in_cascade():
        parent = instance.parent_transaction
        if parent:
            parent.refresh_from_db()
            parent_old_itemized = parent.itemized

            # First try standard itemization update based on parent's aggregate
            parent_changed_by_aggregate = update_itemization(parent)

            # If parent is not itemized, check if it should be itemized because child is itemized
            if not parent.itemized and instance.itemized:
                parent.itemized = True
                parent_changed_by_aggregate = True  # Mark as changed to trigger cascade

            if parent_changed_by_aggregate:
                # Clear force_itemized so it doesn't retain stale values
                # from previous operations
                parent.force_itemized = None
                parent.save(update_fields=["itemized", "force_itemized"])
                parent.refresh_from_db()
                # If parent became itemized, cascade to grandparents
                if parent.itemized and not parent_old_itemized:
                    cascade_itemization_to_parents(parent)
                # If parent became unitemized, cascade to children
                elif not parent.itemized and parent_old_itemized:
                    cascade_unitemization_to_children(parent)


@receiver(post_delete, sender=Transaction)
def log_post_delete(sender, instance, **kwargs):
    schedule = instance.get_schedule_name()
    logger.info(
        f"{schedule} Transaction: {instance.id} "
        f"({instance.transaction_id}) was deleted"
    )
