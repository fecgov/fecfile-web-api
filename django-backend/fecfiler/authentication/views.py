from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, logout, login
from django.views.decorators.http import require_http_methods
from urllib.parse import quote_plus
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from fecfiler.settings import (
    LOGIN_REDIRECT_CLIENT_URL,
    FFAPI_LOGIN_DOT_GOV_COOKIE_NAME,
    FFAPI_FIRST_NAME_COOKIE_NAME,
    FFAPI_LAST_NAME_COOKIE_NAME,
    FFAPI_EMAIL_COOKIE_NAME,
    FFAPI_SECURITY_CONSENT_DATE_COOKIE_NAME,
    FFAPI_COOKIE_DOMAIN,
    OIDC_RP_CLIENT_ID,
    LOGOUT_REDIRECT_URL,
    OIDC_OP_LOGOUT_ENDPOINT,
    ALTERNATIVE_LOGIN,
)

from rest_framework.response import Response
from rest_framework import status
from urllib.parse import urlencode
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

"""
Option for :py:const:`fecfiler.settings.base.ALTERNATIVE_LOGIN`.
See :py:meth:`fecfiler.authentication.views.authenticate_login`
"""
USERNAME_PASSWORD = "USERNAME_PASSWORD"


def login_dot_gov_logout(request):
    client_id = OIDC_RP_CLIENT_ID
    post_logout_redirect_uri = LOGOUT_REDIRECT_URL
    state = request.get_signed_cookie("oidc_state")

    params = {
        "client_id": client_id,
        "post_logout_redirect_uri": post_logout_redirect_uri,
        "state": state,
    }
    query = urlencode(params)
    op_logout_url = OIDC_OP_LOGOUT_ENDPOINT
    redirect_url = "{url}?{query}".format(url=op_logout_url, query=query)

    return redirect_url


def generate_username(uuid):
    return uuid


def handle_valid_login(user):
    logger.debug("Successful login: {}".format(user))
    user.login_dot_gov = False
    response = HttpResponse()
    set_user_logged_in_cookies_for_user(response, user)
    return response


def handle_invalid_login(username):
    logger.debug("Unauthorized login attempt: {}".format(username))
    return HttpResponse('Unauthorized', status=401)


def set_user_logged_in_cookies_for_user(response, user):
    if user.first_name:
        response.set_cookie(
            FFAPI_FIRST_NAME_COOKIE_NAME,
            quote_plus(user.first_name),
            domain=FFAPI_COOKIE_DOMAIN,
            secure=True,
        )
    if user.last_name:
        response.set_cookie(
            FFAPI_LAST_NAME_COOKIE_NAME,
            quote_plus(user.last_name),
            domain=FFAPI_COOKIE_DOMAIN,
            secure=True,
        )
    if user.email:
        response.set_cookie(
            FFAPI_EMAIL_COOKIE_NAME,
            quote_plus(user.email),
            domain=FFAPI_COOKIE_DOMAIN,
            secure=True,
        )
    response.set_cookie(
        FFAPI_LOGIN_DOT_GOV_COOKIE_NAME,
        "true" if user.login_dot_gov else "false",
        domain=FFAPI_COOKIE_DOMAIN,
        secure=True,
    )
    response.set_cookie(
        FFAPI_SECURITY_CONSENT_DATE_COOKIE_NAME,
        user.security_consent_date,
        domain=FFAPI_COOKIE_DOMAIN,
        secure=True,
    )


def delete_user_logged_in_cookies(response):
    response.delete_cookie(FFAPI_LOGIN_DOT_GOV_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie(FFAPI_FIRST_NAME_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie(FFAPI_LAST_NAME_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie(FFAPI_SECURITY_CONSENT_DATE_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie(FFAPI_EMAIL_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie("oidc_state", domain=FFAPI_COOKIE_DOMAIN)
    response.delete_cookie("csrftoken", domain=FFAPI_COOKIE_DOMAIN)


@api_view(["GET"])
@require_http_methods(["GET"])
def login_redirect(request):
    request.user.login_dot_gov = True
    redirect = HttpResponseRedirect(LOGIN_REDIRECT_CLIENT_URL)
    set_user_logged_in_cookies_for_user(redirect, request.user)
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
