"""Logs Transaction events

We use signals to log deletes rather than overwriting delete()
to handle bulk delete cases
https://docs.djangoproject.com/en/dev/topics/db/models/#overriding-predefined-model-methods

We use signals to log saves to be consistent with delete logging
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ScheduleATransaction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ScheduleATransaction)
def action_post_save(sender, instance, created, **kwargs):
    action = "updated"
    if created:
        action = "created"
    elif instance.deleted:
        action = "deleted"

        # If the transaction being deleted is one of several specific memo types,
        # update the contribution_purpose_descrip of the parent if the parent
        # transaction becomes childless
        cpd = None
        partnership_attr_clause = (
            "Partnership attributions do not require itemization"
        )
        if instance.transaction_type_identifier == "PARTNERSHIP_MEMO":
            cpd = partnership_attr_clause
        elif instance.transaction_type_identifier == (
            "PARTNERSHIP_NATIONAL_PARTY_RECOUNT_ACCOUNT_MEMO"
        ):
            cpd = f"Recount/Legal Proceedings Account ({partnership_attr_clause})"
        elif instance.transaction_type_identifier == (
            "PARTNERSHIP_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT_MEMO"
        ):
            cpd = f"Headquarters Buildings Account ({partnership_attr_clause})"
        elif instance.transaction_type_identifier == (
            "PARTNERSHIP_NATIONAL_PARTY_CONVENTION_ACCOUNT_MEMO"
        ):
            cpd = f"Pres. Nominating Convention Account ({partnership_attr_clause})"

        if cpd:
            update_cpb_if_last_child(instance, cpd)

    logger.info(f"Schedule A Transaction: {instance.transaction_id} was {action}")


def update_cpb_if_last_child(instance, new_cbd):
    if (
        ScheduleATransaction.objects.filter(
            parent_transaction_object_id=instance.parent_transaction_object_id
        ).count()
        == 0
    ):
        parent = ScheduleATransaction.objects.get(
            id=instance.parent_transaction_object_id
        )
        parent.contribution_purpose_descrip = new_cbd
        parent.save()


@receiver(post_delete, sender=ScheduleATransaction)
def log_post_delete(sender, instance, **kwargs):
    logger.info(f"Schedule A Transaction: {instance.transaction_id} was deleted")
