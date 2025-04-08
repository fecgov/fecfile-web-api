from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from fecfiler.user.managers import UserManager
import structlog

logger = structlog.get_logger(__name__)


class User(AbstractUser):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    groups = None
    user_permissions = None
    security_consent_exp_date = models.DateField(null=True, blank=True)

    objects = UserManager()

    def update_username(self, new_username):
        old_username = self.username
        self.username = new_username
        self.save()
        logger.info(f"Updated username: {old_username} -> {new_username}")

        self.redeem_pending_memberships()

    def update_email(self, new_email):
        self.email = new_email
        self.save()
        logger.info(f"Updated email for user {self.id}")

        self.redeem_pending_memberships()

    def redeem_pending_memberships(self):
        from fecfiler.committee_accounts.models import Membership  # no circular import

        pending_memberships = list(
            Membership.objects.filter(user=None, pending_email__iexact=self.email)
        )

        for pending_membership in pending_memberships:
            pending_membership.redeem(self)

        redeemed_count = len(pending_memberships)
        if redeemed_count > 0:
            logger.info(
                f"Redeemed {redeemed_count} pending memberships for user {self.id}"
            )

        return redeemed_count
