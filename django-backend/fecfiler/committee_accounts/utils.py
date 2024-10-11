import logging
import requests
import re
from django.db import connection
from rest_framework.exceptions import ValidationError
from .models import CommitteeAccount, Membership
from fecfiler.mock_openfec.mock_endpoints import recent_f1
from fecfiler.transactions.models import (
    Transaction,
    get_committee_view_name,
)
from fecfiler.settings import (
    FEC_API,
    FEC_API_KEY,
    MOCK_OPENFEC_REDIS_URL,
    CREATE_COMMITTEE_ACCOUNT_ALLOWED_EMAIL_LIST,
)

logger = logging.getLogger(__name__)


def retrieve_recent_f1(committee_id):
    """Gets the most recent F1 filing
    First checks the realtime enpdpoint for a recent F1 filing.  If none is found,
    a request is made to a different endpoint that is updated nightly.
    The realtime endpoint will have more recent filings, but does not provide
    filings older than 6 months. The other endpoint returns a committee's current data
    informed by their most recent F1 and F2 filings."""
    headers = {"Content-Type": "application/json"}
    params = {
        "api_key": FEC_API_KEY,
        "committee_id": committee_id,
    }
    endpoints = [
        f"{FEC_API}efile/form1/",
        f"{FEC_API}committee/{committee_id}/",
    ]
    for endpoint in endpoints:
        response = requests.get(endpoint, headers=headers, params=params).json()
        results = response["results"]
        if len(results) > 0:
            return results[0]


def check_email_can_create_committee_account(email):
    """
    Check if the provided email is allowed to create a committee based on domain
    or exception list.

    Args:
        email (str): The email to be checked.

    Returns:
        boolean True if email is allowed, False otherwise.
    """
    allowed_domains = ["fec.gov"]
    allowed_emails = CREATE_COMMITTEE_ACCOUNT_ALLOWED_EMAIL_LIST
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

    if MOCK_OPENFEC_REDIS_URL:
        f1 = recent_f1(committee_id)
    else:
        f1 = retrieve_recent_f1(committee_id)

    f1_emails = (f1 or {}).get("email")
    failure_reason = check_email_match(email, f1_emails)

    existing_account = CommitteeAccount.objects.filter(committee_id=committee_id).first()
    if existing_account:
        failure_reason = f"Committee account {committee_id} already created"

    if not check_email_can_create_committee_account(email):
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
