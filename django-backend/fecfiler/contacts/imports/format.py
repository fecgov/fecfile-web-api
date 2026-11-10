"""The fixed-column contacts CSV contract shared by the resource and template."""
import csv
import io

import tablib
from import_export.formats.base_formats import CSV

CONTACT_COLUMNS = (
    "type",
    "name",
    "first_name",
    "last_name",
    "middle_name",
    "prefix",
    "suffix",
    "committee_id",
    "candidate_id",
    "candidate_office",
    "candidate_state",
    "candidate_district",
    "street_1",
    "street_2",
    "city",
    "state",
    "zip",
    "country",
    "telephone",
    "employer",
    "occupation",
)
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_ROWS = 1000


class ContactsCSV(CSV):
    def create_dataset(self, in_stream, **kwargs):
        if isinstance(in_stream, bytes):
            in_stream = in_stream.decode("utf-8-sig")
        reader = csv.reader(
            io.StringIO(in_stream.lstrip("\ufeff"), newline=""), strict=True
        )
        try:
            headers = next(reader)
            if len(headers) != len(set(headers)):
                raise ValueError("CSV headers must not repeat.")
            if not headers or any(key not in CONTACT_COLUMNS for key in headers):
                raise ValueError("CSV contains an empty or unsupported header.")
            required = {"type", "street_1", "city", "state", "country"}
            if not required.issubset(headers):
                raise ValueError(
                    "CSV requires type, street_1, city, state, and country columns."
                )
            dataset = tablib.Dataset(headers=headers)
            for number, row in enumerate(reader, start=2):
                if len(row) != len(headers):
                    raise ValueError(f"CSV row {number} has the wrong number of columns.")
                if len(dataset) >= MAX_ROWS:
                    raise ValueError(f"Import at most {MAX_ROWS} contacts at a time.")
                dataset.append(row)
            if not len(dataset):
                raise ValueError("CSV must contain at least one contact.")
            return dataset
        except StopIteration:
            raise ValueError("CSV must have a header and at least one contact.")
        except csv.Error:
            raise ValueError(f"Malformed CSV near line {reader.line_num}.")
