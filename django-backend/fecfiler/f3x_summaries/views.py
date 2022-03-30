from rest_framework import viewsets
from .models import F3XSummary
from .serializers import F3XSummarySerializer


class F3XSummaryViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    queryset = F3XSummary.objects.all().order_by("-id")
    serializer_class = F3XSummarySerializer
    permission_classes = []
