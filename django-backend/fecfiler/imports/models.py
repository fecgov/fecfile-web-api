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
    parsed_file_name = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "imports"

    def update_status(self, status):
        self.status = status
        self.save(update_fields=["status", "updated"])


class ImportStatus(StrEnum):
    INITIAL = "initial"
    UPLOADED = "uploaded"
    # Parsing statuses
    PARSE_INITIALIZING = "parse_initializing"
    PARSE_STARTING_TASK = "parse_starting_task"
    PARSE_READING_UPLOAD = "parse_reading_upload"
    PARSE_WRITING_PARSED_FILE = "parse_writing_parsed_file"
    PARSE_COMPLETED = "parse_completed"
    PARSE_FAILED = "parse_failed"
    # Importing statuses
    IMPORT_INITIALIZING = "import_initializing"
    IMPORT_STARTING_TASK = "import_starting_task"
    IMPORT_READING_PARSED_FILE = "import_reading_parsed_file"
    IMPORT_SAVING_TO_COMMITTEE = "import_saving_to_committee"
    IMPORT_COMPLETED = "import_completed"
    IMPORT_FAILED = "import_failed"
