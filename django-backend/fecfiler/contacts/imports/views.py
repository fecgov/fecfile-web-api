from django.conf import settings
from django.http import Http404
from django.db import transaction
from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from import_export_extensions.api.views import ImportJobViewSet
from import_export_extensions.models import ImportJob

from fecfiler.committee_accounts.views import IsCommitteeAdministrator
from .resource import ContactImportResource
from .serializers import ContactImportCreateSerializer, ContactImportJobSerializer


class ContactImportEnabled(permissions.BasePermission):
    def has_permission(self, request, view):
        return settings.FLAG__ENABLE_IMPORT


class ContactImportViewSet(ImportJobViewSet):
    resource_class = ContactImportResource
    import_detail_serializer_class = ContactImportJobSerializer
    serializer_class = ContactImportJobSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsCommitteeAdministrator,
        ContactImportEnabled,
    ]
    parser_classes = [MultiPartParser, JSONParser]

    def get_serializer_class(self):
        if getattr(self, "action", None) == self.import_action:
            return self.get_import_create_serializer_class()
        return self.import_detail_serializer_class

    def get_import_create_serializer_class(self):
        class CreateContactsImport(ContactImportCreateSerializer):
            resource_class = ContactImportResource

        return CreateContactsImport

    def get_import_resource_kwargs(self):
        return {
            "committee_id": str(self.request.session["committee_uuid"]),
            "user_id": str(self.request.user.pk),
        }

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ImportJob.objects.none()
        return ImportJob.objects.filter(
            resource_path=ContactImportResource.class_path,
            resource_kwargs__committee_id=str(self.request.session["committee_uuid"]),
        )

    def start_import(self, request):
        if len(request.FILES.getlist("file")) != 1 or len(request.FILES) != 1:
            raise ValidationError(
                {"file": ["Upload exactly one CSV using the file field."]}
            )
        return super().start_import(request)

    def confirm(self, request, *args, **kwargs):
        # A second confirmation cannot queue another import of the same job.
        with transaction.atomic():
            job = self.get_queryset().select_for_update().filter(pk=kwargs["pk"]).first()
            if job is None:
                raise Http404
            try:
                job.confirm_import()
            except ValueError as error:
                raise ValidationError(str(error))
        return Response(ContactImportJobSerializer(job).data)
