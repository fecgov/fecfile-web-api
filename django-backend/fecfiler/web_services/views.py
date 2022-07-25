from wsgiref.util import FileWrapper
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.web_services.tasks import create_dot_fec
from .serializers import ReportIdSerializer
from .renderers import DotFECRenderer
from .web_service_storage import get_file
from .models import DotFEC
from fecfiler.settings import CELERY_BROKER_URL

import logging

logger = logging.getLogger(__name__)


class WebServicesViewSet(viewsets.ViewSet):
    """
    A viewset that provides actions to start web service tasks and
    retrieve thier statuses and results
    """

    @action(
        detail=False,
        methods=["post"],
        url_path="dot-fec",
    )
    def create_dot_fec(self, request):
        serializer = ReportIdSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            logger.error(f"Create .FEC: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Create .FEC starting celery task: {CELERY_BROKER_URL}")
        task = create_dot_fec.delay(serializer.validated_data["report_id"], retry=False)

        return Response({"status": ".FEC task created"})

    @action(
        detail=False,
        methods=["get"],
        url_path="dot-fec/(?P<report_id>[a-z0-9]+)",
        renderer_classes=(DotFECRenderer,),
    )
    def get_dot_fec(self, request, report_id):
        committee_id = request.user.cmtee_id
        dot_fec_record = DotFEC.objects.filter(
            report__id=report_id, report__committee_account__committee_id=committee_id
        ).order_by("-file_name")
        if not dot_fec_record.exists():
            logger.error(f"No .FEC was found for report id: {report_id}")
            return Response(
                f"No .FEC was found for report id: {report_id}",
                status=status.HTTP_400_BAD_REQUEST,
            )
        file_name = dot_fec_record.first().file_name
        logger.info(f".FEC was found for report id: {report_id}")
        file = get_file(file_name)
        return Response(FileWrapper(file))
