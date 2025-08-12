from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.reports.models import Report
from fecfiler.shared.utilities import generate_fec_uid
from django.db import models
import uuid
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class ImportStatus(Enum):
    UPLOADING = "Uploading dotFEC"
    PREPROCESSING = "Preprocessing dotFEC"
    AWAITING = "Awaiting user review and approval"
    IMPORTING = "Importing data from dotFEC"
    SUCCESS = "Successfully created data from dotFEC"
    FAILED_UPLOAD = "Failed to upload dotFEC"
    FAILED_PREPROCESS = "Failed to preprocess dotFEC"
    FAILED_CREATION = "Failed to create data from dotFEC"
    CANCELLED = "User canceled the import"


class Imports(SoftDeleteModel, CommitteeOwnedModel,):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    dot_fec_file = models.TextField(null=True, blank=True)
    preprocessed_json = models.JSONField(null=True, blank=True)
    report = models.TextField(null=True, blank=True)
    report_type = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True, default=ImportStatus.UPLOADING)
    coverage_from_date = models.DateField(null=True, blank=True)
    coverage_through_date = models.DateField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def uploader_committee_id_number(self):
        return self.committee_account.committee_id

    class Meta:
        db_table = "imports"
