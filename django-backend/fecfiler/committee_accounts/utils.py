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
if settings.FLAG__COMMITTEE_DATA_SOURCE == "MOCKED" or settings.UNIT_TESTING_ENVIRONMENT:
    redis_instance = redis.Redis.from_url(settings.MOCK_OPENFEC_REDIS_URL)
else:
    redis_instance = None


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

    f1 = get_recent_f1(committee_id)

    f1_emails = (f1 or {}).get("email")
    failure_reason = check_email_match(email, f1_emails)

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
            return get_committee_account_data_from_efo(committee_id)
        case "TEST":
            return get_committee_account_data_from_test_efo(committee_id)
        case "MOCKED":
            return get_committee_account_data_from_redis(committee_id)
        case _:
            return get_response_for_bad_committee_source_config()


def get_committee_account_data_from_efo(committee_id):
    headers = {"Content-Type": "application/json"}
    return requests.get(
        f"{settings.FEC_API}committee/{committee_id}/?api_key={settings.FEC_API_KEY}",
        headers=headers
    ).json()


def get_committee_account_data_from_test_efo(committee_id):
    headers = {"Content-Type": "application/json"}
    params = {
        "api_key": settings.FEC_API_KEY,
        "committee_id": committee_id,
    }
    endpoint = f"{settings.FEC_API_STAGE}efile/test-form1/"
    response = requests.get(endpoint, headers=headers, params=params)
    response_data = response.json()
    results = response_data.get('results', [])
    if results:
        results[0]['name'] = results[0].get('committee_name', None)

    return {
        'api_version': response_data.get('api_version', None),
        'results': response_data.get('results', [])[:1],
    }


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
        if committee:
            # rename key so we can use same mock data for both
            # query_filings and committee details endpoints
            committee['name'] = committee.pop('committee_name')
            return {  # same as api.open.fec.gov
                "api_version": "1.0",
                "results": [committee],
                "pagination": {
                    "pages": 1,
                    "per_page": 20,
                    "count": 1,
                    "page": 1,
                },
            }
        return None


def get_recent_f1(committee_id):
    match settings.FLAG__COMMITTEE_DATA_SOURCE:
        case "PRODUCTION":
            return get_recent_f1_from_efo(committee_id)
        case "TEST":
            return get_recent_f1_from_test_efo(committee_id)
        case "MOCKED":
            return get_recent_f1_from_redis(committee_id)
        case _:
            return get_response_for_bad_committee_source_config()


def get_recent_f1_from_efo(committee_id):
    headers = {"Content-Type": "application/json"}
    params = {
        "api_key": settings.FEC_API_KEY,
        "committee_id": committee_id,
    }
    endpoints = [
        f"{settings.FEC_API}efile/form1/",
        f"{settings.FEC_API}committee/{committee_id}/"
    ]
    for endpoint in endpoints:
        response = requests.get(endpoint, headers=headers, params=params).json()
        if response.get('results'):
            return response['results'][0]


def get_recent_f1_from_test_efo(committee_id):
    headers = {"Content-Type": "application/json"}
    params = {
        "api_key": settings.FEC_API_KEY,
        "committee_id": committee_id,
    }
    endpoint = f"{settings.FEC_API_STAGE}efile/test-form1/"
    response = requests.get(endpoint, headers=headers, params=params).json()
    if response.get('results'):
        return response['results'][0]


def get_recent_f1_from_redis(committee_id):
    if redis_instance:
        committee_data = redis_instance.get(COMMITTEE_DATA_REDIS_KEY) or ""
        committees = json.loads(committee_data) or []
        return next(
            committee
            for committee in committees
            if committee.get("committee_id") == committee_id
        )
