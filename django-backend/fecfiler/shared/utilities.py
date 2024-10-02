import uuid


def generate_fec_uid():
    unique_id = uuid.uuid4()
    hex_id = unique_id.hex.upper()
    # Take 20 characters from the end, skipping over the 20th char from the right,
    # which is the version number (uuid4 -> "4")
    return hex_id[-21] + hex_id[-19:]


def get_model_data(data, model):
    field_names = sum(
        [[field.name, field.name + "_id"] for field in model._meta.get_fields()], []
    )
    return {field: data[field] for field in field_names if field in data}


def get_float_from_string(string, fallback=None):
    try:
        return float(string)
    except Exception:
        if fallback is not None:
            return fallback
        raise ValueError("String to float conversion failed with no provided fallback")
