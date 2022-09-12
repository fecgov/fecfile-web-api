from django.contrib.auth import authenticate, logout
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from rest_framework import permissions, status, views, viewsets
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
import pytz
import jwt
import time
from django.db import connection

from fecfiler.authentication.token import jwt_payload_handler
from .models import Account
from datetime import datetime, timedelta
from django.http import JsonResponse
from .serializers import AccountSerializer
from .permissions import IsAccountOwner
from fecfiler.settings import (
    LOGIN_MAX_RETRY,
    LOGIN_TIMEOUT_TIME,
    SECRET_KEY,
    JWT_PASSWORD_EXPIRY,
)
import logging

logger = logging.getLogger(__name__)


def update_last_login_time(account):
    account.last_login = datetime.now()
    account.save()


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def authenticate_two_login_boogaloo(request):
    username = request.data.get("username", None)
    password = request.data.get("password", None)

    account = authenticate(
        request=request, username=username, password=password
    ) ## Returns an account if the username is found and the password is valid
    
    response = JsonResponse(
        {
            "status": "Unauthorized",
            "message": "ID/Password combination invalid.",
        },
        status=401,
    )

    if account:
        return handle_valid_login(account)

    return response

def handle_valid_login(account):
    update_last_login_time(account)
    is_allowed = True
    payload = jwt_payload_handler(account)
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    token = jwt_encode_handler(payload)

    logger.debug("Successful login: {}".format(account))
    return JsonResponse({
        "is_allowed": is_allowed,
        "committee_id": account.cmtee_id,
        "email": account.email,
        "token": token,
    }, status=200, safe=False)

"""
@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def authenticate_login(request):
    try:
        data = request.data
        username = data.get("username", None)
        password = data.get("password", None)
        is_allowed = False

        account = authenticate(
            request=request, username=username, password=password
        )

        # fail, bad login info
        if account is None:
            user = Account.objects.filter(username=username).first()
            if user is None:
                logger.debug(
                    "Attempt to login to Account "
                    "with username : {} was denied at {}.".format(
                        username, datetime.now()
                    )
                )
                return JsonResponse(
                    {
                        "status": "Unauthorized",
                        "message": "ID/Password combination invalid.",
                    },
                    status=401,
                )
            else:
                current_counter = int(user.login_code_counter)
                if not user.is_active:
                    if current_counter <= LOGIN_MAX_RETRY - 1:
                        update_last_login_time(username)
                        current_time = datetime.now()
                        logger.debug(
                            "Attempt to login to Account ID{} was "
                            "denied at {}. Account is locked.".format(
                                user.id, current_time
                            )
                        )
                        msg = "Account is locked. Please try again after 15"
                        msg += " mins or call IT support to unlock account. "
                        return JsonResponse(
                            {
                                "status": "Unauthorized",
                                "message": msg,
                            },
                            status=403,
                        )

                    elif current_counter >= LOGIN_MAX_RETRY:
                        last_login_time = get_last_login_time(username)
                        est = pytz.timezone("US/Eastern")
                        current_time_est = datetime.now(est)
                        current_time_est1 = current_time_est.replace(tzinfo=None)
                        upper_limit = last_login_time + timedelta(
                            minutes=LOGIN_TIMEOUT_TIME
                        )
                        upper_limit1 = upper_limit.replace(tzinfo=None)
                        if upper_limit1 < current_time_est1:
                            activate_account(username)
                            account = authenticate(
                                request=request,
                                username=username,
                                password=password,
                            )
                            if account is not None:
                                is_allowed = True
                                update_last_login_time(username)
                                token = create_jwt_token(
                                    account.email, account.cmtee_id
                                )
                                logger.debug(
                                    "Attempt to login to Account ID :{} "
                                    "was successful at {}.".format(
                                        account.id, datetime.now()
                                    )
                                )
                                response = {
                                    "is_allowed": is_allowed,
                                    "committee_id": account.cmtee_id,
                                    "email": account.email,
                                    "token": token,
                                }

                                return JsonResponse(
                                    response, status=200, safe=False
                                )

                        current_time = datetime.now()
                        update_last_login_time(username)
                        logger.debug(
                            "Attempt to login to Account ID: {} was"
                            " denied at {}. Account is locked.".format(
                                user.id, current_time
                            )
                        )
                        msg = "Account is locked. Please try again after 15"
                        msg += " mins or call IT support to unlock account. "
                        return JsonResponse(
                            {
                                "status": "Unauthorized",
                                "message": msg,
                            },
                            status=403,
                        )
                if current_counter <= LOGIN_MAX_RETRY - 1:
                    user.login_code_counter = current_counter + 1
                    update_counter(current_counter, username)
                elif current_counter >= LOGIN_MAX_RETRY:
                    last_login_time = get_last_login_time(username)
                    est = pytz.timezone("US/Eastern")
                    current_time_est = datetime.now(est)
                    current_time_est1 = current_time_est.replace(tzinfo=None)
                    upper_limit = last_login_time + timedelta(
                        minutes=LOGIN_TIMEOUT_TIME
                    )
                    upper_limit1 = upper_limit.replace(tzinfo=None)
                    if upper_limit1 < current_time_est1:
                        activate_account(username)
                    else:
                        lock_account(current_counter, user.secret_key)

                logger.debug(
                    "Attempt to login to Account with username:"
                    " {} was denied at {}.".format(username, datetime.now())
                )
                return JsonResponse(
                    {
                        "status": "Unauthorized",
                        "message": "ID/Password combination invalid.",
                    },
                    status=401,
                )

        logger.debug(
            "Attempt to login to Account ID :{} was successful at {}.".format(
                account.id, datetime.now()
            )
        )

        ##update_last_login_time(username)
        a = Account.objects.all().get(username=username)
        logger.debug(account, a)
        update_last_login_time2(a)
        is_allowed = True
        user = Account.objects.filter(username=username).first()
        payload = jwt_payload_handler(user)
        from rest_framework_jwt.settings import api_settings
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        token = jwt_encode_handler(payload)

        response = {
            "is_allowed": is_allowed,
            "committee_id": account.cmtee_id,
            "email": account.email,
            "token": token,
        }

        return JsonResponse(response, status=200, safe=False)
    except Exception as e:
        logger.error("exception occurred while getting account information", str(e))
        json_result = {}
        return JsonResponse(json_result, status=400, safe=False)
"""

class AccountViewSet(viewsets.ModelViewSet):
    lookup_field = "username"

    serializer_class = AccountSerializer

    def get_queryset(self):
        queryset = Account.objects.all()
        queryset = queryset.filter(self.request.user)
        serializer_class = AccountSerializer(Account, many=True)
        return JsonResponse(serializer_class.data, safe=False)

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return (permissions.AllowAny(),)
        if self.request.method == "POST":
            return (permissions.AllowAny(),)
        return permissions.IsAuthenticated(), IsAccountOwner()

    def create(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            Account.objects.create_user(**serializer.validated_data)
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

        return Response(
            {
                "status": "Bad request",
                "message": "Account could not be created with received data.",
                "details": str(serializer.errors),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class LogoutView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        logout(request)
        return Response({}, status=status.HTTP_204_NO_CONTENT)
