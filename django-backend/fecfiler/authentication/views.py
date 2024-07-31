from django.http import HttpResponse
from django.contrib.auth import authenticate, logout, login
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from fecfiler.settings import (
    ALTERNATIVE_LOGIN,
)

from fecfiler.authentication.utils import delete_user_logged_in_cookies

from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import structlog


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
