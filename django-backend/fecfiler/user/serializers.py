from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)


class CurrentUserSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField(read_only=True)
    login_dot_gov = serializers.BooleanField(read_only=True)
