from fecfiler.imports.parser import SUPPORTED_REPORT_TYPES
from fecfiler.reports.form_3x.serializers import Form3XSerializer
import json

from fecfiler.imports.storage import read_import_file


def import_report(import_instance):
    parsed_data = load_parsed_data(import_instance)

    report_data = build_report_payload(parsed_data["report"])

    report = create_imported_report(import_instance, report_data)


def load_parsed_data(import_instance):
    if not import_instance.parsed_file_name:
        raise ValueError("The import has no parsed file.")

    content = read_import_file(import_instance.parsed_file_name)
    parsed_data = json.loads(content)

    if not isinstance(parsed_data, dict):
        raise ValueError("Parsed import data must be an object.")

    if not isinstance(parsed_data.get("report"), dict):
        raise ValueError("Parsed import data is missing its report.")

    return parsed_data


def build_report_payload(parsed_report):
    form_type = parsed_report.get("form_type")

    if form_type not in SUPPORTED_REPORT_TYPES:
        raise ValueError(f"Unsupported report form type: {form_type!r}")

    serializer = Form3XSerializer()

    payload = {
        name: parsed_report[name]
        for name, field in serializer.fields.items()
        if not field.read_only and name in parsed_report
    }

    return payload


def create_imported_report(import_instance, report_data):
    committee_account_id = import_instance.committee_account.committee_id

    serializer = Form3XSerializer(
        data=report_data.copy(),
        context={
            "committee_uuid": import_instance.committee_account_id,
        },
    )
    serializer.is_valid(raise_exception=True)
    return serializer.save()
