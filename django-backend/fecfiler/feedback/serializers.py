from rest_framework import serializers
from rest_framework.serializers import CharField
import logging

logger = logging.getLogger(__name__)


class FeedbackSerializer(serializers.Serializer):
    action = CharField(max_length=2000)
    feedback = CharField(max_length=2000)
    about = CharField(max_length=2000)
