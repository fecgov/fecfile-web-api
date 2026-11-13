from rest_framework import serializers
from fecfiler.imports.models import Import
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.decorators import action
from fecfiler.committee_accounts.views import CommitteeOwnedViewMixin
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.committee_accounts.models import CommitteeAccount
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView, PermissionDenied
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from django.http import HttpResponseBadRequest


class ImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate(self, data):
        # TODO validate size
        # TODO validate file type
        """
        Ensure that we are not trying to start an import when there is already one going
        """
        request = self.context.get("request")
        if not request:
            raise ValidationError("Request context is required.")
        committee_uuid = request.session.get("committee_uuid")
        if not committee_uuid:
            raise PermissionDenied("You must activate a committee account")
        committee_account = CommitteeAccount.objects.get(id=committee_uuid)
        existing_import = get_active_import(committee_account)
        if existing_import is not None:
            raise ValidationError(
                f"This account already has an import in progress.  Cannot have more than one."
            )
        return True


class ImportViewSet(CommitteeOwnedViewMixin):
    """Handle a CSV upload for an active committee administrator, without saving it."""

    queryset = Import.objects.all()

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser],
        url_path="upload-file",
    )
    def upload_file(self, request):
        if len(request.FILES.getlist("file")) != 1 or len(request.FILES) != 1:
            raise ValidationError(
                {"file": ["Upload exactly one file using the file field."]}
            )
        serializer = ImportUploadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return Response("good to go")


def get_active_import(committee_account):
    # TODO actually filter down to active
    active_imports = Import.objects.filter(committee_account=committee_account)
    number_of_imports = active_imports.count()
    if number_of_imports > 1:
        raise RuntimeError(
            f"Committee account ({committee_account.committee_id}) has more than one import."
        )
    return active_imports.first()
