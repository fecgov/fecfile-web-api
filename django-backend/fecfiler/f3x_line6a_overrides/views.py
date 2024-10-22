from rest_framework import viewsets
from .serializers import F3xLine6aOverrideSerializer
from .models import F3xLine6aOverride
import logging

logger = logging.getLogger(__name__)


class F3xLine6aOverrideViewSet(viewsets.ModelViewSet):
    queryset = F3xLine6aOverride.objects.all()
    serializer_class = F3xLine6aOverrideSerializer
