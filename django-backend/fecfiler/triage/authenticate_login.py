from django.contrib.auth import authenticate
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
import pytz
from django.db import connection
from fecfiler.authentication.models import Account
from datetime import datetime, timedelta
from django.http import JsonResponse
from fecfiler.password_management.views import create_jwt_token
from fecfiler.settings import LOGIN_MAX_RETRY, LOGIN_TIMEOUT_TIME
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
                        status=401,
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
                                        response, status=200, safe=False
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
                        "Attempt to login to Account with username : {} was denied at {}.".format(
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
