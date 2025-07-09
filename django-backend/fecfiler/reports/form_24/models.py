import uuid
from django.db.models import Model, UUIDField, TextField, DateField
import structlog

logger = structlog.get_logger(__name__)


class Form24(Model):
    """Generated model from json schema"""

    id = UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    report_type_24_48 = TextField(null=True, blank=True)
    original_amendment_date = DateField(null=True, blank=True)
    name = TextField(null=False, blank=False)

    class Meta:
        app_label = "reports"
