from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, logout, login
from django.core.exceptions import SuspiciousOperation
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from fecfiler.settings import (
    LOGIN_REDIRECT_CLIENT_URL,
    OIDC_RP_CLIENT_ID,
    LOGIN_REDIRECT_URL,
    LOGOUT_REDIRECT_URL,
    OIDC_OP_LOGOUT_ENDPOINT,
    ALTERNATIVE_LOGIN,
    FFAPI_COOKIE_DOMAIN,
    FFAPI_LOGIN_DOT_GOV_COOKIE_NAME,
    FFAPI_TIMEOUT_COOKIE_NAME,
    OIDC_ACR_VALUES,
    OIDC_OP_AUTHORIZATION_ENDPOINT,
    OIDC_MAX_STATES,
)

from rest_framework.response import Response
from rest_framework import status
from urllib.parse import urlencode
from django.http import JsonResponse
import structlog
import time

logger = structlog.get_logger(__name__)

"""
Option for :py:const:`fecfiler.settings.base.ALTERNATIVE_LOGIN`.
See :py:meth:`fecfiler.authentication.views.authenticate_login`
"""
USERNAME_PASSWORD = "USERNAME_PASSWORD"


def handle_valid_login(user):
    logger.debug(f"Successful login: {user}")
    response = HttpResponse()
    return response


def handle_invalid_login(username):
    logger.debug(f"Unauthorized login attempt: {username}")
    return HttpResponse("Unauthorized", status=401)


def delete_user_logged_in_cookies(response):
    response.delete_cookie(FFAPI_LOGIN_DOT_GOV_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie(FFAPI_TIMEOUT_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie("oidc_state")
    response.delete_cookie("csrftoken", domain=FFAPI_COOKIE_DOMAIN)


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
    return HttpResponseRedirect("/")


def add_nonce_to_session(request, state, nonce):
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


@api_view(["GET"])
@require_http_methods(["GET"])
def login_redirect(request):
    redirect = HttpResponseRedirect(LOGIN_REDIRECT_CLIENT_URL)
    redirect.set_cookie(
        FFAPI_LOGIN_DOT_GOV_COOKIE_NAME,
        "true",
        domain=FFAPI_COOKIE_DOMAIN,
        secure=True,
    )
    return redirect


@api_view(["GET"])
@require_http_methods(["GET"])
@permission_classes([])
def logout_redirect(request):
    response = HttpResponseRedirect(LOGIN_REDIRECT_CLIENT_URL)
    delete_user_logged_in_cookies(response)
    return response


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET", "POST"])
def authenticate_login(request):
    endpoint_is_available = ALTERNATIVE_LOGIN == USERNAME_PASSWORD
    if request.method == "GET":
        return JsonResponse({"endpoint_available": endpoint_is_available})

    if not endpoint_is_available:
        return JsonResponse(status=405, safe=False)

    username = request.data.get("username", None)
    password = request.data.get("password", None)
    account = authenticate(
        request=request, username=username, password=password
    )  # Returns an account if the username is found and the password is valid

    if account:
        login(request, account)
        return handle_valid_login(account)
    else:
        return handle_invalid_login(username)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET"])
def authenticate_logout(request):
    logout(request)
    response = Response({}, status=status.HTTP_204_NO_CONTENT)
    delete_user_logged_in_cookies(response)
    return response


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET"])
def oidc_authenticate(request):
    state = get_random_string(32)
    nonce = get_random_string(32)
    params = {
        "acr_values": OIDC_ACR_VALUES,
        "client_id": OIDC_RP_CLIENT_ID,
        "prompt": "select_account",
        "response_type": "code",
        "redirect_uri": request.build_absolute_uri(reverse("oidc_callback")),
        "scope": "openid email",
        "state": state,
        "nonce": nonce,
    }
    add_nonce_to_session(request, state, nonce)
    query = urlencode(params)
    redirect_url = "{url}?{query}".format(url=OIDC_OP_AUTHORIZATION_ENDPOINT, query=query)
    response = HttpResponseRedirect(redirect_url)
    response.set_signed_cookie("oidc_state", state)
    return response


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
@require_http_methods(["GET"])
def oidc_callback(request):
    if (
        "error" not in request.query_params
        and "code" in request.query_params
        and "state" in request.query_params
    ):
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
            return HttpResponseRedirect(LOGIN_REDIRECT_URL)

    return handle_oidc_callback_error(request)


@api_view(["GET"])
@require_http_methods(["GET"])
def oidc_logout(request):
    logout_url = LOGOUT_REDIRECT_URL
    if request.user.is_authenticated:
        params = {
            "client_id": OIDC_RP_CLIENT_ID,
            "post_logout_redirect_uri": LOGOUT_REDIRECT_URL,
            "state": request.get_signed_cookie("oidc_state"),
        }
        query = urlencode(params)
        op_logout_url = OIDC_OP_LOGOUT_ENDPOINT
        logout_url = f"{op_logout_url}?{query}"
        logout(request)
    return HttpResponseRedirect(logout_url)
