from rest_framework import viewsets
from .serializers import F3xLine6aOverrideSerializer
from .models import F3xLine6aOverride
import logging

logger = logging.getLogger(__name__)


class F3xLine6aOverrideViewSet(viewsets.ModelViewSet):
    serializer_class = F3xLine6aOverrideSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = F3xLine6aOverride.objects.all()
        year = self.request.query_params.get("year")
        if year is not None:
            queryset = queryset.filter(year=year)
        return queryset
