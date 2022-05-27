from django.contrib.auth import authenticate, logout
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from rest_framework import permissions, status, views, viewsets
from rest_framework.response import Response
import pytz
import jwt
import time
from django.db import connection
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


def update_last_login_time(username):
    try:
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET last_login = %s
            WHERE username = %s AND delete_ind !='Y'
            """
            cursor.execute(_sql, [datetime.now(), username])
            if cursor.rowcount != 1:
                logger.error("Couldn't update login time")
        return cursor.rowcount
    except Exception as e:
        logger.error("exception occurred while updating last login time")
        raise e


def get_last_login_time(username):
    try:
        with connection.cursor() as cursor:
            _sql = """
            select last_login from public.authentication_account
            where username = %s AND delete_ind !='Y'
            """
            cursor.execute(_sql, [username])
            update_time = cursor.fetchone()[0]

        return update_time
    except Exception as e:
        raise e


def update_counter(counter, username):
    try:
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET last_login = %s, login_code_counter = %s
            WHERE username = %s AND delete_ind !='Y'
            """
            cursor.execute(_sql, [datetime.now(), counter + 1, username])
            if cursor.rowcount != 1:
                logger.error("Couldn't reset log-in counter")
        return cursor.rowcount
    except Exception as e:
        logger.error("exception occurred reset counter for login")
        raise e


def lock_account(counter, key):
    try:
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET is_active = %s, last_login = %s, login_code_counter = %s
            WHERE secret_key = %s AND delete_ind !='Y'
            """
            cursor.execute(_sql, ["false", datetime.now(), counter + 1, key])
            if cursor.rowcount != 1:
                logger.error("Lock account failed for key {}", key)
        return cursor.rowcount
    except Exception as e:
        logger.error("exception occurred locking account for key {}", key)
        raise e


def activate_account(username):
    try:
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET last_login = %s, is_active = %s
            WHERE username = %s AND delete_ind !='Y'
            """
            cursor.execute(_sql, [datetime.now(), "true", username])
            if cursor.rowcount != 1:
                logger.error("Couldn't update login time")
        return cursor.rowcount
    except Exception as e:
        logger.error("exception occurred while updating last login time")
        raise e


def create_jwt_token(email, cmte_id):
    now = int(time.time())
    token = jwt.encode(
        {"email": email, "committee_id": cmte_id, "exp": now + JWT_PASSWORD_EXPIRY},
        SECRET_KEY,
        algorithm="HS256",
    ).decode("utf-8")
    logger.debug(f"token created: {token}")
    logger.debug(f"using sk: {hash(SECRET_KEY)}")
    logger.debug(f"email: {email} committee_id: {cmte_id} exp: {JWT_PASSWORD_EXPIRY}")
    return token


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def authenticate_login(request):
    if request.method == "POST":

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
                    logger.info(
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
                            logger.info(
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

                    logger.info(
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

            is_allowed = True
            update_last_login_time(username)
            token = create_jwt_token(account.email, account.cmtee_id)
            logger.debug(
                "Attempt to login to Account ID :{} was successful at {}.".format(
                    account.id, datetime.now()
                )
            )

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
