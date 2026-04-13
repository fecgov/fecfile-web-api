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


def censor_api_key(input_string):
    try:
        safe_string = input_string.replace(
            settings.STAGE_OPEN_FEC_API_KEY,
            settings.STAGE_OPEN_FEC_API_KEY[:4] + "*" * 8
        )
        safe_string = safe_string.replace(
            settings.PRODUCTION_OPEN_FEC_API_KEY,
            settings.PRODUCTION_OPEN_FEC_API_KEY[:4] + "*" * 8
        )
        return safe_string
    except Exception:
        raise Exception("Encountered exception when attempting to stub out API key")


def get_boolean_from_string(string):
    return string.lower() == "true"


"""
FEC API methods
"""


# A modified version of the python request library's raise_for_status method
# that sanitizes the url when logging an error
def raise_for_status(response):
    http_error_msg = ""
    if isinstance(response.reason, bytes):
        try:
            reason = response.reason.decode("utf-8")
        except UnicodeDecodeError:
            reason = response.reason.decode("iso-8859-1")
    else:
        reason = response.reason

    sanitized_url = censor_api_key(response.url)

    if 400 <= response.status_code < 500:
        http_error_msg = (
            f"{response.status_code} Client Error: {reason} for url: {sanitized_url}"
        )

    elif 500 <= response.status_code < 600:
        http_error_msg = (
            f"{response.status_code} Server Error: {reason} for url: {sanitized_url}"
        )

    if http_error_msg:
        raise requests.HTTPError(http_error_msg, response=response)


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
        try:
            raise_for_status(response)
        except requests.HTTPError as error:
            error_message = str(error)
            safe_message = censor_api_key(error_message)
            raise requests.HTTPError(safe_message)

    response_data = response.json()
    return response_data.get("results", [])
