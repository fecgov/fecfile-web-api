import github3
import structlog
from fecfiler.settings import FECFILE_GITHUB_TOKEN
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import FeedbackSerializer

logger = structlog.get_logger(__name__)


class FeedbackViewSet(viewsets.ViewSet):
    @action(
        detail=False,
        methods=["post"],
        url_path="submit",
    )
    def submit_feedback(self, request):
        serializer = FeedbackSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        title = "User feedback on " + request.META.get("Referer")

        body = (
            "## What were you trying to do and how can we improve it?\n %s \n\n"
            "## General feedback?\n %s \n\n"
            "## Tell us about yourself\n %s \n\n"
            "## Details\n"
            "* URL: %s \n"
            "* User Agent: %s"
        ) % (
            serializer.validated_data["action"],
            serializer.validated_data["feedback"],
            serializer.validated_data["about"],
            request.META.get("Referer"),
            request.META["User-Agent"],
        )

        client = github3.login(token=FECFILE_GITHUB_TOKEN)
        client.repository("fecgov", "fecfile-feedback").create_issue(title, body=body)

        return Response({"status": "feedback submitted"})
