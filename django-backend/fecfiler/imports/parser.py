"""Extract a report preview from the CSV export layout; never persist data."""

import csv
import io
import json
from pathlib import Path

from rest_framework.exceptions import ValidationError

MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_VERSION = "8.5"
SCHEMA_DIRECTORY = (
    Path(__file__).resolve().parents[1] / "web_services/dot_fec/schema_fields"
)


def read_mapping(name):
    with (SCHEMA_DIRECTORY / f"{name}.json").open(encoding="utf-8") as schema:
        return json.load(schema)


def extract_report(upload):
    if not upload.name.lower().endswith(".csv"):
        raise ValidationError({"file": ["Choose a CSV file."]})
    if not upload.size or upload.size > MAX_FILE_SIZE:
        raise ValidationError({"file": ["Choose a nonempty CSV file up to 10 MB."]})
    content = upload.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise ValidationError({"file": ["File exceeds the 10 MB limit."]})
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValidationError({"file": ["CSV must use UTF-8 encoding."]})

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header_row = next(reader)
        report_row = next(reader)
    except StopIteration:
        raise ValidationError(
            {"file": ["Expected an HDR row followed by an F3X report row."]}
        )
    except csv.Error:
        raise ValidationError({"file": [f"Invalid CSV near line {reader.line_num}."]})

    header_fields = read_mapping("HDR")
    if len(header_row) != len(header_fields) or header_row[:2] != ["HDR", "FEC"]:
        raise ValidationError({"file": ["The first row must be an FEC HDR record."]})
    header = dict(zip(header_fields, header_row))
    if header["fec_version"] != SUPPORTED_VERSION:
        raise ValidationError({"file": ["This prototype supports FEC version 8.5 only."]})
    if not report_row or report_row[0] not in ("F3XN", "F3XA", "F3XT"):
        raise ValidationError({"file": ["The second row must be an F3X report record."]})
    report_fields = read_mapping("F3X")
    if len(report_row) != len(report_fields):
        raise ValidationError(
            {
                "file": [
                    f"The F3X row must have {len(report_fields)} columns; "
                    f"received {len(report_row)}."
                ]
            }
        )
    return {
        "header": header,
        "report": dict(zip(report_fields, report_row)),
        "saved": False,
        "transactions_processed": False,
    }
