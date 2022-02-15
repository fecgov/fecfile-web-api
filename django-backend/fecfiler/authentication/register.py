import boto3
import logging
import uuid

from rest_framework.response import Response
from botocore.exceptions import ClientError
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.http import JsonResponse
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)

from fecfiler.core.views import check_null_value, NoOPError
from fecfiler.password_management.otp import TOTPVerification
from fecfiler.password_management.views import (
    check_madatory_field,
    create_jwt_token,
    send_email,
    send_text,
    send_call,
    token_verification,
    reset_code_counter,
    create_password_jwt_token,
)
from fecfiler.settings import REGISTER_USER_URL, OTP_DISABLE

logger = logging.getLogger(__name__)


def send_email_register(user_data, cmte_id, register_url_token):
    SENDER = "donotreply@fec.gov"
    RECIPIENT = []
    data = {}
    name = ""
    RECIPIENT.append("%s" % user_data.get("email"))

    SUBJECT = "Register Account"

    if check_null_value(user_data.get("first_name")) and check_null_value(
        user_data.get("last_name")
    ):
        name = user_data.get("first_name") + " " + user_data.get("last_name")
    elif check_null_value(user_data.get("first_name")) and not check_null_value(
        user_data.get("last_name")
    ):
        name = user_data.get("first_name")
    elif not check_null_value(user_data.get("first_name")) and check_null_value(
        user_data.get("last_name")
    ):
        name = user_data.get("last_name")

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = (
        "Dear User /"
        + name
        + "/"
        + "\r\nYou have been added to NextGen for Committee ID:"
        + cmte_id
        + "as the role of:"
        + "\r\n"
        + user_data.get("role")
        + "\r\n Please create your Account by selecting the link below."
        + "\r\n"
        + REGISTER_USER_URL
        + register_url_token
        + "\r\nPlease do not reply to this message"
        "\r\nThis email was sent by FEC.gov. If you are receiving this email in error or have any "
        "questions, "
        "please contact the FEC Electronic Filing Office toll-free at (800) 424-9530 ext. 1307 or locally "
        "at (202) 694-1307. "
    )

    data["name"] = name
    data["cmtee_id"] = cmte_id
    data["role"] = user_data.get("role")
    data["url"] = REGISTER_USER_URL + register_url_token

    BODY_HTML = render_to_string("add_user.html", {"data": data})

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client("ses", region_name="us-east-1")

    # Send the email.
    try:
        # Provide the contents of the email.
        client.send_email(
            Destination={
                "ToAddresses": RECIPIENT,
            },
            Message={
                "Body": {
                    "Html": {
                        "Charset": CHARSET,
                        "Data": BODY_HTML,
                    },
                    "Text": {
                        "Charset": CHARSET,
                        "Data": BODY_TEXT,
                    },
                },
                "Subject": {
                    "Charset": CHARSET,
                    "Data": SUBJECT,
                },
            },
            Source=SENDER,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response["Error"]["Message"])


def check_registration_token_exist(register_token):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """
            SELECT json_agg(t)
            FROM (Select * from public.authentication_account
            WHERE register_token = %s
            AND status ='Pending' AND delete_ind !='Y') t
            """
            cursor.execute(_sql, [register_token])
            user_list = cursor.fetchone()
            merged_list = []
            for dictL in user_list:
                merged_list = dictL[0]

        return merged_list
    except Exception as e:
        logger.debug("Exception occurred while checking user already present", str(e))
        raise e


def check_password_account_exist(cmte_id, email):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """
            SELECT json_agg(t)
            FROM (Select * from public.authentication_account
            WHERE cmtee_id = %s AND lower(email) = lower(%s)
            AND status ='Pending' AND delete_ind !='Y') t
            """
            cursor.execute(_sql, [cmte_id, email])
            user_list = cursor.fetchone()
            merged_list = []
            for dictL in user_list:
                merged_list = dictL[0]

        return merged_list
    except Exception as e:
        logger.debug("Exception occurred while checking user already present", str(e))
        raise e


def create_account_password(cmte_id, password, email, personal_key):
    try:
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET password = %s, status = %s, personal_key = %s, is_active = %s
            WHERE cmtee_id = %s
            AND email = %s AND delete_ind !='Y'
            """
            cursor.execute(
                _sql,
                [
                    make_password(password),
                    "Registered",
                    personal_key,
                    "true",
                    cmte_id,
                    email,
                ],
            )
            if cursor.rowcount != 1:
                raise Exception("Password was not reset.")
            else:
                return True
    except Exception as e:
        logger.debug("Exception occurred while resetting password.", str(e))
        raise e


def update_personal_key(cmte_id, email, personal_key):
    try:
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET personal_key = %s
            WHERE cmtee_id = %s
            AND email = %s AND delete_ind !='Y'
            """
            cursor.execute(_sql, [personal_key, cmte_id, email])
            if cursor.rowcount != 1:
                raise Exception("Personal Key was not updated.")
            else:
                return True
    except Exception as e:
        logger.debug("Exception occurred while updating personal key.", str(e))
        raise e


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def code_verify_register(request):
    if request.method == "POST":

        try:
            is_allowed = False
            token = ""
            code = request.data.get("code", None)
            payload = token_verification(request)
            cmte_id = payload.get("committee_id", None)
            email = payload.get("email", None)
            data = {"committee_id": cmte_id, "email": email, "code": code}

            list_mandatory_fields = ["committee_id", "email", "code"]
            check_madatory_field(data, list_mandatory_fields)
            user_list = check_password_account_exist(cmte_id, email)

            if user_list is None:
                is_allowed = False
                response = {"is_allowed": is_allowed}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)

            username = user_list["username"]
            key = user_list["secret_key"]
            unix_time = user_list["code_time"]
            otp_class = TOTPVerification(username)
            token_val = otp_class.verify_token(key, unix_time)

            if code == token_val:
                is_allowed = True
                reset_code_counter(key)
                token = create_password_jwt_token(email, cmte_id)

            response = {
                "is_allowed": is_allowed,
                "committee_id": cmte_id,
                "email": email,
                "token": token,
            }
            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug("exception occurred while verifying code", str(e))
            json_result = {"is_allowed": False}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def create_password(request):
    if request.method == "POST":
        try:
            password_created = False
            password = request.data.get("password", None)
            payload = token_verification(request)
            cmte_id = payload.get("committee_id", None)
            email = payload.get("email", None)
            two_factor = payload.get("2fVerified", None)
            data = {"committee_id": cmte_id, "email": email, "password": password}

            list_mandatory_fields = ["committee_id", "password", "email"]
            check_madatory_field(data, list_mandatory_fields)
            account_exist = check_password_account_exist(cmte_id, email)

            if not two_factor:
                is_allowed = False
                response = {"is_allowed": is_allowed}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
            if account_exist is None:
                is_allowed = False
                response = {"is_allowed": is_allowed}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
            if account_exist:
                personal_key = uuid.uuid4()
                password_created = create_account_password(
                    cmte_id, password, email, personal_key
                )

            response = {
                "password_created": password_created,
                "personal_key": personal_key,
            }
            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug("exception occurred while getting account information", str(e))
            json_result = {"message": "Password Reset was not successful."}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
def get_another_personal_key(request):
    if request.method == "GET":
        try:
            personal_key_updated = False
            payload = token_verification(request)
            cmte_id = payload.get("committee_id", None)
            email = payload.get("email", None)
            data = {"committee_id": cmte_id, "email": email}

            list_mandatory_fields = ["committee_id", "email"]
            check_madatory_field(data, list_mandatory_fields)
            personal_key = uuid.uuid4()
            update_personal_key(cmte_id, email, personal_key)
            personal_key_updated = True

            response = {
                "personal_key_updated": personal_key_updated,
                "personal_key": personal_key,
            }
            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug("exception occurred while getting account information", str(e))
            json_result = {"message": "Personal Key was not updated."}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
def get_committee_details(request):
    try:
        payload = token_verification(request)
        cmte_id = payload.get("committee_id", None)
        with connection.cursor() as cursor:
            query_string = """
            SELECT cm.cmte_id AS "committeeid", cm.cmte_name AS "committeename", cm.street_1 AS "street1", cm.street_2 AS "street2",
            cm.city, cm.state, cm.zip_code AS "zipcode",
            cm.cmte_email_1 AS "email_on_file", cm.cmte_email_2 AS "email_on_file_1", cm.phone_number, cm.cmte_type, cm.cmte_dsgn,
            cm.cmte_filing_freq, cm.cmte_filed_type,
            cm.treasurer_last_name AS "treasurerlastname", cm.treasurer_first_name AS "treasurerfirstname", cm.treasurer_middle_name AS "treasurermiddlename",
            cm.treasurer_prefix AS "treasurerprefix", cm.treasurer_suffix AS "treasurersuffix", cm.create_date AS "created_at", cm.cmte_type_category, f1.fax,
            f1.tphone as "treasurerphone", f1.url as "website", f1.email as "treasureremail"
            FROM public.committee_master cm
            LEFT JOIN public.form_1 f1 ON f1.comid=cmte_id
            WHERE cm.cmte_id = %s ORDER BY cm.create_date, f1.sub_date DESC, f1.create_date DESC LIMIT 1
            """
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""", [cmte_id]
            )
            modified_output = cursor.fetchone()[0]
        if modified_output is None:
            raise NoOPError(
                "The Committee ID: {} does not match records in Committee table".format(
                    cmte_id
                )
            )
        # levin_accounts = get_levin_accounts(cmte_id)
        # modified_output[0]['levin_accounts'] = levin_accounts
        return Response(modified_output[0], status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            "The get_committee_details API is throwing  an error: " + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def authenticate(request):
    if request.method == "POST":

        try:
            data = request.data
            register_token = data.get("register_token", None)
            id = data.get("id", None)
            is_allowed = False

            list_mandatory_fields = ["register_token", "id"]
            check_madatory_field(data, list_mandatory_fields)
            user_list = check_registration_token_exist(register_token)

            if not user_list:
                response = {"is_allowed": is_allowed}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)

            if id == "EMAIL":
                try:
                    email = data.get("email", None)
                    if not check_null_value(email):
                        raise Exception("email is required")

                    email_data = user_list["email"]
                    if not email_data.upper() == email.upper():
                        raise Exception("No matching record found")

                    cmte_id = user_list["cmtee_id"]
                    username = user_list["username"]
                    otp_class = TOTPVerification(username)
                    token_val = otp_class.generate_token(username)
                    if token_val != -1:
                        is_allowed = True

                    if is_allowed and not OTP_DISABLE:
                        send_email(token_val, email)
                        token = create_jwt_token(email, cmte_id)

                    response = {
                        "is_allowed": is_allowed,
                        "committee_id": cmte_id,
                        "email": email,
                        "token": token,
                    }
                    return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
                except Exception as e:
                    logger.debug(
                        "exception occurred while generating token for email option.",
                        str(e),
                    )
                    json_result = {"is_allowed": False}
                    return JsonResponse(
                        json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
                    )

            elif id == "TEXT" or id == "CALL":
                try:
                    email = user_list["email"]
                    contact = data.get("contact")
                    if not check_null_value(contact):
                        raise Exception("contact is required")
                    if not user_list["contact"] == contact:
                        raise Exception(" No matching record found.")

                    cmte_id = user_list["cmtee_id"]
                    username = user_list["username"]
                    otp_class = TOTPVerification(username)
                    token_val = otp_class.generate_token(username)
                    if token_val != -1:
                        is_allowed = True

                    if is_allowed and not OTP_DISABLE:
                        if request.data.get("id") == "TEXT":
                            send_text(token_val, user_list["contact"])

                        elif request.data.get("id") == "CALL":
                            send_call(token_val, user_list["contact"])

                    token = create_jwt_token(email, cmte_id)
                    response = {
                        "is_allowed": is_allowed,
                        "committee_id": cmte_id,
                        "email": email,
                        "token": token,
                    }
                    return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
                except Exception as e:
                    logger.debug(
                        "exception occurred while generating token for call/text option.",
                        str(e),
                    )
                    json_result = {"is_allowed": False}
                    return JsonResponse(
                        json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
                    )

            else:
                json_result = {"message": "Please select proper option."}
                return JsonResponse(
                    json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
                )
        except Exception as e:
            logger.debug(
                "exception occurred while registering -getting account information",
                str(e),
            )
            json_result = {"is_allowed": False}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )
