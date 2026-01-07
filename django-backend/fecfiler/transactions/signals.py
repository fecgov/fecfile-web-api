"""Logs Transaction events

We use signals to log deletes rather than overwriting delete()
to handle bulk delete cases
https://docs.djangoproject.com/en/dev/topics/db/models/#overriding-predefined-model-methods

We use signals to log saves to be consistent with delete logging

Note: Aggregate recalculation is now handled explicitly in the
aggregate_service module, not via signals.
"""

from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Transaction
import structlog

logger = structlog.get_logger(__name__)


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
