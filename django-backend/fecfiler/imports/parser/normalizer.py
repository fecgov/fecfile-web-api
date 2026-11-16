from datetime import datetime
import re

from fecfiler.web_services.dot_fec.dot_fec_serializer import get_field_mappings


def parse_date(value):
    if value == "":
        return None

    if not re.fullmatch(r"[0-9]{8}", value):
        raise ValueError(f"Expected YYYYMMDD, got {value!r}.")

    return datetime.strptime(value, "%Y%m%d").date().isoformat()


def parse_boolean_x(value):
    if value == "X":
        return True
    if value == "":
        return None

    raise ValueError(f"Expected X or blank, got {value!r}.")


def parse_boolean_yn(value):
    if value == "Y":
        return True
    if value == "N":
        return False
    if value == "":
        return None

    raise ValueError(f"Expected Y, N, or blank, got {value!r}.")


def preserve_value(value):
    if value == "":
        return None
    return value


FIELD_PARSERS = {
    None: preserve_value,
    "DATE": parse_date,
    "BOOLEAN_X": parse_boolean_x,
    "BOOLEAN_YN": parse_boolean_yn,
    # ignore for nows
    "ELECTION_CODE": preserve_value,
    "TEXT_TO_DATE": preserve_value,
    "LOAN_INTEREST_RATE": preserve_value,
}


def normalize_row(data, schema_name):
    mappings = get_field_mappings(schema_name)
    normalized = {}

    for field_name, value in data.items():
        mapping = mappings.get(field_name, {})
        serializer_type = mapping.get("serializer")

        if serializer_type not in FIELD_PARSERS:
            raise ValueError(
                f"No import converter for {serializer_type!r} "
                f"on {schema_name}.{field_name}."
            )

        try:
            normalized[field_name] = FIELD_PARSERS[serializer_type](value)
        except ValueError as error:
            raise ValueError(f"{schema_name}.{field_name}: {error}") from error

    return normalized
