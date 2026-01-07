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

from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from typing import Optional
from contextlib import contextmanager
from .models import Transaction
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


@contextmanager
def skip_aggregate_recalc():
    """Context manager to skip aggregate recalculation during cascade ops."""
    old_value = getattr(_thread_locals, 'skip_aggregate_recalc', False)
    _thread_locals.skip_aggregate_recalc = True
    try:
        yield
    finally:
        _thread_locals.skip_aggregate_recalc = old_value


def should_skip_aggregate_recalc():
    """Check if aggregate recalculation should be skipped"""
    return getattr(_thread_locals, 'skip_aggregate_recalc', False)


def _log_transaction_action(instance, action: str) -> None:
    """Log the transaction action."""
    schedule = instance.get_schedule_name()
    txn_id = instance.id
    txn_tid = instance.transaction_id
    transaction.on_commit(
        lambda s=schedule, i=txn_id, t=txn_tid, a=action: logger.info(
            f"{s} Transaction: {i} ({t}) was {a}"
        )
    )


@receiver(post_save, sender=Transaction)
def log_post_save(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    _log_transaction_action(instance, action)


@receiver(post_delete, sender=Transaction)
def log_post_delete(sender, instance, **kwargs):
    _log_transaction_action(instance, "deleted")
