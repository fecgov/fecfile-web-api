from .models import MockCommitteeDetail
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)


class MockCommitteeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MockCommitteeDetail
        exclude = []
