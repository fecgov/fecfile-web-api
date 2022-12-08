from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.authentication.authenticate_login import get_logged_in_user
from rest_framework import serializers, relations
import logging

logger = logging.getLogger(__name__)


class CommitteeOwnedSerializer(serializers.ModelSerializer):
    """Serializer for CommitteeOwnedModel
    Inherit this to assign the user's committee as the object's
    owning CommitteeAccount
    """

    committee_account = relations.PrimaryKeyRelatedField(
        queryset=CommitteeAccount.objects.all()
    )

    def to_internal_value(self, data):
        """Extract committee_id from request to assign the corresponding
        CommitteeAccount as the owner of the object
        """
        request = self.context["request"]
        user = get_logged_in_user(request)
        print(
            '\n\n\n',
            'Committee ID:', user.pk, user.cmtee_id,
            '\n\n\n'
        )
        committee_id = user.cmtee_id
        committee = CommitteeAccount.objects.get(committee_id=committee_id)
        data["committee_account"] = committee.id
        return super().to_internal_value(data)
