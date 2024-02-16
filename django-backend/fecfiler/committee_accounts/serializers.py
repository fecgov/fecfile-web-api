from fecfiler.committee_accounts.models import CommitteeAccount, Membership
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


class CommitteeMembershipSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    role = serializers.CharField()
    is_active = serializers.SerializerMethodField()

    def get_id(self, object):
        if object.user is not None:
            return object.user.id
        return object.id

    def get_email(self, object):
        if object.user is not None:
            return object.user.email
        return object.pending_email

    def get_username(self, object):
        if object.user is not None:
            return object.user.username
        return ''

    def get_name(self, object):
        if object.user is not None:
            return f"{object.user.last_name}, {object.user.first_name}"
        return ''

    def get_is_active(self, object):
        return object.user is not None

    class Meta:
        model = Membership

        def get_fields():
            return [
                f.name
                for f in Membership._meta.get_fields()
                if f.name
                not in [
                    "deleted",
                    "user",
                    "pending_email"
                ]
            ]


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
