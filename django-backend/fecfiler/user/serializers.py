from .models import User
from fecfiler.committee_accounts.models import Membership
from rest_framework.serializers import BooleanField, ModelSerializer
from datetime import date
import structlog

logger = structlog.getLogger(__name__)

session_security_consented_key = "session_security_consented"


class CurrentUserSerializer(ModelSerializer):
    consent_for_one_year = BooleanField(write_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "consent_for_one_year",
        ]
        read_only_fields = ["email", "security_consented"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        data["security_consented"] = (
            request.user.security_consent_exp_date
            and date.today() <= request.user.security_consent_exp_date
        ) or (request.session.get(session_security_consented_key, None) is True)

        # Assign role based on active committee
        committee_uuid = request.session.get("committee_uuid")
        if committee_uuid:
            membership = Membership.objects.filter(
                user=instance, committee_account__id=committee_uuid
            ).first()
            data["role"] = membership.role if membership else None
        else:
            data["role"] = None
        return data
