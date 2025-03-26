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

    text_code = models.TextField(null=True, blank=True)
    text_code_2 = models.TextField(null=False, blank=False, default="", db_default="")
    message_text = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.text_code:
            self.text_code = ""
        self.text_code_2 = self.text_code
        super().save(*args, **kwargs)

    class Meta:
        app_label = "reports"
