from .models import User
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "security_consent_exp_date",
        ]
        read_only_fields = [
            "email",
        ]
