from .models import User
from rest_framework import serializers
from rest_framework.serializers import BooleanField
import datetime
import logging

logger = logging.getLogger(__name__)


class CurrentUserSerializer(serializers.ModelSerializer):
    consent_for_one_year = BooleanField(write_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
        ]
        read_only_fields = ["email", "security_consented"]
