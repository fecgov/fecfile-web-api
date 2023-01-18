import logging

from fecfiler.transactions.schedule_a.models import ScheduleA
from rest_framework import serializers

logger = logging.getLogger(__name__)


class ScheduleASerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ScheduleA._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ]
        model = ScheduleA
