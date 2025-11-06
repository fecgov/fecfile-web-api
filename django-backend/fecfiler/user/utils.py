from fecfiler.user.models import User
from django.db.models import Q
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


def get_user_by_email_or_id(email_or_id: str) -> User | None:
    return User.objects.filter(
        # __iexact is used for case-insensitive exact matching
        # which is necessary for email matching, but also
        # helpfully forces string comparison for UUID's
        Q(email__iexact=email_or_id)
        | Q(id__iexact=email_or_id)
    ).first()


def delete_active_sessions_for_user_and_committee(
    user_id: str, committee_id: str
) -> None:
    sessions = Session.objects.filter(expire_date__gt=datetime.now())
    for session in sessions:
        data = session.get_decoded()
        if (
            user_id
            and committee_id
            and data.get("_auth_user_id") == user_id
            and data.get("committee_id") == committee_id
        ):
            session.delete()


def disable_user(uuid, email, enable=False):
    user_model = get_user_model()

    try:
        # if they use both arguments, prefer UUID
        if uuid is not None:
            user = user_model.objects.get(id=uuid)
        else:
            user = user_model.objects.get(email=email)
    except user_model.DoesNotExist:
        logger.error("User does not exist")
        return

    user.is_active = enable
    user.save()

    logger.info(
        f"The is_active flag for user [{user.id} | {user.email}] "
        f"set to: {user.is_active}"
    )
