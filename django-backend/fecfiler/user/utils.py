from fecfiler.user.models import User
from django.db.models import Q


def get_user_by_email_or_id(email_or_id: str) -> User | None:
    return User.objects.filter(
        # __iexact is used for case-insensitive exact matching
		# which helpfully forces string comparison for UUID's
        Q(email__iexact=email_or_id) | Q(id__iexact=email_or_id)
	).first()
