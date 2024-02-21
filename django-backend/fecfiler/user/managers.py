import structlog
from django.contrib.auth.models import UserManager as AbstractUserManager

logger = structlog.get_logger(__name__)


class UserManager(AbstractUserManager):
    def create_user(self, user_id, **obj_data):
        from fecfiler.committee_accounts.models import Membership

        new_user = super().create_user(user_id, **obj_data)
        pending_memberships = Membership.objects.filter(
            user=None,
            pending_email=obj_data['email']
        )

        logger.info(f"New User Created: {obj_data['email']} - {pending_memberships.count()} Pending Memberships")

        for new_membership in pending_memberships:
            new_membership.user = new_user
            new_membership.save()

        return new_user