from fecfile_validate import validate
from fecfiler.settings import BASE_DIR
from curses import ascii
import os
import json

import logging

logger = logging.getLogger(__name__)

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


def default_serializer(model_instance, field_name, mapping):
    """For most field types, just stringifying the value will work.
    In the case where the field is None, we want empty string rather than
    "None", thus the falsy condition
    """
    value = get_value_from_path(model_instance, mapping.get("path", None) or field_name)
    return str(value) if value else ""


"""A map of model field types to their serializers.
Pass the model instance and field name into the serializer to
get a string representation in the FEC standard
"""
FIELD_SERIALIZERS = {
    "BOOLEAN_X": boolean_x_serializer,
    "BOOLEAN_YN": boolean_yn_serializer,
    "DATE": date_serializer,
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
        serialize_field(instance, column_sequences[column_index + 1], field_mappings)
        if (column_index + 1) in column_sequences
        else ""
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
    schema = validate.get_schema(schema_name)
    schema_properties = schema.get("properties", {}).items()
    column_sequences = {
        v.get("fec_spec", {}).get("COL_SEQ", None): k for k, v in schema_properties if v.get("fec_spec", {}).get("COL_SEQ", None)
    }
    row_length = max(column_sequences.keys())
    return column_sequences, row_length
