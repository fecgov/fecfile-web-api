from rest_framework import serializers
from rest_framework.serializers import CharField
import structlog

logger = structlog.getLogger(__name__)


class FeedbackSerializer(serializers.Serializer):
    action = CharField(max_length=2000)
    feedback = CharField(max_length=2000, allow_null=True)
    about = CharField(max_length=2000, allow_null=True)
    location = CharField(max_length=2000)
