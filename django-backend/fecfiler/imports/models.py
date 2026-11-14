from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.reports.models import Report
from fecfiler.shared.utilities import generate_fec_uid
from django.db import models
import uuid
from enum import StrEnum
import structlog

logger = structlog.get_logger(__name__)


class Import(CommitteeOwnedModel):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    uploaded_file_name = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "imports"


class ImportStatus(StrEnum):
    INITIAL = "initial"
    UPLOADED = "uploaded"
    PARSING = "parsing"
