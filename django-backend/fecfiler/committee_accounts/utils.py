import logging
import requests
import re
from django.db import connection
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import CommitteeAccount, Membership
from fecfiler.transactions.models import (
    Transaction,
    get_committee_view_name,
)
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


def get_response_for_bad_committee_source_config():
    error_message = f"""FLAG__COMMITTEE_DATA_SOURCE improperly configured: {
        settings.FLAG__COMMITTEE_DATA_SOURCE
    }"""
    response = Response()
    response.status_code = 500
    response.content = error_message
    logger.exception(Exception(error_message))
    return response


def check_email_allowed_to_create_committee_account(email):
    """
    Check if the provided email is allowed to create a committee based on domain
    or exception list.

    Args:
        email (str): The email to be checked.

    Returns:
        boolean True if email is allowed, False otherwise.
    """
    allowed_domains = ["fec.gov"]
    allowed_emails = settings.CREATE_COMMITTEE_ACCOUNT_ALLOWED_EMAIL_LIST
    if email:
        email_to_check = email.lower()
        split_email = email_to_check.split("@")
        if len(split_email) == 2:
            domain = split_email[1]
            if domain and domain in allowed_domains:
                return True
        if email_to_check in allowed_emails:
            return True
    return False


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

    committee = get_committee_account_data(committee_id)
    committee_emails = committee.get("email", "")

    failure_reason = check_email_match(email, committee_emails)

    existing_account = CommitteeAccount.objects.filter(committee_id=committee_id).first()
    if existing_account:
        failure_reason = f"Committee account {committee_id} already created"

    if not check_email_allowed_to_create_committee_account(email):
        failure_reason = f"Email {email} is not allowed to create a committee account"

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

    create_committee_view(account.id)
    return account


def create_committee_view(committee_uuid):
    view_name = get_committee_view_name(committee_uuid)
    with connection.cursor() as cursor:
        sql, params = (
            Transaction.objects.transaction_view()
            .filter(committee_account_id=committee_uuid)
            .query.sql_with_params()
        )
        definition = cursor.mogrify(sql, params).decode("utf-8")
        cursor.execute(f"CREATE OR REPLACE VIEW {view_name} as {definition}")


def get_committee_account_data(committee_id):
    match settings.FLAG__COMMITTEE_DATA_SOURCE:
        case "PRODUCTION":
            committee = get_committee_account_data_from_efo(committee_id)
        case "TEST":
            committee = get_committee_account_data_from_test_efo(committee_id)
        case "MOCKED":
            committee = get_committee_account_data_from_redis(committee_id)
    return committee


def get_committee_account_data_from_efo(committee_id):
    # To be verified in https://fecgov.atlassian.net/browse/FECFILE-1706
    committee_data = query_production_efo(committee_id)
    if committee_data == None:
        return None

    # Committee Type Label
    committee_data["committee_type_label"] = committee_data.get(
        "committee_type_full", None
    )

    # PAC/PTY
    committee_data["isPTY"] = is_production_efo_PTY(committee_data)
    committee_data["isPAC"] = is_production_efo_PAC(committee_data)

    # Qualified
    committee_data["qualified"] = (
        committee_data.get("committee_type") in PRODUCTION_QUALIFIED_COMMITTEES
    )

    return committee_data


def is_production_efo_PTY(committee_data):
    designation = committee_data.get("designation", None)
    committee_type = committee_data.get("committee_type", None)
    return designation != None and (
        committee_type == "Y" or (committee_type == "X" and designation != "U")
    )


def is_production_efo_PAC(committee_data):
    return committee_data.get("committee_type") in PRODUCTION_PAC_COMMITTEE_TYPES


def query_production_efo(committee_id):
    raw_and_processed_endpoints = [
        f"{settings.PRODUCTION_OPEN_FEC_API}efile/form1/",
        f"{settings.PRODUCTION_OPEN_FEC_API}committee/{committee_id}/",
    ]

    params = {
        "api_key": settings.PRODUCTION_OPEN_FEC_API_KEY,
        "committee_id": committee_id,
    }
    for endpoint in raw_and_processed_endpoints:
        committee_data = query_efo_api(endpoint, params)
        if committee_data:
            return committee_data
    return None


def query_efo_api(endpoint, params):
    headers = {"Content-Type": "application/json"}
    response = requests.get(endpoint, headers=headers, params=params)
    response_data = response.json()
    committee_results = response_data.get("results", [])
    return committee_results[0] if committee_results else None


def get_committee_account_data_from_test_efo(committee_id):
    params = {
        "api_key": settings.STAGE_OPEN_FEC_API_KEY,
        "committee_id": committee_id,
    }
    endpoint = f"{settings.STAGE_OPEN_FEC_API}efile/test-form1/"
    committee_data = query_efo_api(endpoint, params)
    if committee_data == None:
        return None

    # PAC/PTY
    committee_data["isPTY"] = is_test_efo_PTY(committee_data)
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


def is_test_efo_PTY(committee_data):
    return committee_data.get("committee_type") == "D"


def get_committee_account_data_from_redis(committee_id):
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
