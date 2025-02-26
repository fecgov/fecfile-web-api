import uuid
from django.db import models
from django.core.validators import RegexValidator
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.user.models import User

COMMITTEE_ID_REGEX = RegexValidator(r"^C[0-9]{8}$", "invalid committee id format")


class CommitteeAccount(SoftDeleteModel):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    committee_id = models.CharField(
        max_length=9, unique=True, validators=[COMMITTEE_ID_REGEX]
    )
    members = models.ManyToManyField(
        User,
        through="Membership",
        through_fields=("committee_account", "user"),
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
        "committee_accounts.CommitteeAccount", on_delete=models.CASCADE, null=True
    )

    class Meta:
        abstract = True


class Membership(CommitteeOwnedModel):
    class CommitteeRole(models.TextChoices):
        COMMITTEE_ADMINISTRATOR = "COMMITTEE_ADMINISTRATOR"
        MANAGER = "MANAGER"

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    user = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)
    pending_email = models.EmailField(null=True, blank=True)
    role = models.CharField(
        max_length=25, choices=CommitteeRole.choices, null=False, blank=False
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
