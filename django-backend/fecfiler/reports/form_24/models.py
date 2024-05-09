import uuid
from django.db import models
import structlog

logger = structlog.get_logger(__name__)


class Form24(models.Model):
    """Generated model from json schema"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    report_type_24_48 = models.TextField(null=True, blank=True)
    original_amendment_date = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "reports"
