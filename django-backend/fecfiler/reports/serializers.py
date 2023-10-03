import logging

from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from rest_framework.serializers import (
    UUIDField,
    CharField,
    ModelSerializer,
)
from fecfiler.contacts.models import Contact
from .models import Report
from .f3x_report.models import F3XReport


logger = logging.getLogger(__name__)
MISSING_SCHEMA_NAME_ERROR = ValidationError(
    {"schema_name": ["No schema_name provided"]}
)


class F3xReportSerializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in F3XReport._meta.get_fields()
            if f.name not in ["deleted", "report"]
        ]
        model = F3XReport


class ReportSerializerBase(
    CommitteeOwnedSerializer, FecSchemaValidatorSerializerMixin
):
    """id must be explicitly configured in order to have it in validated_data
    https://github.com/encode/django-rest-framework/issues/2320#issuecomment-67502474"""

    id = UUIDField(required=False)
    form_type = CharField(required=False, allow_null=True)
    f3x_report = F3xReportSerializer(required=False)

    """
    def create(self, validated_data: dict):
        print("\n\n\n",validated_data,"\n\n")
        return super(ReportSerializerBase).create(**validated_data)
    """

    def to_representation(self, instance, depth=0):
        print("\n\n\n\n\nYOOOOOO\n\n\n\n")
        representation = super().to_representation(instance)
        f3x_report = None
        if ("f3x_report" in representation.keys()):
            f3x_report = representation.pop("f3x_report")

        if f3x_report:
            for property in f3x_report:
                if not representation.get(property):
                    representation[property] = f3x_report[property]

        representation["form_type"] = instance.form_type

        return representation
    
    def create(self, validated_data):
        print("CREATED:", validated_data, "\n\n\n")
        return self.Meta.model.create(validated_data)

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        if internal_value.get("form_type"):
            internal_value["_form_type"] = internal_value["form_type"]
        return internal_value

    def validate(self, data):
        self.context["fields_to_ignore"] = self.context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    class Meta:
        model = Report

        def get_fields():
            return [
                f.name
                for f in Report._meta.get_fields()
                if f.name not in ["deleted"]
            ] + [
                "form_type",
                "fields_to_validate",
                "f3x_report",
            ]

        fields = get_fields()
        read_only_fields = ["id","deleted","created","updated"]
