"""
This source code has been copied from the mozilla-django-oidc
project:
https://mozilla-django-oidc.readthedocs.io/en/stable/index.html#
https://github.com/mozilla/mozilla-django-oidc/tree/main

It has been modified in places to meet the needs of the project and
the original version can be found on Github:
https://github.com/mozilla/mozilla-django-oidc/blob/main/mozilla_django_oidc/utils.py
https://github.com/mozilla/mozilla-django-oidc/blob/main/mozilla_django_oidc/views.py
"""

import time
import base64
import hashlib

from django.core.exceptions import SuspiciousOperation
from django.contrib.auth import logout, authenticate, login


from fecfiler.settings import (
    FFAPI_COOKIE_DOMAIN,
    FFAPI_TIMEOUT_COOKIE_NAME,
    OIDC_MAX_STATES,
)
import structlog

logger = structlog.getLogger(__name__)


def handle_oidc_callback_request(request):
    state = request.query_params.get("state")
    if (
        "oidc_states" not in request.session
        or state not in request.session["oidc_states"]
    ):
        msg = "OIDC callback state not found in session `oidc_states`!"
        raise SuspiciousOperation(msg)
    # Get the noncefrom the dictionary for further processing
    # and delete the entry to prevent replay attacks.
    nonce = request.session["oidc_states"][state]["nonce"]
    del request.session["oidc_states"][state]

    # Authenticating is slow, so save the updated oidc_states.
    request.session.save()

    kwargs = {
        "request": request,
        "nonce": nonce,
    }

    user = authenticate(**kwargs)
    if user and user.is_active:
        login(request, user)


def handle_oidc_callback_error(request):
    # Delete the state entry also for failed authentication attempts
    # to prevent replay attacks.
    if (
        "state" in request.GET
        and "oidc_states" in request.session
        and request.GET["state"] in request.session["oidc_states"]
    ):
        del request.session["oidc_states"][request.GET["state"]]
        request.session.save()

    # Make sure the user doesn't get to continue to be logged in
    if request.user.is_authenticated:
        logout(request)
    assert not request.user.is_authenticated


def add_oidc_nonce_to_session(request, state, nonce):
    if "oidc_states" not in request.session or not isinstance(
        request.session["oidc_states"], dict
    ):
        request.session["oidc_states"] = {}

    # Make sure that the State/Nonce dictionary in the session does not get too big.
    # If the number of State/Nonce combinations reaches a certain threshold,
    # remove the oldest state by finding out which element has the oldest "add_on" time.
    if len(request.session["oidc_states"]) >= OIDC_MAX_STATES:
        logger.info(
            'User has more than {} "oidc_states" in their session, '
            "deleting the oldest one!".format(OIDC_MAX_STATES)
        )
        oldest_state = None
        oldest_added_on = time.time()
        for item_state, item in request.session["oidc_states"].items():
            if item["added_on"] < oldest_added_on:
                oldest_state = item_state
                oldest_added_on = item["added_on"]
        if oldest_state:
            del request.session["oidc_states"][oldest_state]
    request.session["oidc_states"][state] = {
        "nonce": nonce,
        "added_on": time.time(),
    }


def delete_user_logged_in_cookies(response):
    response.delete_cookie(FFAPI_TIMEOUT_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie("csrftoken", domain=FFAPI_COOKIE_DOMAIN)


# based on idp impl:
# https://github.com/18F/identity-idp/blob/799fc62621a30c54e7edba17e376d94606d0c956/app/services/id_token_builder.rb#L69
def idp_base64_encode_left_128_bits_of_str(target_string: str):
    digest = hashlib.sha256(target_string.encode()).digest()
    return base64.urlsafe_b64encode(digest[:16]).rstrip(b"=").decode()
