import math
from datetime import datetime
from wsgiref.util import FileWrapper
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .tasks import (
    create_dot_fec,
    submit_to_fec,
    submit_to_webprint,
    compose_dot_fec,
    store_file,
    DotFEC,
    get_file_bytes,
    WEB_PRINT_KEY,
    MOCK_WEB_PRINT_KEY,
    SUBMISSION_MANAGERS,
    SUBMISSION_CLASSES,
    FECStatus,
    calculate_polling_interval,
    resolve_final_submission_state,
    MAX_ATTEMPTS,
    logger,
)
from .summary.tasks import CalculationState, calculate_summary
from fecfiler.settings import MOCK_EFO_FILING
from .serializers import ReportIdSerializer, SubmissionRequestSerializer
from .renderers import DotFECRenderer
from .web_service_storage import get_file
from .models import DotFEC, UploadSubmission, WebPrintSubmission, FECSubmissionState
from fecfiler.reports.models import Report, FORMS_TO_CALCULATE
from drf_spectacular.utils import extend_schema
from celery.result import AsyncResult
import structlog

import time
from silk.profiling.profiler import silk_profile

logger = structlog.get_logger(__name__)


class WebServicesViewSet(viewsets.ViewSet):
    """
    A viewset that provides actions to start web service tasks and
    retrieve thier statuses and results
    """

    """Return the appropriate serializer class for the action."""

    def get_serializer_class(self):
        if self.action == "create_dot_fec":
            return ReportIdSerializer
        elif self.action == "submit_to_fec":
            return SubmissionRequestSerializer
        elif self.action == "submit_to_webprint":
            return ReportIdSerializer

    @action(
        detail=False,
        methods=["post"],
        url_path="dot-fec",
    )
    def create_dot_fec(self, request):
        """Create a .FEC file and store it
        Currently only useful for testing purposes
        """
        serializer = self.get_serializer_class()(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        report_id = serializer.validated_data["report_id"]
        logger.debug(f"Starting Celery Task create_dot_fec for report :{report_id}")

        file_name = f"{report_id}_{math.floor(datetime.now().timestamp())}.fec"
        task = self.get_calculation_task(request, report_id)
        if task:
            task = (task | create_dot_fec.s(None, None, False, file_name)).apply_async()
        else:
            task = create_dot_fec.apply_async(
                (report_id, None, None, False, file_name), retry=False
            )
        logger.debug(f"Status from create_dot_fec report {report_id}: {task.status}")
        return Response({"file_name": file_name, "task_id": task.task_id})

    @extend_schema(exclude=True)
    @action(
        detail=False,
        methods=["get"],
        url_path="dot-fec/check/(?P<task_id>[a-z0-9-]+)",
    )
    def check_dot_fec(self, request, task_id):
        res = AsyncResult(task_id)
        if res.ready():
            return Response({"done": True, "id": res.get()})
        return Response({"done": False})

    @extend_schema(exclude=True)
    @action(
        detail=False,
        methods=["get"],
        url_path="dot-fec/(?P<id>[a-z0-9-]+)",
        renderer_classes=(DotFECRenderer,),
    )
    def get_dot_fec(self, request, id):
        """Download the most recent .FEC created for a report
        Currently only useful for testing purposes
        """
        committee_uuid = request.session["committee_uuid"]
        dot_fec_record = DotFEC.objects.filter(
            id=id, report__committee_account_id=committee_uuid
        )
        if not dot_fec_record.exists():
            not_found_msg = f"No .FEC was found for id: {id}"
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
        serializer = self.get_serializer_class()(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        """Retrieve parameters"""
        mock = request.query_params.get("mock", "false").lower() == "true"
        mock_reject = request.query_params.get("mock_reject", "false").lower() == "true"
        if MOCK_EFO_FILING:
            """If the server is set to mock, all submissions will be mocked"""
            mock = True
        report = serializer.validated_data["report_instance"]
        report_id = serializer.validated_data["report_id"]

        if (
            report.upload_submission
            and report.upload_submission.fecfile_task_state
            not in [FECSubmissionState.SUCCEEDED, FECSubmissionState.FAILED]
        ):
            logger.debug(f"""There is already an active upload being generated for report
                {report_id}: {report.upload_submission.fecfile_task_state}""")
            return Response(
                {"status": f"""There is already an active upload
                     being generated for report {report_id}"""},
                status=status.HTTP_400_BAD_REQUEST,
            )

        e_filing_password = serializer.validated_data["password"]
        backdoor_code = serializer.validated_data.get("backdoor_code", None)

        """Start tracking submission"""
        submission_id = UploadSubmission.objects.initiate_submission(report_id).id

        """Start Celery tasks in chain
        Check to see if calculating the summary is necessary. If not, just start
        then chain with create_dot_fec
        """
        task = self.get_calculation_task(request, report_id)
        if task:
            task = task | create_dot_fec.s(upload_submission_id=submission_id)
        else:
            task = create_dot_fec.s(report_id, upload_submission_id=submission_id)

        task = (
            task
            | submit_to_fec.si(
                submission_id, e_filing_password, False, backdoor_code, mock, mock_reject
            )
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
        serializer = self.get_serializer_class()(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        """Retrieve parameters"""
        mock = request.query_params.get("mock", "false").lower() == "true"
        if MOCK_EFO_FILING:
            """If the server is set to mock, all submissions will be mocked"""
            mock = True
        report_id = serializer.validated_data["report_id"]

        """Check if there's an already running submission"""
        report = serializer.validated_data["report_instance"]
        if (
            report.webprint_submission
            and report.webprint_submission.fecfile_task_state
            not in [FECSubmissionState.SUCCEEDED, FECSubmissionState.FAILED]
        ):
            logger.debug(
                f"""There is already an active webprint being generated for report
                {report_id}: {report.webprint_submission.fecfile_task_state}"""
            )
            return Response(
                {"status": f"""There is already an active webprint being generated
                    for report {report_id}"""},
                status=status.HTTP_400_BAD_REQUEST,
            )

        """Start tracking submission"""
        submission = WebPrintSubmission.objects.initiate_submission(report)
        submission_id = submission.id

        """Start Celery tasks in chain
        Notice that we don't send the upload submission id to `create_dot_fec`
        We don't want the .FEC to be signed for WebPrint

        Check to see if calculating the summary is necessary. If not, just start
        then chain with create_dot_fec
        """
        task = self.get_calculation_task(request, report_id)
        if task:
            task = task | create_dot_fec.s(webprint_submission_id=submission_id)
        else:
            task = create_dot_fec.s(report_id, webprint_submission_id=submission_id)

        task = (task | submit_to_webprint.si(submission_id, False, mock)).apply_async(
            retry=False
        )

        logger.debug(f"submit_to_webprint report {report_id}: {task.status}")
        return Response({"status": "Submit .FEC task created"})

    def get_calculation_task(self, request, report_id):
        committee_uuid = request.session["committee_uuid"]
        report = Report.objects.filter(
            id=report_id, committee_account_id=committee_uuid
        ).first()
        if (
            report.get_form_name() in FORMS_TO_CALCULATE
            and report.calculation_status != CalculationState.SUCCEEDED.value
        ):
            return calculate_summary.s(report_id)
        return None

    # @action(
    #     detail=False,
    #     methods=["post"],
    #     url_path="submit-to-webprint",
    # )
    # def submit_to_webprint(self, request):
    #     """
    #     A purely synchronous copy of the submission pipeline.
    #     Runs completely within the HTTP request lifecycle so Silk captures it easily.
    #     """
    #     serializer = self.get_serializer_class()(
    #         data=request.data, context={"request": request}
    #     )
    #     if not serializer.is_valid():
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    #     mock = request.query_params.get("mock", "false").lower() == "true"
    #     if MOCK_EFO_FILING:
    #         mock = True

    #     report_id = serializer.validated_data["report_id"]
    #     report = serializer.validated_data["report_instance"]

    #     # 1. Initialize submission state record
    #     submission = WebPrintSubmission.objects.initiate_submission(report)
    #     submission_id = submission.id

    #     # Add a global silk profile tag for the whole view execution script
    #     with silk_profile(name="Webprint create_dot_fec"):

    #         # ==========================================
    #         # STEP A: Inline Version of create_dot_fec
    #         # ==========================================
    #         submission.save_state(FECSubmissionState.CREATING_FILE)
    #         try:
    #             file_content = compose_dot_fec(report_id)
    #             file_name = f"{report_id}_{math.floor(datetime.now().timestamp())}.fec"

    #             if not file_content:
    #                 raise Exception("No file created")

    #             store_file(file_content, file_name, False)
    #             dot_fec_record = DotFEC(report_id=report_id, file_name=file_name)
    #             dot_fec_record.save()

    #             WebPrintSubmission.objects.filter(id=submission_id).update(
    #                 dot_fec=dot_fec_record
    #             )
    #         except Exception as e:
    #             submission.save_error("Creating .FEC failed")
    #             return Response({"error": f"Failed dot_fec step: {str(e)}"}, status=500)

    #     with silk_profile(name="Webprint submit_to_webprint"):
    #         # ==========================================
    #         # STEP B: Inline Version of submit_to_webprint
    #         # ==========================================
    #         # Fresh fetch with your optimizations included to capture query metrics
    #         submission = WebPrintSubmission.objects.select_related(
    #             "dot_fec__report__committee_account"
    #         ).get(id=submission_id)
    #         submission.save_state(FECSubmissionState.SUBMITTING)

    #         dot_fec_record = submission.dot_fec
    #         file_name = dot_fec_record.file_name
    #         try:
    #             dot_fec_bytes = get_file_bytes(file_name, False)
    #         except Exception:
    #             submission.save_error("Could not retrieve .FEC bytes")
    #             return Response({"error": "Failed retrieving bytes"}, status=500)

    #         submission_type_key = WEB_PRINT_KEY if not mock else MOCK_WEB_PRINT_KEY
    #         submitter = SUBMISSION_MANAGERS[submission_type_key]()

    #         try:
    #             submission_response_string = submitter.submit(None, dot_fec_bytes)
    #             submission.save_fec_response(submission_response_string)
    #         except Exception as e:
    #             submission.save_error("Failed submitting to WebPrint")
    #             resolve_final_submission_state(submission)
    #             return Response({"error": f"Submission error: {str(e)}"}, status=500)

    #     with silk_profile(name="Webprint polling"):
    #         # ==========================================
    #         # STEP C: Synchronous polling loop replacement
    #         # ==========================================
    #         while submission.fec_status not in FECStatus.get_terminal_statuses_strings():
    #             if submission.fecfile_polling_attempts >= MAX_ATTEMPTS:
    #                 logger.warning("POLLING ATTEMPTS EXCEEDED")
    #                 submission.fecfile_task_state = FECSubmissionState.FAILED.value
    #                 resolve_final_submission_state(submission)
    #                 break

    #             # Simulate the countdown sleep interval cleanly
    #             countdown = calculate_polling_interval(
    #                 submission.fecfile_polling_attempts
    #             )
    #             logger.info(f"Sync Polling: Sleeping for {countdown} seconds...")
    #             time.sleep(countdown)  # Keeps execution inside this single HTTP thread

    #             # Re-fetch utilizing your optimization parameters
    #             submission = (
    #                 SUBMISSION_CLASSES[submission_type_key]
    #                 .objects.only(
    #                     "id",
    #                     "fecfile_polling_attempts",
    #                     "fec_submission_id",
    #                     "fec_status",
    #                     "fec_message",
    #                     "fecfile_task_state",
    #                 )
    #                 .get(id=submission_id)
    #             )
    #             submission.save_state(FECSubmissionState.POLLING)
    #             submission.fecfile_polling_attempts += 1

    #             try:
    #                 status_response_string = submitter.poll_status(submission)
    #                 submission.save_fec_response(status_response_string)
    #             except Exception as e:
    #                 submission.save_error(f"Failed submitting during polling context")
    #                 resolve_final_submission_state(submission)
    #                 return Response({"error": f"Polling breakdown: {str(e)}"}, status=500)

    #         # Handle final state resolution
    #         final_id = resolve_final_submission_state(submission)

    #     return Response(
    #         {
    #             "status": "Synchronous submission testing pipeline completed successfully!",
    #             "submission_id": final_id,
    #         }
    #     )
