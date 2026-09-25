from django.core.validators import RegexValidator
from django.db import models
from fecfiler.committee_accounts.models import CommitteeOwnedModel
import uuid
import structlog

logger = structlog.get_logger(__name__)


class ElectionCycle(
    CommitteeOwnedModel,
):
    class Office(models.TextChoices):
        HOUSE = "House", "House"
        PRESIDENTIAL = "Presidential", "Presidential"
        SENATE = "Senate", "Senate"

    class ElectionType(models.TextChoices):
        GENERAL = "General", "General"
        SPECIAL = "Special", "Special"

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    office = models.CharField(
        max_length=20,
        choices=Office.choices,
    )
    election_type = models.CharField(
        max_length=20,
        choices=ElectionType.choices,
    )
    election_year = models.CharField(
        max_length=4,
        validators=[
            RegexValidator(
                regex=r"^\d{4}$",
                message="Election year must be a 4-digit year (YYYY).",
            )
        ],
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.election_year} {self.office} ({self.election_type})"

    class Meta:
        db_table = "election_cycles"
        ordering = ["-election_year", "-start_date"]
