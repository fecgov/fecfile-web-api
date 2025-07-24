import time
from django.http import StreamingHttpResponse
from django.shortcuts import render
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from rest_framework.renderers import BaseRenderer
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated


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
