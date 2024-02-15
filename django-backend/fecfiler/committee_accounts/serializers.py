from fecfiler.committee_accounts.models import CommitteeAccount
from django.contrib.sessions.exceptions import SuspiciousSession
from rest_framework import serializers, relations
import structlog

logger = structlog.get_logger(__name__)


class CommitteeAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommitteeAccount
        fields = "__all__"


class CommitteeMemberSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.CharField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.SerializerMethodField()
    is_active = serializers.BooleanField()

    def get_role(self, object):
        committee_id = self.context.get("committee_id")
        return object.membership_set.get(committee_account_id=committee_id).role


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
        committee = self.get_committee()
        data["committee_account"] = committee.id
        return super().to_internal_value(data)

    def get_committee(self):
        request = self.context["request"]
        committee_uuid = request.session["committee_uuid"]
        committee = (
            CommitteeAccount.objects.get_queryset().filter(id=committee_uuid).first()
        )
        if not committee:
            raise SuspiciousSession("session has invalid committee_uuid")
        return committee
