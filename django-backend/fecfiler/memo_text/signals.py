"""Logs Memo Text events

We use signals to log deletes rather than overwriting delete()
to handle bulk delete cases
https://docs.djangoproject.com/en/dev/topics/db/models/#overriding-predefined-model-methods

We use signals to log saves to be consistent with delete logging
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import MemoText
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MemoText)
def log_post_save(sender, instance, created, **kwargs):
    action = "updated"
    if created:
        action = "created"
    logger.info(f"Memo Text: {instance.id} was {action}")


@receiver(post_delete, sender=MemoText)
def log_post_delete(sender, instance, **kwargs):
    logger.info(f"Memo Text: {instance.id} was deleted")
