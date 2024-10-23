from .models import F3xLine6aOverride
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)


class F3xLine6aOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = F3xLine6aOverride
        fields = [f.name for f in F3xLine6aOverride._meta.get_fields()]
        read_only_fields = [
            "id",
            "created",
            "updated",
        ]
