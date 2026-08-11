from datetime import datetime
from fecfile_validate import validate
from fecfiler.settings import BASE_DIR
from decimal import Decimal, InvalidOperation
from curses import ascii
import os
import json

import structlog

logger = structlog.get_logger(__name__)

CRLF_STR = str(chr(ascii.CR) + chr(ascii.LF))
FS_STR = chr(ascii.FS)


def get_value_from_path(object, path):
    split_path = path if isinstance(path, list) else path.split(".")
    value = getattr(object, split_path[0], None)
    if len(split_path) > 1:
        return get_value_from_path(
            value,
            split_path[1:],
        )
    return value


def boolean_x_serializer(model_instance, field_name, mapping):
    value = get_value_from_path(model_instance, mapping.get("path", None) or field_name)
    return "X" if value else ""


def boolean_yn_serializer(model_instance, field_name, mapping):
    value = get_value_from_path(model_instance, mapping.get("path", None) or field_name)
    if value is True:
        return "Y"
    if value is False:
        return "N"
    return ""


def date_serializer(model_instance, field_name, mapping):
    date = get_value_from_path(model_instance, mapping.get("path", None) or field_name)
    return date.strftime("%Y%m%d") if date else ""


date_formats = [
    "%Y-%m-%d %H:%M:%S",  # "2024-01-10 00:00:00"
    "%m/%d/%Y",  # "01/02/2024"
    "%m/%d/%y",  # "01/02/24"
    "%m-%d-%Y",  # "01-02-2024"
    "%m-%d-%y",  # "01-02-24"
    "%Y-%m-%d",  # "2024-01-10" without time
]


# def election_code_serializer(model_instance, field_name, mapping):
#     form_model = model_instance.form_3 or model_instance.form_3x
#     if form_model is None:
#         raise ValueError(
#             "Attempted to serialize election code on a report without a valid F3 or F3X"
#         )

#     report_code = getattr(model_instance, "report_code", None)
#     election_date = getattr(form_model, "date_of_election", None)
#     if report_code is None:
#         raise ValueError(
#             "Attempted to serialize election code on a report without a report type"
#         )

#     if report_code in ["12P", "12G", "12R", "12S", "12C"]:
#         if election_date is None:
#             raise ValueError(
#                 f"Attempted to serialize election code on a {report_code} report"
#                 "without an election date"
#             )
#         return report_code[-1] + str(election_date.year)
#     else:
#         return default_serializer(model_instance, field_name, mapping)


def election_code_serializer(model_instance, field_name, mapping):
    form_model = model_instance.form_3 or model_instance.form_3x
    if form_model is None:
        raise ValueError(
            "Attempted to serialize election code on a report without a valid F3 or F3X"
        )

    report_code = getattr(model_instance, "report_code", None)
    election_date = getattr(form_model, "date_of_election", None)
    if report_code is None:
        raise ValueError(
            "Attempted to serialize election code on a report without a report type"
        )

    if report_code in [
        "12P",
        "12G",
        "12R",
        "12S",
        "12C",
        "30G",
        "30S",
        "30R",
    ]:
        if election_date is None:
            raise ValueError(
                f"Attempted to serialize election code on a {report_code} report"
                "without an election date"
            )
        return report_code[-1] + str(election_date.year)
    else:
        return default_serializer(model_instance, field_name, mapping)


def text_to_date_serializer(model_instance, field_name, mapping):
    date_string = get_value_from_path(
        model_instance, mapping.get("path", None) or field_name
    )
    for date_format in date_formats:
        try:
            # Try parsing with each format in the list
            date_object = datetime.strptime(date_string, date_format).date()
            return date_object.strftime("%Y%m%d") if date_object else ""
        except ValueError:
            continue  # If it fails, try the next format
    logger.debug(
        f"unable to match manually entered date {date_string} with any known formats.  "
        f"Returning value as is."
    )
    return date_string


def loan_interest_rate_serializer(model_instance, field_name, mapping):
    schedule = model_instance.schedule_c or model_instance.schedule_c1
    if schedule:
        interest_rate = schedule.loan_interest_rate
        is_percent = schedule.loan_interest_rate_is_percent

        if not is_percent:
            return interest_rate
        else:
            try:
                return str(Decimal(interest_rate) / 100)
            except InvalidOperation:
                raise ValueError(
                    f"Interest rate, {interest_rate}, "
                    f"on transaction, {model_instance.id}, "
                    "is not a valid number"
                )
    else:
        raise ValueError(
            "Attempted to serialize loan interest rate on "
            f"a transaction, {model_instance.id}, without a schedule c/c1"
        )


def default_serializer(model_instance, field_name, mapping):
    """For most field types, just stringifying the value will work.
    In the case where the field is None, we want empty string rather than
    "None", thus the falsy condition
    """
    value = get_value_from_path(model_instance, mapping.get("path", None) or field_name)
    return str(value) if value is not None else ""


"""A map of model field types to their serializers.
Pass the model instance and field name into the serializer to
get a string representation in the FEC standard
"""
FIELD_SERIALIZERS = {
    "BOOLEAN_X": boolean_x_serializer,
    "BOOLEAN_YN": boolean_yn_serializer,
    "DATE": date_serializer,
    "TEXT_TO_DATE": text_to_date_serializer,
    "LOAN_INTEREST_RATE": loan_interest_rate_serializer,
    "ELECTION_CODE": election_code_serializer,
    None: default_serializer,
}


def serialize_field(instance, field_name, field_mappings):
    """Serialize field to string in FEC standard
    Args:
        model_instance (django.db.models.Model): Instance of `model` that contains
        field to serialize.  In some cases when serializing a field we need to reference
        another field in the `model_instance`, so we pass it to the serializer.
        field_name (str): name of field to serialize
        field_mappings: mapping of field to how-to-access it, including special
        serializers to use
    """
    mapping = field_mappings[field_name]
    serializer_type = mapping.get("serializer", None)
    serializer = FIELD_SERIALIZERS[serializer_type]
    return serializer(instance, field_name, mapping)


def serialize_instance(schema_name, instance):
    """Serialize model instance into row of FEC standard
    Args:
        schema_name (str): name of schema. the schema informas column layout
        model_instance (django.db.models.Model): Instance of `model` that contains
        field to serialize.
    """
    column_sequences, row_length = extract_row_config(schema_name)
    field_mappings = get_field_mappings(schema_name)
    row = [
        (
            serialize_field(instance, column_sequences[column_index + 1], field_mappings)
            if (column_index + 1) in column_sequences
            else ""
        )
        for column_index in range(0, row_length)
    ]
    return FS_STR.join(row)


def get_field_mappings(schema_name):
    """Return field mappings as JSON object.
    Field Mappings map fields in a schema to a way of accessing them
    in the django instance

    Args:
        schema_name (str): name of schema to retrieve file for

    Returns:
        dict: JSON schema that matches the schema_name"""
    mapping_file = f"{schema_name}.json"
    mapping_path = os.path.join(
        BASE_DIR, "web_services/dot_fec/schema_fields/", mapping_file
    )
    with open(mapping_path) as fp:
        field_mappings = json.load(fp)

    return field_mappings


def extract_row_config(schema_name):
    """Extracts the column sequences and row length from the schema."""
    schema = validate.get_schema(schema_name)
    schema_properties = schema.get("properties", {}).items()
    column_sequences = {
        v.get("fec_spec", {}).get("COL_SEQ", None): k for k, v in schema_properties
    }
    row_length = max(filter(lambda k: k is not None, column_sequences.keys()))
    return column_sequences, row_length
