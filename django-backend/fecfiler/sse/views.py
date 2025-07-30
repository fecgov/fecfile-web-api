from django.http import StreamingHttpResponse
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from rest_framework.renderers import BaseRenderer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from fecfiler.settings import SYSTEM_STATUS_CACHE_BACKEND
from fecfiler.reports.models import Report
from fecfiler.web_services.models import WebPrintSubmission, FECStatus
from fecfiler.web_services.summary.tasks import CalculationState
import redis

if SYSTEM_STATUS_CACHE_BACKEND:
    redis_instance = redis.Redis.from_url(SYSTEM_STATUS_CACHE_BACKEND)
else:
    raise SystemError("SYSTEM_STATUS_CACHE_BACKEND is not set")


class SSEStreamingRenderer(BaseRenderer):
    media_type = "text/event-stream"
    format = "txt"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class SSEViewSet(viewsets.ViewSet):
    renderer_classes = [SSEStreamingRenderer]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    @action(detail=True, methods=["get"], url_path="calculation-status")
    def calculation_status(self, request, pk=None):
        if not redis_instance:
            return StreamingHttpResponse(
                "data: ERROR: Redis connection not available\n\n",
                content_type="text/event-stream",
                status=503,
            )

        report_id = str(pk)
        try:
            report = Report.objects.get(id=report_id)
            if str(report.calculation_status) != str(CalculationState.CALCULATING):

                def immediate_stream():
                    yield f"data: {report.calculation_status}\n\n"

                return StreamingHttpResponse(
                    immediate_stream(), content_type="text/event-stream"
                )
        except Report.DoesNotExist:
            return StreamingHttpResponse(
                "data: ERROR: Report not found\n\n",
                content_type="text/event-stream",
                status=404,
            )

        def event_stream():
            pubsub = None
            try:
                pubsub = redis_instance.pubsub(ignore_subscribe_messages=True)
                channel_name = f"calculation_status:{report_id}"
                pubsub.subscribe(channel_name)

                yield "data: LISTENING\n\n"

                while True:
                    message = pubsub.get_message(timeout=20.0)

                    if message is None:
                        yield ": keep-alive\n\n"
                        continue

                    if message.get("type") == "message":
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        yield f"data: {data}\n\n"
                        break

            except GeneratorExit:
                pass
            finally:
                if pubsub:
                    pubsub.unsubscribe()
                    pubsub.close()

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    @method_decorator(csrf_exempt)
    @action(detail=True, methods=["get"], url_path="webprint-status")
    def webprint_status(self, request, pk=None):
        if not redis_instance:
            return StreamingHttpResponse(
                "data: ERROR: Redis connection not available\n\n",
                content_type="text/event-stream",
                status=503,
            )

        submission_id = str(pk)

        try:
            submission = WebPrintSubmission.objects.get(id=submission_id)
            if submission.fec_status in FECStatus.get_terminal_statuses_strings():

                def immediate_stream():
                    yield f"data: {submission.fec_status}\n\n"

                return StreamingHttpResponse(
                    immediate_stream(), content_type="text/event-stream"
                )
        except WebPrintSubmission.DoesNotExist:
            return StreamingHttpResponse(
                "data: ERROR: Submission not found\n\n",
                content_type="text/event-stream",
                status=404,
            )

        def event_stream():
            pubsub = None
            try:
                pubsub = redis_instance.pubsub(ignore_subscribe_messages=True)
                channel_name = f"webprint_status:{submission_id}"
                pubsub.subscribe(channel_name)
                yield "data: LISTENING\n\n"
                while True:
                    message = pubsub.get_message(timeout=20.0)
                    if message is None:
                        yield ": keep-alive\n\n"
                        continue
                    if message.get("type") == "message":
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        yield f"data: {data}\n\n"
                        break
            finally:
                if pubsub:
                    pubsub.unsubscribe()
                    pubsub.close()

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
