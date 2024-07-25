"""
This source code has been copied from the mozilla-django-oidc
project:
https://mozilla-django-oidc.readthedocs.io/en/stable/index.html#
https://github.com/mozilla/mozilla-django-oidc/tree/main

It has been modified in places to meet the needs of the project and
the original version can be found on Github:
https://github.com/mozilla/mozilla-django-oidc/blob/main/mozilla_django_oidc/views.py
"""

from django.http import HttpResponseRedirect
from django.contrib.auth import logout
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
    LOGOUT_REDIRECT_URL,
    OIDC_OP_LOGOUT_ENDPOINT,
    FFAPI_COOKIE_DOMAIN,
    FFAPI_LOGIN_DOT_GOV_COOKIE_NAME,
    OIDC_ACR_VALUES,
    OIDC_OP_AUTHORIZATION_ENDPOINT,
)
from fecfiler.authentication.utils import delete_user_logged_in_cookies

from .utils import (
    add_oidc_nonce_to_session,
    handle_oidc_callback_error,
    handle_oidc_callback_request,
)

from urllib.parse import urlencode
import structlog

logger = structlog.get_logger(__name__)


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
    add_oidc_nonce_to_session(request, state, nonce)
    query = urlencode(params)
    redirect_url = "{url}?{query}".format(url=OIDC_OP_AUTHORIZATION_ENDPOINT, query=query)
    response = HttpResponseRedirect(redirect_url)
    response.set_signed_cookie("oidc_state", state, secure=True, httponly=True)
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
        return handle_oidc_callback_request(request)
    return handle_oidc_callback_error(request)


@api_view(["GET"])
@require_http_methods(["GET"])
def oidc_logout(request):
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
    return HttpResponseRedirect(logout_url or LOGOUT_REDIRECT_URL)
