"""Logs Contact events

We use signals to log deletes rather than overwriting delete()
to handle bulk delete cases
https://docs.djangoproject.com/en/dev/topics/db/models/#overriding-predefined-model-methods

We use signals to log saves to be consistent with delete logging
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Contact
import structlog

logger = structlog.get_logger(__name__)


@receiver(post_save, sender=Contact)
def log_post_save(sender, instance, created, **kwargs):
    action = "updated"
    if created:
        action = "created"
    elif instance.deleted:
        action = "deleted"
    logger.info(
        f"Contact {action}",
        contact_id=instance.id
    )


@receiver(post_delete, sender=Contact)
def log_post_delete(sender, instance, **kwargs):
    logger.info("Contact deleted", contact_id=instance.id)
