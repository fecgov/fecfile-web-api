import uuid


def generate_fec_uid():
    unique_id = uuid.uuid4()
    hex_id = unique_id.hex.upper()
    # Take 20 characters from the end, skipping over the 20th char from the right,
    # which is the version number (uuid4 -> "4")
    return hex_id[-21] + hex_id[-19:]
