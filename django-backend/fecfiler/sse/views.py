import time
from django.http import StreamingHttpResponse
from django.shortcuts import render
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from rest_framework.renderers import BaseRenderer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from fecfiler.settings import SYSTEM_STATUS_CACHE_BACKEND, SYSTEM_STATUS_CACHE_AGE
from fecfiler.reports.models import Report
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
    @action(detail=False, methods=["get"])
    def stream(self, request):

        def event_stream():
            print(f"SSE connection opened for user: {request.user}")
            while True:
                data = f'data: The server time is {time.strftime("%H:%M:%S")}\n\n'
                yield data
                time.sleep(1)

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["X-Accel-Buffering"] = "no"
        response["Cache-Control"] = "no-cache"  # Ensure client doesn't cache the stream
        return response

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

                yield f"data: LISTENING\n\n"

                while True:
                    message = pubsub.get_message(timeout=20.0)

                    if message is None:
                        yield ": keep-alive\n\n"
                        continue

                    if message.get("type") == "message":
                        yield f"data: {message['data']}\n\n"
                        break  # Exit loop after sending the completion status

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
