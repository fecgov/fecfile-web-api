from django.core.exceptions import ValidationError
from ..models import CommitteeAccount, Membership
from fecfiler.user.utils import get_user_by_email_or_id
from django.db.models import Q
import structlog

logger = structlog.get_logger(__name__)


def add_user_to_committee(user_email, committee_id, role):
    """
    Adds a user to a committee account.
    """
    # Check if the user is already a member of the committee
    matching_memberships = Membership.objects.filter(
        Q(committee_account__committee_id=committee_id)
        & (Q(pending_email__iexact=user_email) | Q(user__email__iexact=user_email))
    )
    if matching_memberships.count() > 0:
        raise ValidationError(
            "User with user_email is already a member of this committee"
        )

    # Get user by email
    user = get_user_by_email_or_id(user_email)

    # Get committee account by ID
    committee_account = CommitteeAccount.objects.filter(committee_id=committee_id).first()
    if not committee_account:
        raise ValidationError("Committee with committee id does not exist")

    membership_args = {
        "committee_account": committee_account,
        "role": role,
        "user": user,
    } | (
        {"pending_email": user_email} if user is None else {}
    )  # Add pending email to args only if there is no user

    new_member = Membership(**membership_args)
    new_member.save()

    return new_member
