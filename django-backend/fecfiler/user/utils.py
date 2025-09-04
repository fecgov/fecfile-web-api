from fecfiler.user.models import User
from django.db.models import Q
from django.contrib.sessions.models import Session


def get_user_by_email_or_id(email_or_id: str) -> User | None:
    return User.objects.filter(
        # __iexact is used for case-insensitive exact matching
        # which is necessary for email matching, but also
        # helpfully forces string comparison for UUID's
        Q(email__iexact=email_or_id)
        | Q(id__iexact=email_or_id)
    ).first()


def delete_all_sessions_for_user(user: User) -> None:
    sessions = Session.objects.all()
    for session in sessions:
        data = session.get_decoded()
        if data.get("_auth_user_id") == str(user.id):
            session.delete()
