import uuid
from django.db import models
from django.core.validators import RegexValidator
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.user.models import User
from django.core.exceptions import ValidationError
import structlog

logger = structlog.get_logger(__name__)

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


class CommitteeManagementEvent(CommitteeOwnedModel):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    user_uuid = models.UUIDField(editable=False)
    event = models.TextField(editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    def save(self, **kwargs):
        from_db = CommitteeManagementEvent.objects.filter(id=self.id)

        if len(from_db) == 0:
            logger.info(self.event)
            super().save()
        else:
            raise ValueError("Cannot update CommitteeManagementEvent objects")


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

    def redeem(self, user):
        if self.user is not None:
            raise ValueError("Cannot redeem a non-pending membership")
        if user is None:
            raise ValueError("Cannot redeem pending membership with null user")

        event_message = f"Pending membership for {self.pending_email} redeemed by user {user.id}"
        CommitteeManagementEvent.objects.create(
            committee_account=self.committee_account,
            user_uuid=user.id,
            event=event_message,
        )

        self.user = user
        self.pending_email = None
        self.save()


    def delete(self, *args, **kwargs):
        """
        Prevent deletion of a COMMITTEE_ADMINISTRATOR
        if there are 2 or fewer on the account.
        """
        if self.role == self.CommitteeRole.COMMITTEE_ADMINISTRATOR:
            admin_count = Membership.objects.filter(
                committee_account=self.committee_account,
                role=self.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            ).count()

            if admin_count < 3:
                raise ValidationError(
                    "Cannot delete a COMMITTEE_ADMINISTRATOR "
                    "when there are 2 or fewer remaining."
                )

        super().delete(*args, **kwargs)
