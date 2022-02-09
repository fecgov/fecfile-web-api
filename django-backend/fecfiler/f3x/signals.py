"""Logs Schedule A Transaction events

We use signals to log deletes rather than overwriting delete()
to handle bulk delete cases
https://docs.djangoproject.com/en/dev/topics/db/models/#overriding-predefined-model-methods

We use signals to log saves to be consistent with delete logging
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import F3X
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=F3X)
def log_post_save(sender, instance, created, **kwargs):
    action = 'created' if created else 'updated'
    logger.info('F3X: %s was %s',
                instance.committee_name, action)


@receiver(post_delete, sender=F3X)
def log_post_delete(sender, instance, **kwargs):
    logger.info('F3X: %s was deleted',
                instance.committee_name)
