from rest_framework import serializers
from import_export_extensions.api.serializers.import_job import CreateImportJob
from import_export_extensions.models import ImportJob

from fecfiler.contacts.models import Contact
from fecfiler.contacts.serializers import ContactSerializer
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
from .format import CONTACT_COLUMNS, MAX_FILE_SIZE


class ContactImportRowSerializer(
    FecSchemaValidatorSerializerMixin, serializers.ModelSerializer
):
    # Reuse field/schema rules, omitting the regular API's FEC-ID uniqueness check.
    type = serializers.ChoiceField(choices=Contact._meta.get_field("type").choices)

    class Meta:
        model = Contact
        fields = CONTACT_COLUMNS

    def get_schema_name(self, data):
        return f"Contact_{ContactSerializer.contact_value[data['type']]}"


class ContactImportCreateSerializer(CreateImportJob):
    def validate_file(self, upload):
        if not upload.name.lower().endswith(".csv"):
            raise serializers.ValidationError("Choose a CSV file.")
        if not upload.size or upload.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("Choose a nonempty CSV file up to 10 MB.")
        return upload

    def validate(self, data):
        if data.get("force_import") or data.get("skip_parse_step"):
            raise serializers.ValidationError(
                "Partial imports and skipping validation are disabled."
            )
        return data


class ContactImportJobSerializer(serializers.ModelSerializer):
    total_rows = serializers.SerializerMethodField()
    totals = serializers.SerializerMethodField()
    errors = serializers.SerializerMethodField()
    preview = serializers.SerializerMethodField()

    class Meta:
        model = ImportJob
        fields = (
            "id",
            "import_status",
            "total_rows",
            "totals",
            "errors",
            "preview",
            "created",
            "modified",
        )

    def get_total_rows(self, job):
        return getattr(job.result, "total_rows", 0)

    def get_totals(self, job):
        return getattr(job.result, "totals", {})

    def get_errors(self, job):
        errors = []
        result = job.result
        for row in getattr(result, "invalid_rows", []):
            errors.append({"row": row.number + 1, "fields": row.error.message_dict})
        for number, row_errors in result.row_errors():
            errors.append(
                {
                    "row": number + 1,
                    "fields": {
                        "__all__": ["Could not process this row; no contacts were saved."]
                    },
                }
            )
        if job.import_status in ("PARSE_ERROR", "IMPORT_ERROR"):
            errors.append(
                {
                    "row": None,
                    "fields": {
                        "__all__": [
                            job.error_message
                            if job.import_status == "PARSE_ERROR"
                            else "Import failed; no contacts were saved."
                        ]
                    },
                }
            )
        if result.base_errors:
            errors.append(
                {
                    "row": None,
                    "fields": {
                        "__all__": [
                            "Could not validate this import; no contacts were saved."
                        ]
                    },
                }
            )
        return errors

    def get_preview(self, job):
        if job.import_status != "PARSED":
            return []
        return [
            {key: getattr(row.instance, key, None) for key in CONTACT_COLUMNS}
            for row in job.result.rows[:100]
            if row.instance is not None
        ]
