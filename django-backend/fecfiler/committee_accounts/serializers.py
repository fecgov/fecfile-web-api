from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from django.contrib.sessions.exceptions import SuspiciousSession
from rest_framework import serializers, relations
import structlog

logger = structlog.get_logger(__name__)


class CommitteeAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommitteeAccount
        fields = "__all__"


class CommitteeMembershipSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=Membership.CommitteeRole)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.user is not None:
            representation.update({
                'id': instance.user.id,
                'email': instance.user.email,
                'username': instance.user.username,
                'name': f"{instance.user.last_name}, {instance.user.first_name}",
            })
        else:
            representation.update({
                'id': instance.id,
                'email': instance.pending_email,
                'username': '',
                'name': '',
            })

        representation['is_active'] = instance.user is not None
        return representation

    class Meta:
        model = Membership

        fields = [
            f.name
            for f in Membership._meta.get_fields()
            if f.name
            not in [
                "deleted",
                "user",
                "pending_email"
            ]
        ] + ["name", "email"]
        read_only_fields = [
            "id",
            "created",
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
