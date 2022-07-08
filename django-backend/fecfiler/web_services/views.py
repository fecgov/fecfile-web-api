from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.web_services.tasks import create_dot_fec
from fecfiler.f3x_summaries.models import F3XSummary
from .serializers import ReportIdSerializer


class WebServicesViewSet(viewsets.ViewSet):
    """
    A viewset that provides actions to start web service tasks and
    retrieve thier statuses and results
    """

    @action(
        detail=False,
        methods=["post"],
        url_path="create-dot-fec",
    )
    def create_dot_fec(self, request):
        serializer = ReportIdSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        task = create_dot_fec.delay(serializer.validated_data["report_id"])
        return Response({"status": ".FEC task created"})
