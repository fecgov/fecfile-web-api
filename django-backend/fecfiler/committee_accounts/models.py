import uuid
from django.db import models
from django.core.validators import RegexValidator
from fecfiler.soft_delete.models import SoftDeleteModel

COMMITTEE_ID_REGEX = RegexValidator(r"^C[0-9]{8}$", "invalid committee id format")


class CommitteeAccount(SoftDeleteModel):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    committee_id = models.CharField(
        max_length=9, unique=True, validators=[COMMITTEE_ID_REGEX]
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "committee_accounts"
        app_label = "committee_accounts"

    def __str__(self):
        return self.committee_id


class CommitteeOwnedModel(models.Model):
    """Abstract model for committee ownership

    Inherit this model to add a CommitteeAccount foreign key, attributing
    ownership of the object by a CommitteeAccount
    """

    committee_account = models.ForeignKey(
        "committee_accounts.CommitteeAccount", on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
