import uuid
from django.db import models
import structlog

logger = structlog.get_logger(__name__)


class Form99(models.Model):
    """Generated model from json schema"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    text_code = models.TextField(null=False, blank=False, default="", db_default="")
    filing_frequency = models.TextField(null=True, blank=True, max_length=1)
    message_text = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "reports"
