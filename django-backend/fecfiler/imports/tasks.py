from celery import shared_task
from .models import Import, ImportStatus
from .parser.parser import parse_upload_file
from .storage import save_import_file
from .importer.report import import_report
import json
from django.core.files.base import ContentFile


@shared_task
def parse_upload(import_id):
    import_instance = Import.objects.get(pk=import_id)

    try:
        if import_instance.status != ImportStatus.PARSE_INITIALIZING:
            raise Exception(
                f"Tried to parse upload {import_id} "
                f"for committee account {import_instance.committee_account.committee_id} "
                f"when it is not in parsing status"
            )

        import_instance.update_status(ImportStatus.PARSE_STARTING_TASK)

        print("Parsing upload...")
        parsed_data = parse_upload_file(import_instance)
        print(f"Finished parsing upload {import_id}")

        import_instance.update_status(ImportStatus.PARSE_WRITING_PARSED_FILE)
        parsed_data_file_name = f"{import_instance.uploaded_file_name}_parsed.json"
        parsed_file = ContentFile(
            json.dumps(parsed_data, ensure_ascii=False, allow_nan=False).encode("utf-8"),
            name=parsed_data_file_name,
        )
        save_import_file(parsed_file)

        import_instance.status = ImportStatus.PARSE_COMPLETED
        import_instance.parsed_file_name = parsed_data_file_name
        import_instance.save(update_fields=["status", "updated", "parsed_file_name"])

    except Exception as e:
        import_instance.update_status(ImportStatus.PARSE_FAILED)
        raise e


@shared_task
def start_import(import_id):
    import_instance = Import.objects.get(pk=import_id)

    try:
        if import_instance.status != ImportStatus.IMPORT_INITIALIZING:
            raise Exception(
                f"Tried to start import {import_id} "
                f"for committee account {import_instance.committee_account.committee_id} "
                f"when it is not in importing status"
            )

        import_instance.update_status(ImportStatus.IMPORT_STARTING_TASK)

        print(f"Starting import for {import_id}...")
        import_report(import_instance)
        print(f"Finished import for {import_id}")

        import_instance.update_status(ImportStatus.IMPORT_COMPLETED)

    except Exception as e:
        import_instance.update_status(ImportStatus.IMPORT_FAILED)
        raise e
