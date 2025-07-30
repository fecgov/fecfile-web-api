from fecfiler.settings import FEC_FORMAT_VERSION

"""These schemas have column sequences in 8.4 that are different from 8.5"""
OVERRIDE_LIST = ["SchC2", "F99"]


def get_schema_name_for_version(schema_name):
    """Returns the schema name unless we are overriding it for a specific version."""
    if FEC_FORMAT_VERSION == "8.4" and schema_name in OVERRIDE_LIST:
        schema_name = f"_OVERRIDE_{schema_name}"
    return schema_name
