from wsgiref.util import FileWrapper
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.web_services.tasks import (
    create_dot_fec,
    submit_to_fec,
    submit_to_webprint,
)
from fecfiler.settings import FEC_FILING_API
from .serializers import ReportIdSerializer, SubmissionRequestSerializer
from .renderers import DotFECRenderer
from .web_service_storage import get_file
from .models import DotFEC, UploadSubmission, WebPrintSubmission

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
        """Create a .FEC file and store it
        Currently only useful for testing purposes
        """
        serializer = ReportIdSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        report_id = serializer.validated_data["report_id"]
        logger.debug(f"Starting Celery Task create_dot_fec for report :{report_id}")
        task = create_dot_fec.apply_async((report_id, None, None), retry=False)
        logger.debug(f"Status from create_dot_fec report {report_id}: {task.status}")
        return Response({"status": ".FEC task created"})

    @action(
        detail=False,
        methods=["get"],
        url_path="dot-fec/(?P<report_id>[a-z0-9]+)",
        renderer_classes=(DotFECRenderer,),
    )
    def get_dot_fec(self, request, report_id):
        """Download the most recent .FEC created for a report
        Currently only useful for testing purposes
        """
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
        """Create a signed .FEC, store it, and submit it to FEC Webload"""
        serializer = SubmissionRequestSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        """Retrieve parameters"""
        report_id = serializer.validated_data["report_id"]
        e_filing_password = serializer.validated_data["password"]

        """Start tracking submission"""
        upload_submission = UploadSubmission.objects.initiate_submission(report_id)

        """Start Celery tasks in chain"""
        task = (
            create_dot_fec.s(report_id, upload_submission_id=upload_submission.id)
            | submit_to_fec.s(upload_submission.id, e_filing_password, FEC_FILING_API)
        ).apply_async(retry=False)

        logger.debug(f"submit_to_fec report {report_id}: {task.status}")
        return Response({"status": "Submit .FEC task created"})

    @action(
        detail=False,
        methods=["post"],
        url_path="submit-to-webprint",
    )
    def submit_to_webprint(self, request):
        """Create an unsigned .FEC, store it, and submit it to FEC WebPrint"""
        serializer = ReportIdSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        """Retrieve parameters"""
        report_id = serializer.validated_data["report_id"]

        """Start tracking submission"""
        webprint_submission = WebPrintSubmission.objects.initiate_submission(report_id)

        """Start Celery tasks in chain
        Notice that we don't send the submission id to `create_dot_fec`
        We don't want the .FEC to be signed for WebPrint
        """
        task = (
            create_dot_fec.s(report_id, webprint_submission_id=webprint_submission.id)
            | submit_to_webprint.s(webprint_submission.id, FEC_FILING_API)
        ).apply_async(retry=False)

        logger.debug(f"submit_to_webprint report {report_id}: {task.status}")
        return Response({"status": "Submit .FEC task created"})
