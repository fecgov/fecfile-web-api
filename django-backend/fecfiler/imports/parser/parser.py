from fecfiler.imports.models import Import, ImportStatus
from fecfiler.imports.storage import read_import_file
from fecfiler.imports.parser.normalizer import normalize_row
from fecfile_validate import validate
import csv


def parse_upload_file(import_instance: Import):
    committee_fec_id = import_instance.committee_account.committee_id

    import_instance.update_status(ImportStatus.PARSE_READING_UPLOAD)

    upload_file = read_import_file(import_instance.uploaded_file_name)

    reader = csv.reader(
        upload_file.decode("utf-8").splitlines(), delimiter=",", quotechar='"'
    )

    print(f"Parsing header row for {committee_fec_id}'s upload")
    header_row = next(reader)
    parsed_header = parse_row(header_row, get_row_config("HDR"))
    print(f"Parsed header for {committee_fec_id}'s upload: {parsed_header}")

    print(f"Parsing report row for {committee_fec_id}'s upload")
    report_row = next(reader)
    parsed_report = parse_report(report_row)
    print(f"Parsed report for {committee_fec_id}'s upload")

    print(f"Parsing transactions for {committee_fec_id}'s upload")
    parsed_transactions = parse_transactions(reader)
    print(f"Parsed transactions for {committee_fec_id}'s upload: {parsed_transactions}")

    return {
        "header": parsed_header,
        "report": parsed_report,
        "transactions": parsed_transactions,
    }


SUPPORTED_FORM_TYPES = {
    "F3XN": "F3X",
    "F3XA": "F3X",
    "F3XT": "F3X",
}


def parse_report(report_row):
    if not report_row:
        raise Exception("The report row is empty.")

    form_type = report_row[0]
    schema_name = SUPPORTED_FORM_TYPES.get(form_type)

    if schema_name is None:
        raise Exception(f"Unsupported report form type: {form_type!r}")

    return parse_row(report_row, get_row_config(schema_name))


""" Longer prefixes must come first: SC1/SC2 before SC,
because we match with first hit
"""
TRANSACTION_SCHEDULE_PREFIXES = (
    ("SC1", "SchC1"),
    ("SC2", "SchC2"),
    ("SA", "SchA"),
    ("SB", "SchB"),
    ("SC", "SchC"),
    ("SD", "SchD"),
    ("SE", "SchE"),
    ("SF", "SchF"),
)


def get_transaction_schema(form_type):
    for prefix, schema_name in TRANSACTION_SCHEDULE_PREFIXES:
        if form_type.startswith(prefix):
            return schema_name

    raise ValueError(f"Unsupported transaction schedule: {form_type!r}")


def parse_transaction(transaction_row):
    if not transaction_row:
        raise Exception("The transaction row is empty.")

    form_type = transaction_row[0]
    schema_name = get_transaction_schema(form_type)

    return {
        "schema_name": schema_name,
        "data": parse_row(transaction_row, get_row_config(schema_name)),
    }


def parse_transactions(reader):
    transactions = []

    # The header and report have already been consumed.
    for row_number, row in enumerate(reader, start=3):
        if not row or all(value == "" for value in row):
            continue

        try:
            transaction = parse_transaction(row)
        except Exception as error:
            raise Exception(f"Row {row_number}: {error}") from error

        transaction["source_row"] = row_number
        transactions.append(transaction)

    return transactions


def get_row_config(schema_name):
    column_sequences, row_length = extract_row_config(schema_name)
    return (schema_name, column_sequences, row_length)


def parse_row(row, row_config):
    schema_name, column_sequences, row_length = row_config

    if len(row) != row_length:
        raise ValueError(
            f"Expected {row_length} columns for {schema_name}, " f"got {len(row)}."
        )

    row_data = {
        field_name: row[column_sequence - 1]
        for column_sequence, field_name in column_sequences.items()
        if column_sequence is not None
    }

    return normalize_row(row_data, schema_name)


def extract_row_config(schema_name):
    """Extracts the column sequences and row length from the schema."""
    schema = validate.get_schema(schema_name)
    schema_properties = schema.get("properties", {}).items()
    column_sequences = {
        v.get("fec_spec", {}).get("COL_SEQ", None): k for k, v in schema_properties
    }
    row_length = max(filter(lambda k: k is not None, column_sequences.keys()))
    return column_sequences, row_length
