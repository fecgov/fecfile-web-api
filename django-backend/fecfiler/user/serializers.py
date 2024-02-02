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
            "login_dot_gov",
        ]
        read_only_fields = [
            "email",
            "login_dot_gov",
        ]
