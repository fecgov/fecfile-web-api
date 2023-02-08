"""Logs Mock Open Fec events

We use signals to log deletes rather than overwriting delete()
to handle bulk delete cases
https://docs.djangoproject.com/en/dev/topics/db/models/#overriding-predefined-model-methods

We use signals to log saves to be consistent with delete logging
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import MockCommitteeDetail
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MockCommitteeDetail)
def log_post_save(sender, instance, created, **kwargs):
    action = "updated"
    if created:
        action = "created"
    logger.info(f"Mock Committee Detail: {instance.id} was {action}")


@receiver(post_delete, sender=MockCommitteeDetail)
def log_post_delete(sender, instance, **kwargs):
    logger.info(f"Mock Committee Detail: {instance.id} was deleted")
