import requests
import re
from rest_framework.exceptions import ValidationError
from .models import CommitteeAccount, Membership
from rest_framework.status import HTTP_404_NOT_FOUND
from fecfiler import settings
import redis
import json
import structlog

logger = structlog.getLogger(__name__)


COMMITTEE_DATA_REDIS_KEY = "COMMITTEE_DATA"
if settings.FLAG__COMMITTEE_DATA_SOURCE == "MOCKED":
    redis_instance = redis.Redis.from_url(settings.MOCK_OPENFEC_REDIS_URL)
else:
    redis_instance = None


PRODUCTION_PAC_COMMITTEE_TYPES = ["O", "U", "D", "N", "Q", "V", "W"]
PRODUCTION_QUALIFIED_COMMITTEES = ["Q", "W", "Y"]


def check_user_email_matches_committee_email(user_email, committee_emails):
    """
    Check if the provided email matches any of the committee emails.

    Args:
        user_email (str): The email to be checked.
        committee_emails (str): A string containing a list of committee emails separated
        by commas or semicolons.

    Returns:
        True if the user email matches a commmittee email and False otherwise.
    """
    if user_email and committee_emails:
        committee_emails_lowercase = committee_emails.lower()
        committee_emails_list = re.split(r"[;,]", committee_emails_lowercase)
        if user_email.lower() in committee_emails_list:
            return True
    return False


def raise_if_cannot_create_committee_account(committee_id, user):
    user_email = user.email
    try:
        committee_emails = get_committee_emails(committee_id)
    except Exception as e:
        raise ValidationError(
            "Call to retrieve form 1 committee emails failed: " + str(e)
        )
    if not committee_emails:
        raise ValidationError("No form 1 found for committee")

    if not check_user_email_matches_committee_email(user_email, committee_emails):
        raise ValidationError("User email does not match committee email")

    existing_account = CommitteeAccount.objects.filter(committee_id=committee_id).first()
    if existing_account:
        raise ValidationError("Committee account already exists")


def create_committee_account(committee_id, user):
    raise_if_cannot_create_committee_account(committee_id, user)

    account = CommitteeAccount.objects.create(committee_id=committee_id)
    Membership.objects.create(
        committee_account=account,
        user=user,
        role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
    )

    logger.info(
        f"User {user.email} successfully created committee account {committee_id}"
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


def query_fec_api_single(endpoint, params):
    results = query_fec_api(endpoint, params)
    return results[0] if results else None


def query_fec_api(endpoint, params, raise_for_404=True):
    """Shared method to query an EFO API"""

    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"FECfile+ {settings.ENVIRONMENT}",
    }
    response = requests.get(endpoint, headers=headers, params=params)
    if response.status_code != HTTP_404_NOT_FOUND or raise_for_404:
        response.raise_for_status()
    response_data = response.json()
    return response_data.get("results", [])


"""
Production FEC
"""


def get_production_committee_emails(committee_id):
    """
    First query the raw endpoint,
    if no raw data is available, query the processed endpoint
    """
    committee_data = get_raw_committee_data(committee_id)

    if committee_data is None:
        committee_data = get_processed_committee_data(committee_id)

    return committee_data.get("email", None) if committee_data else None


def get_production_committee_data(committee_id):
    """
    First query the processed endpoint,
    if no processed data is available, query the raw endpoint
    """
    # first try processed endpoint
    committee_data = get_processed_committee_data(committee_id)

    if committee_data is None:
        # if no processed data, try raw endpoint
        committee_data = get_raw_committee_data(committee_id)

    return committee_data


def get_processed_committee_data(committee_id):

    params = {
        "api_key": settings.PRODUCTION_OPEN_FEC_API_KEY,
        "committee_id": committee_id,
    }
    committee_data = query_fec_api_single(
        f"{settings.PRODUCTION_OPEN_FEC_API}committee/{committee_id}/", params
    )

    if committee_data:
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


def get_raw_committee_data(committee_id):
    params = {
        "api_key": settings.PRODUCTION_OPEN_FEC_API_KEY,
        "committee_id": committee_id,
    }
    committee_data = query_fec_api_single(
        f"{settings.PRODUCTION_OPEN_FEC_API}efile/form1/", params
    )

    if committee_data:
        """For now we're just using the same logic as alpha"""
        committee_data["isPTY"] = True
        committee_data["isPAC"] = True

        # Committee type label
        committee_data["committee_type_label"] = "Non-qualified"
        # Qualified
        committee_data["qualified"] = False

        # Filing Frequency
        committee_data["filing_frequency"] = "Q"

        committee_data = convert_raw_to_processed(committee_data)

    return committee_data


def is_production_efo_pty(committee_data):
    designation = committee_data.get("designation", None)
    committee_type = committee_data.get("committee_type", None)
    return designation is not None and (committee_type == "Y" or committee_type == "X")


def is_production_efo_pac(committee_data):
    designation = committee_data.get("designation", None)
    committee_type = committee_data.get("committee_type", None)
    return committee_type in PRODUCTION_PAC_COMMITTEE_TYPES or (
        committee_type == "X" and designation == "U"
    )


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
    committee_data = query_fec_api_single(endpoint, params)
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
    if committee_data:

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

        committee_data = convert_raw_to_processed(committee_data)

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


"""
Shared
"""


def convert_raw_to_processed(committee_data):
    """
    Converts field names used in raw endpoint to ones used in processed endpoint
    """

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
