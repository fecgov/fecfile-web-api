from wsgiref.util import FileWrapper
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.web_services.tasks import create_dot_fec, submit_to_fec
from .serializers import ReportIdSerializer, SubmissionSerializer
from .renderers import DotFECRenderer
from .web_service_storage import get_file
from .models import DotFEC, UploadSubmission

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
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        report_id = serializer.validated_data["report_id"]
        logger.debug(f"Starting Celery Task create_dot_fec for report :{report_id}")
        task = create_dot_fec.apply_async((report_id, False), retry=False)
        logger.debug(f"Status from create_dot_fec report {report_id}: {task.status}")
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
            not_found_msg = f"No .FEC was found for report id: {report_id}"
            logger.error(not_found_msg)
            return Response(not_found_msg, status=status.HTTP_400_BAD_REQUEST)
        file_name = dot_fec_record.first().file_name
        file = get_file(file_name)
        logger.debug(f"Retrieved .FEC: {file_name}")
        return Response(FileWrapper(file))

    @action(
        detail=False,
        methods=["post"],
        url_path="submit-to-fec",
    )
    def submit_to_fec(self, request):
        serializer = SubmissionSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        report_id = serializer.validated_data["report_id"]
        e_filing_password = serializer.validated_data["e_filing_password"]
        upload_submission_record = UploadSubmission(
            report_id=report_id, fecfile_task_state="CREATING_FILE"
        ).save()
        logger.debug(
            f"Starting Celery Task submit_to_fec for report :{report_id} {upload_submission_record.id}"
        )
        task = (
            create_dot_fec.s(report_id, False)
            | submit_to_fec.s(upload_submission_record.id, e_filing_password)
        ).apply_async(retry=False)
        logger.debug(f"Status from submit_to_fec report {report_id}: {task.status}")
        return Response({"status": "Submit .FEC task created"})
