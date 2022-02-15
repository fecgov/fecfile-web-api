import logging
import pytz

from datetime import datetime, timedelta

from django.contrib.auth import authenticate
from django.db import connection
from django.http import JsonResponse
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)

from fecfiler.authentication.models import Account
from fecfiler.authentication.token import jwt_payload_handler
from fecfiler.password_management.otp import TOTPVerification
from fecfiler.password_management.views import (
    token_verification,
    check_madatory_field,
    check_account_exist,
    create_jwt_token,
)
from fecfiler.settings import LOGIN_MAX_RETRY, LOGIN_TIMEOUT_TIME, OTP_DISABLE

jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

logger = logging.getLogger(__name__)


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


def update_counter_val(counter, key):
    try:
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET last_login = %s, login_code_counter = %s
            WHERE secret_key = %s
            """
            cursor.execute(_sql, [datetime.now(), counter + 1, key])
            if cursor.rowcount != 1:
                logger.error("Couldn't reset log-in counter {}", key)
        return cursor.rowcount
    except Exception as e:
        logger.error("exception occurred reset counter for login {}", key)
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


def reset_code_counter(key):
    try:
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET code_generated_counter = 0, last_login = %s, updated_at = %s, login_code_counter = 0
            WHERE secret_key = %s
            """
            cursor.execute(_sql, [datetime.now(), datetime.now(), key])
            if cursor.rowcount != 1:
                logger.error("Reset key failed for key {}", key)
        return cursor.rowcount
    except Exception as e:
        logger.error("exception occurred reset key for key {}", key)
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


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def verify_login(request):
    if request.method == "POST":

        try:
            is_allowed = False
            code = request.data.get("code", None)
            payload = token_verification(request)
            cmte_id = payload.get("committee_id", None)
            email = payload.get("email", None)
            data = {"committee_id": cmte_id, "email": email, "code": code}

            list_mandatory_fields = ["committee_id", "email", "code"]
            check_madatory_field(data, list_mandatory_fields)
            user_list = check_account_exist(cmte_id, email)

            if user_list is None:
                is_allowed = False
                response = {"is_allowed": is_allowed}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
            if not user_list["is_active"]:
                is_allowed = False
                msg = "Account is locked. Please try again after 15 mins or call IT support to unlock account."
                response = {"is_allowed": is_allowed, "msg": msg}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)

            username = user_list["username"]
            key = user_list["secret_key"]
            unix_time = "code_time" in user_list and user_list["code_time"]
            otp_class = TOTPVerification(username)
            token_val = otp_class.verify_token(key, unix_time)

            if code == token_val:
                is_allowed = True
                if not OTP_DISABLE:
                    reset_code_counter(key)
                # call obtain token here and check

                user = Account.objects.filter(username=username).first()
                payload = jwt_payload_handler(user)

                token = jwt_encode_handler(payload)
            else:
                counter = int(user_list["login_code_counter"])
                if counter <= LOGIN_MAX_RETRY - 1:
                    msg = "Invalid attempt"
                    update_counter_val(counter, key)
                    logger.debug(
                        "2 Factor login of Account ID{} failed at {}.".format(
                            user_list["id"], datetime.now()
                        )
                    )
                elif counter >= LOGIN_MAX_RETRY:
                    msg = "Account is locked. Please try again after 15 mins or call IT support to unlock account."
                    lock_account(counter, key)
                    logger.debug(
                        "2 Factor login of Account ID{} failed at {}. Max attempt reached. Account is "
                        "being locked.".format(user_list["id"], datetime.now())
                    )
                is_allowed = False
                response = {"is_allowed": is_allowed, "msg": msg}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)

            logger.debug(
                "2 Factor login of Account ID{} was successful at {}.".format(
                    user_list["id"], datetime.now()
                )
            )
            response = {
                "is_allowed": is_allowed,
                "committee_id": cmte_id,
                "email": email,
                "token": token,
            }
            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.error("exception occurred while verifying code", str(e))
            json_result = {"is_allowed": False}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )


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

            list_mandatory_fields = ["username", "password"]
            check_madatory_field(data, list_mandatory_fields)

            account = authenticate(
                request=request, username=username, password=password
            )

            # fail, bad login info
            if account is None:
                user = Account.objects.filter(username=username).first()
                if user is None:
                    logger.debug(
                        "Attempt to login to Account with username : {} was denied at {}.".format(
                            username, datetime.now()
                        )
                    )
                    return JsonResponse(
                        {
                            "status": "Unauthorized",
                            "message": "ID/Password combination invalid.",
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
                else:
                    current_counter = int(user.login_code_counter)
                    if not user.is_active:
                        if current_counter <= LOGIN_MAX_RETRY - 1:
                            update_last_login_time(username)
                            current_time = datetime.now()
                            logger.debug(
                                "Attempt to login to Account ID{} was denied at {}. Account is locked.".format(
                                    user.id, current_time
                                )
                            )
                            return JsonResponse(
                                {
                                    "status": "Unauthorized",
                                    "message": "Account is locked. Please try again after 15 mins or call IT support to unlock account. ",
                                },
                                status=status.HTTP_403_FORBIDDEN,
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

                                    return JsonResponse(
                                        response, status=status.HTTP_200_OK, safe=False
                                    )

                            current_time = datetime.now()
                            update_last_login_time(username)
                            logger.debug(
                                "Attempt to login to Account ID: {} was denied at {}. Account is locked.".format(
                                    user.id, current_time
                                )
                            )
                            return JsonResponse(
                                {
                                    "status": "Unauthorized",
                                    "message": "Account is locked. Please try again after 15 mins or call IT support to "
                                    "unlock account. ",
                                },
                                status=status.HTTP_403_FORBIDDEN,
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
                        "Attempt to login to Account with username : {} was denied at {}.".format(
                            username, datetime.now()
                        )
                    )
                    return JsonResponse(
                        {
                            "status": "Unauthorized",
                            "message": "ID/Password combination invalid.",
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
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
            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.error("exception occurred while getting account information", str(e))
            json_result = {}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )
