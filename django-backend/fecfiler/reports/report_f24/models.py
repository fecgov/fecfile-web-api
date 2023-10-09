import uuid
from django.db import models
import logging


logger = logging.getLogger(__name__)


class ReportF24(models.Model):
    """Generated model from json schema"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    # filer_committee_id_number = models.TextField(null=True, blank=True) -- can be calculated JIT
    report_type_24_48 = models.TextField(null=True, blank=True)
    original_amendment_date = models.DateField(null=True, blank=True)
    # committee_name = models.TextField(null=True, blank=True) -- can be calculated JIT
    street_1 = models.TextField(null=True, blank=True)
    street_2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    zip = models.TextField(null=True, blank=True)
    treasurer_last_name = models.TextField(null=True, blank=True)
    treasurer_first_name = models.TextField(null=True, blank=True)
    treasurer_middle_name = models.TextField(null=True, blank=True)
    treasurer_prefix = models.TextField(null=True, blank=True)
    treasurer_suffix = models.TextField(null=True, blank=True)
    date_signed = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "reports"
        db_table = "reports_f24"
