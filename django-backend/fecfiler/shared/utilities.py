import uuid
import requests
from rest_framework.status import HTTP_404_NOT_FOUND
from fecfiler import settings


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


def get_boolean_from_string(string):
    return str(string).strip().lower() in {"true", "1", "yes", "y"}


"""
FEC API methods
"""


def query_fec_api_single(endpoint, params):
    results = query_fec_api(endpoint, params)
    return results[0] if results else None


def query_fec_api(endpoint, params, raise_for_404=True):
    """Shared method to query an EFO API"""

    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"FECfile+ {settings.SPACE}",
    }
    response = requests.get(endpoint, headers=headers, params=params)
    if response.status_code != HTTP_404_NOT_FOUND or raise_for_404:
        response.raise_for_status()
    response_data = response.json()
    return response_data.get("results", [])
