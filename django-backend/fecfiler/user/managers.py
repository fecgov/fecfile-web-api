import structlog
from django.contrib.auth.models import UserManager as AbstractUserManager

logger = structlog.get_logger(__name__)


class UserManager(AbstractUserManager):
    def create_user(self, user_id, **obj_data):

        new_user = super().create_user(user_id, **obj_data)

        logger.info(
            f"New User Created: {obj_data['email']}"
        )

        new_user.redeem_pending_memberships()

        return new_user