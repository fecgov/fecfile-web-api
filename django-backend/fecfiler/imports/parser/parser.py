from fecfiler.imports.models import Import, ImportStatus
from fecfiler.imports.storage import read_import_file, save_upload
from fecfile_validate import validate
import csv


def parse_upload_file(import_instance: Import):
    committee_fec_id = import_instance.committee_account.committee_id
    import_instance.status = ImportStatus.PARSE_READING_UPLOAD
    import_instance.save(update_fields=["status", "updated"])

    upload_file = read_import_file(import_instance.uploaded_file_name)

    reader = csv.reader(
        upload_file.decode("utf-8").splitlines(), delimiter=",", quotechar='"'
    )

    print(f"Parsing header row for {committee_fec_id}'s upload")
    header_row = next(reader)
    parsed_header = parse_header(header_row)
    print(f"Parsed header for {committee_fec_id}'s upload: {parsed_header}")

    return {"header": parsed_header}


def parse_header(header):
    column_sequences, row_length = extract_row_config("HDR")
    if len(header) != row_length:
        raise Exception(f"Expected {row_length} header columns, got {len(header)}.")

    return {
        field_name: header[column_sequence - 1]
        for column_sequence, field_name in column_sequences.items()
        if column_sequence is not None
    }


def extract_row_config(schema_name):
    """Extracts the column sequences and row length from the schema."""
    schema = validate.get_schema(schema_name)
    schema_properties = schema.get("properties", {}).items()
    column_sequences = {
        v.get("fec_spec", {}).get("COL_SEQ", None): k for k, v in schema_properties
    }
    row_length = max(filter(lambda k: k is not None, column_sequences.keys()))
    return column_sequences, row_length
