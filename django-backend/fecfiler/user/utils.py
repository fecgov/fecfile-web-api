from fecfiler.user.models import User


def get_user_by_email_or_id(email_or_id: str) -> User | None:
	if "@" in email_or_id:
		return User.objects.filter(email__iexact=email_or_id).first()
	elif len(email_or_id) == 36 and email_or_id.count("-") == 4:
		return User.objects.filter(id=email_or_id).first()
	return None