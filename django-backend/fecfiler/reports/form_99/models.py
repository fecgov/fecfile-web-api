import uuid
from django.db import models
import logging


logger = logging.getLogger(__name__)


class Form99(models.Model):
    """Generated model from json schema"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    street_1 = models.TextField(null=True, blank=True)
    street_2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    zip = models.TextField(null=True, blank=True)
    text_code = models.TextField(null=True, blank=True)

    text = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "reports"
