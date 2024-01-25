from fecfiler.committee_accounts.models import CommitteeAccount
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
        committee = self.get_committee(data)
        data["committee_account"] = committee.id
        return super().to_internal_value(data)

    def get_committee(self):
        request = self.context["request"]
        return request.user.committee_account_set.first()
