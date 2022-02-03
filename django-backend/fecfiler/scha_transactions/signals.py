from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SchATransaction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SchATransaction)
def log_post_save(sender, instance, created, **kwargs):
    logger.info('Schedule A Transaction: %s was %s', instance.transaction_id, 'created' if created else 'updated')

@receiver(post_delete, sender=SchATransaction)
def log_post_delete(sender, instance, **kwargs):
    logger.info('Schedule A Transaction: %s was deleted', instance.transaction_id)
