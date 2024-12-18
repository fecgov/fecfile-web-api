from .models import User
from rest_framework import serializers
from rest_framework.serializers import BooleanField
from datetime import date
import logging

logger = logging.getLogger(__name__)

session_security_consented_key = "session_security_consented"


class CurrentUserSerializer(serializers.ModelSerializer):
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
        return data
