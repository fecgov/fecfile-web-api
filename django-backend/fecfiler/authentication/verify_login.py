from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from .otp import TOTPVerification, OTP_DISABLE
from .token import token_verification
from rest_framework import status
from rest_framework_jwt.settings import api_settings
from django.db import connection
from .models import Account
from datetime import datetime
from django.http import JsonResponse
from fecfiler.settings import LOGIN_MAX_RETRY

from .token import jwt_payload_handler
import logging

logger = logging.getLogger(__name__)

jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


def reset_code_counter(key):
    try:
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET code_generated_counter = 0, last_login = %s,
            updated_at = %s, login_code_counter = 0
            WHERE secret_key = %s
            """
            cursor.execute(_sql, [datetime.now(), datetime.now(), key])
            if cursor.rowcount != 1:
                logger.error("Reset key failed for key {}", key)
        return cursor.rowcount
    except Exception as e:
        logger.error("exception occurred reset key for key {}", key)
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


def check_account_exist(cmte_id, email):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """SELECT json_agg(t) FROM
            (Select * from public.authentication_account
            WHERE cmtee_id = %s AND lower(email) = lower(%s)
            AND status ='Registered' AND delete_ind !='Y') t"""
            cursor.execute(_sql, [cmte_id, email])
            user_list = cursor.fetchone()
            merged_list = []
            for dictL in user_list:
                merged_list = dictL[0]

        return merged_list
    except Exception as e:
        logger.debug("Exception occurred while checking user already present", str(e))
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

            user_list = check_account_exist(cmte_id, email)

            if user_list is None:
                is_allowed = False
                response = {"is_allowed": is_allowed}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
            if not user_list["is_active"]:
                is_allowed = False
                msg = "Account is locked. Please try again after 15 mins"
                msg += " or call IT support to unlock account."
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
                    msg = "Account is locked. Please try again after 15 mins"
                    msg += " or call IT support to unlock account."
                    lock_account(counter, key)
                    logger.debug(
                        "2 Factor login of Account ID{} failed at {}. "
                        "Max attempt reached. Account is "
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
