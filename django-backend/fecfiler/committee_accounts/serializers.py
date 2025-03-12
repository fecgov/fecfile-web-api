from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from django.contrib.sessions.exceptions import SuspiciousSession
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer, ChoiceField, SerializerMethodField
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
import structlog

logger = structlog.get_logger(__name__)


class CommitteeAccountSerializer(ModelSerializer):
    class Meta:
        model = CommitteeAccount
        fields = "__all__"


class CommitteeOwnedSerializer(ModelSerializer):
    """Serializer for CommitteeOwnedModel
    Inherit this to assign the user's committee as the object's
    owning CommitteeAccount
    """

    committee_account = PrimaryKeyRelatedField(queryset=CommitteeAccount.objects.all())

    def to_internal_value(self, data):
        """Extract committee_id from request to assign the corresponding
        CommitteeAccount as the owner of the object
        """
        data["committee_account"] = self.get_committee_uuid()
        return super().to_internal_value(data)

    def get_committee_uuid(self):
        request = self.context["request"]
        get_committee_uuid = request.session["committee_uuid"]
        if not get_committee_uuid:
            raise SuspiciousSession("session has invalid committee_uuid")
        return get_committee_uuid


class CommitteeMembershipSerializer(CommitteeOwnedSerializer):
    role = ChoiceField(choices=Membership.CommitteeRole)
    name = SerializerMethodField()
    email = SerializerMethodField()

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation.update(
            {
                "id": instance.id,
                "email": self.get_email(instance),
                "username": instance.user.username if instance.user else "",
                "name": self.get_name(instance),
                "is_active": instance.user is not None,
            }
        )

        return representation

    class Meta:
        model = Membership
        fields = [
            f.name
            for f in Membership._meta.get_fields()
            if f.name not in ["deleted", "user", "pending_email"]
        ] + [
            "name",
            "email",
        ]  # This is now valid

        read_only_fields = ["id", "created"]

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, instance):
        return (
            f"{instance.user.last_name}, {instance.user.first_name}"
            if instance.user
            else ""
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_email(self, instance):
        return instance.user.email if instance.user else instance.pending_email
