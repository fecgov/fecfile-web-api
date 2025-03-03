import logging
import requests
import re
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import CommitteeAccount, Membership

from fecfiler import settings
import redis
import json

logger = logging.getLogger(__name__)


COMMITTEE_DATA_REDIS_KEY = "COMMITTEE_DATA"
if settings.FLAG__COMMITTEE_DATA_SOURCE == "MOCKED":
    redis_instance = redis.Redis.from_url(settings.MOCK_OPENFEC_REDIS_URL)
else:
    redis_instance = None


PRODUCTION_PAC_COMMITTEE_TYPES = ["O", "U", "D", "N", "Q", "V", "W"]
PRODUCTION_QUALIFIED_COMMITTEES = ["Q", "W", "Y"]


def check_email_match(email, f1_emails):
    """
    Check if the provided email matches any of the committee emails.

    Args:
        email (str): The email to be checked.
        f1_emails (str): A string containing a list of committee emails separated
        by commas or semicolons.

    Returns:
        str or None: If the provided email does not match any of the committee emails,
        returns a string indicating the mismatch. Otherwise, returns None.
    """
    if not f1_emails:
        return "No email provided in F1"
    else:
        f1_email_lowercase = f1_emails.lower()
        f1_emails = re.split(r"[;,]", f1_email_lowercase)
        if email.lower() not in f1_emails:
            return f"Email {email} does not match committee email"
    return None


def check_can_create_committee_account(committee_id, user):
    email = user.email

    committee_emails = get_committee_emails(committee_id)
    failure_reason = check_email_match(email, committee_emails)

    existing_account = CommitteeAccount.objects.filter(committee_id=committee_id).first()
    if existing_account:
        failure_reason = f"Committee account {committee_id} already created"

    if failure_reason:
        logger.error(f"Failure to create committee account: {failure_reason}")
        return False

    return True


def create_committee_account(committee_id, user):
    if not check_can_create_committee_account(committee_id, user):
        raise ValidationError("could not create committee account")

    account = CommitteeAccount.objects.create(committee_id=committee_id)
    Membership.objects.create(
        committee_account=account,
        user=user,
        role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
    )

    return account


def get_committee_emails(committee_id):
    match settings.FLAG__COMMITTEE_DATA_SOURCE:
        case "PRODUCTION":
            emails = get_production_committee_emails(committee_id)
        case "TEST":
            emails = get_test_committee_emails(committee_id)
        case "MOCKED":
            emails = get_mocked_committee_emails(committee_id)
    return emails


def get_committee_account_data(committee_id):
    match settings.FLAG__COMMITTEE_DATA_SOURCE:
        case "PRODUCTION":
            committee = get_production_committee_data(committee_id)
        case "TEST":
            committee = get_test_committee_data(committee_id)
        case "MOCKED":
            committee = get_mocked_committee_data(committee_id)
    return committee


"""
FEC API methods
"""


def query_fec_api(endpoint, params):
    """Shared method to query an EFO API"""
    headers = {"Content-Type": "application/json"}
    response = requests.get(endpoint, headers=headers, params=params)
    response_data = response.json()
    committee_results = response_data.get("results", [])
    return committee_results[0] if committee_results else None


def query_multiple_endpoints(endpoints, params):
    """Queries multiple endpoints and returns the first successful response"""
    for endpoint in endpoints:
        response = query_fec_api(endpoint, params)
        if response:
            return response
    return None


"""
Production FEC
"""


def get_production_committee_raw_first(committee_id):
    """Queries the production FEC API for committee data
    First tries raw endpoint and then falls back to processed endpoint
    """
    raw_and_processed_endpoints = [
        f"{settings.PRODUCTION_OPEN_FEC_API}efile/form1/",
        f"{settings.PRODUCTION_OPEN_FEC_API}committee/{committee_id}/",
    ]
    params = {
        "api_key": settings.PRODUCTION_OPEN_FEC_API_KEY,
        "committee_id": committee_id,
    }
    return query_multiple_endpoints(raw_and_processed_endpoints, params)


def get_production_committee_processed_first(committee_id):
    """Queries the production FEC API for committee data
    First tries processed endpoint and then falls back to raw endpoint
    """
    processed_and_raw_endpoints = [
        f"{settings.PRODUCTION_OPEN_FEC_API}committee/{committee_id}/",
        f"{settings.PRODUCTION_OPEN_FEC_API}efile/form1/",
    ]
    params = {
        "api_key": settings.PRODUCTION_OPEN_FEC_API_KEY,
        "committee_id": committee_id,
    }
    return query_multiple_endpoints(processed_and_raw_endpoints, params)


def get_production_committee_emails(committee_id):
    """"""
    committee = get_production_committee_raw_first(committee_id)
    return committee.get("email", "") if committee else ""


def get_production_committee_data(committee_id):
    committee_data = get_production_committee_processed_first(committee_id)
    if committee_data is None:
        return None

    # Committee Type Label
    committee_data["committee_type_label"] = committee_data.get(
        "committee_type_full", None
    )

    # PAC/PTY
    committee_data["isPTY"] = is_production_efo_pty(committee_data)
    committee_data["isPAC"] = is_production_efo_pac(committee_data)

    # Qualified
    committee_data["qualified"] = (
        committee_data.get("committee_type") in PRODUCTION_QUALIFIED_COMMITTEES
    )

    return committee_data


def is_production_efo_pty(committee_data):
    designation = committee_data.get("designation", None)
    committee_type = committee_data.get("committee_type", None)
    return designation is not None and (
        committee_type == "Y" or (committee_type == "X" and designation != "U")
    )


def is_production_efo_pac(committee_data):
    return committee_data.get("committee_type") in PRODUCTION_PAC_COMMITTEE_TYPES


"""
Test FEC
"""


def get_committee_from_test_fec(committee_id):
    """
    Retrieves committee data from test efo using the fec API.
    """
    params = {
        "api_key": settings.STAGE_OPEN_FEC_API_KEY,
        "committee_id": committee_id,
    }
    endpoint = f"{settings.STAGE_OPEN_FEC_API}efile/test-form1/"
    committee_data = query_fec_api(endpoint, params)
    return committee_data if committee_data is not None else None


def get_test_committee_emails(committee_id):
    committee = get_committee_from_test_fec(committee_id)
    return committee.get("email", "") if committee else ""


def get_test_committee_data(committee_id):
    """
    Retrieves committee data from test efo using the fec API.
    Derives committee_type_label, isPTY, isPAC, qualified, filing_frequency,
    and maps some fields to their names as prod has them
    """
    committee_data = get_committee_from_test_fec(committee_id)

    print(f"AHOY {committee_data}")
    if committee_data is None:
        return None

    # PAC/PTY
    committee_data["isPTY"] = is_test_efo_pty(committee_data)
    committee_data["isPAC"] = not committee_data["isPTY"]

    # Committee type label
    committee_data["committee_type_label"] = (
        f'{"Party" if committee_data["isPTY"] else "PAC"} - Qualified - Unauthorized'
    )
    # Qualified
    committee_data["qualified"] = True

    # Filing Frequency
    committee_data["filing_frequency"] = "Q"

    # map some fields to their names as prod has them
    committee_data["name"] = committee_data.get("committee_name", None)
    committee_data["treasurer_name_1"] = committee_data.get("treasurer_first_name", None)
    committee_data["treasurer_name_2"] = committee_data.get("treasurer_last_name", None)
    committee_data["treasurer_name_middle"] = committee_data.get(
        "treasurer_middle_name", None
    )
    committee_data["treasurer_street_1"] = committee_data.get("treasurer_str1", None)
    committee_data["treasurer_street_2"] = committee_data.get("treasurer_str2", None)
    committee_data["street_1"] = committee_data.get("committee_str1", None)
    committee_data["street_2"] = committee_data.get("committee_str2", None)
    committee_data["city"] = committee_data.get("committee_city", None)
    committee_data["state"] = committee_data.get("committee_state", None)
    committee_data["zip"] = committee_data.get("committee_zip", None)
    return committee_data


def is_test_efo_pty(committee_data):
    return committee_data.get("committee_type") == "D"


"""
Mock
"""


def get_mocked_committee_emails(committee_id):
    committee = get_mocked_committee_data(committee_id)
    return committee.get("email", "") if committee else ""


def get_mocked_committee_data(committee_id):
    if redis_instance:
        committee_data = redis_instance.get(COMMITTEE_DATA_REDIS_KEY) or ""
        committees = json.loads(committee_data) or []
        committee = next(
            (
                committee
                for committee in committees
                if committee.get("committee_id") == committee_id
            ),
            None,
        )
        return committee
