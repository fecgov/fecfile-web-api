from rest_framework import serializers
from fecfiler.imports.models import Import, ImportStatus
from rest_framework.mixins import RetrieveModelMixin
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
from fecfiler.imports.storage import save_upload

from fecfiler.imports.serializers import ImportSerializer, ImportUploadSerializer


class ImportViewSet(CommitteeOwnedViewMixin, RetrieveModelMixin):
    """Handle a CSV upload for an active committee administrator, without saving it."""

    queryset = Import.objects.all()
    serializer_class = ImportSerializer

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser],
        url_path="upload-file",
    )
    def upload_file(self, request):
        committee_uuid = self.get_committee_uuid()
        if len(request.FILES.getlist("file")) != 1 or len(request.FILES) != 1:
            raise ValidationError(
                {"file": ["Upload exactly one file using the file field."]}
            )
        serializer = ImportUploadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        self.validate_upload(request, committee_uuid)

        import_instance = Import.objects.create(
            committee_account_id=committee_uuid,
            uploaded_file_name=request.FILES["file"].name,
            status=ImportStatus.INITIAL,
        )

        save_file(import_instance, request.FILES["file"])

        return Response(ImportSerializer(import_instance).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="start-parse",
    )
    def start_parse(self, request, pk):
        import_instance = self.get_object()
        if import_instance.status != ImportStatus.UPLOADED:
            raise ValidationError(
                {"status": ["Cannot start parse unless file is uploaded."]}
            )
        import_instance.status = ImportStatus.PARSING
        import_instance.save()
        return Response(ImportSerializer(import_instance).data)

    def validate_upload(self, request, committee_uuid):
        # TODO validate size
        # TODO validate file type
        """
        Ensure that we are not trying to start an import when there is already one going
        """
        committee_account = CommitteeAccount.objects.get(id=committee_uuid)
        """off for now"""
        # existing_import = get_active_import(committee_account)
        # if existing_import is not None:
        #     raise ValidationError(
        #         f"This account already has an import in progress.  Cannot have more than one."
        #     )


def get_active_import(committee_account):
    # TODO actually filter down to active
    active_imports = Import.objects.filter(committee_account=committee_account)
    number_of_imports = active_imports.count()
    if number_of_imports > 1:
        raise RuntimeError(
            f"Committee account ({committee_account.committee_id}) has more than one import."
        )
    return active_imports.first()


def save_file(import_instance, file):
    file.name = f"{import_instance.committee_account_id}_upload"
    import_instance.uploaded_file_name = save_upload(file)
    import_instance.status = ImportStatus.UPLOADED
    import_instance.save()
