from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from fecfiler.committee_accounts.views import IsCommitteeAdministrator
from .parser import extract_report


class ImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class ImportPreviewView(APIView):
    """Parse a CSV upload for an active committee administrator, without saving it."""

    permission_classes = [IsAuthenticated, IsCommitteeAdministrator]
    parser_classes = [MultiPartParser]

    @extend_schema(request=ImportUploadSerializer, responses={200: OpenApiTypes.OBJECT})
    def post(self, request):
        if len(request.FILES.getlist("file")) != 1 or len(request.FILES) != 1:
            raise ValidationError(
                {"file": ["Upload exactly one file using the file field."]}
            )
        serializer = ImportUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(extract_report(serializer.validated_data["file"]))
