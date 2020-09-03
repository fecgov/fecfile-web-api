import logging
import re
import time
import boto3
import jwt

from datetime import datetime
from datetime import timedelta
from callfire.client import CallfireClient
from botocore.exceptions import ClientError
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.http import JsonResponse
from django.template.loader import render_to_string
from django_otp.oath import TOTP
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes

from fecfiler.core.views import check_null_value
from fecfiler.password_management.otp import TOTPVerification
from fecfiler.settings import SECRET_KEY, JWT_PASSWORD_EXPIRY, API_LOGIN, API_PASSWORD

logger = logging.getLogger(__name__)


def find_account(cmte_id, personal_key, email):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """Select * from public.authentication_account WHERE cmtee_id = %s AND lower(email) = lower(%s) 
            AND personal_key = %s AND delete_ind !='Y' """
            cursor.execute(_sql, [cmte_id, email, personal_key])
            user_list = cursor.fetchone()
            if user_list is None:
                return False
            elif cursor.rowcount == 1:
                return True
            else:
                return False
    except Exception as e:
        logger.debug("exception occurred while checking if user was previously deleted", str(e))
        return False


def check_madatory_field(data, list_mandatory_fields):
    try:
        error = []
        for field in list_mandatory_fields:
            if not (field in data and check_null_value(data.get(field))):
                error.append(field)
        if len(error) > 0:
            string = ""
            for x in error:
                string = string + x + ", "
            string = string[0:-2]
            raise Exception(
                "The following mandatory fields are required in order to save data to Reports table: {}".format(
                    string
                )
            )
    except Exception as e:
        raise e


def check_account_exist(cmte_id, email):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """SELECT json_agg(t) FROM (Select * from public.authentication_account WHERE cmtee_id = %s AND lower(email) = lower(%s) 
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


def reset_code_counter(key):
    try:
        with connection.cursor() as cursor:
            _sql = """UPDATE public.authentication_account SET code_generated_counter = 0, updated_at = %s WHERE secret_key = %s"""
            cursor.execute(_sql, [datetime.now(), key])
            if cursor.rowcount != 1:
                logger.debug("Reset key failed for key {}", key)
        return cursor.rowcount
    except Exception as e:
        logger.debug("exception occurred reset key for key {}", key)


def reset_account_password(cmte_id, password, email):
    try:
        with connection.cursor() as cursor:
            _sql = """UPDATE public.authentication_account SET password = %s, status = %s WHERE cmtee_id = %s AND 
            email = %s AND delete_ind !='Y' """
            cursor.execute(_sql, [make_password(password), "Registered", cmte_id, email])
            if cursor.rowcount != 1:
                raise Exception("Password was not reset.")
            else:
                return True
    except Exception as e:
        logger.debug("Exception occurred while resetting password.", str(e))
        raise e


def token_verification(request):
    try:
        token_received = request.headers['token']
        payload = verify_token(token_received)
        return payload
    except Exception as e:
        logger.debug("exception occurred while generating token for email option.", str(e))
        raise e


def create_jwt_token(email, cmte_id):
    now = int(time.time())
    token = jwt.encode({
        'email': email,
        'committee_id': cmte_id,
        'exp': now + JWT_PASSWORD_EXPIRY
    }, SECRET_KEY, algorithm='HS256').decode('utf-8')
    return token


def verify_token(token_received):
    options = {'verify_exp': True,  # Skipping expiration date check
               'verify_aud': False}  # Skipping audience check
    payload = jwt.decode(token_received, key=SECRET_KEY, algorithms='HS256', options=options)
    return payload


def check_email(email):
    pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    if re.fullmatch(pattern, email):
        return email
    else:
        raise Exception(
            "Email entered is in an invalid format. Input received is: {}. Expected: abc@def.xyz or abc@def.wxy.xyz".format(
                email
            )
        )


def send_email(token_val, email):
    SENDER = "donotreply@fec.gov"
    RECIPIENT = []
    data = {}
    RECIPIENT.append("%s" % email)

    SUBJECT = "Register Account"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Use the code provided below to continue the verification process of your account.\r\n" +
                 token_val
                 + "\r\nPlease do not reply to this message"
                   "\r\nThis email was sent by FEC.gov. If you are receiving this email in error or have any "
                   "questions, "
                   "please contact the FEC Electronic Filing Office toll-free at (800) 424-9530 ext. 1307 or locally "
                   "at (202) 694-1307. "
                 )

    data['token'] = token_val

    BODY_HTML = render_to_string('forgot_password.html', {'data': data})

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name='us-east-1')

    # Send the email.
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses':
                    RECIPIENT,

            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,

        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])


def send_text(token_val, phone_no):
    try:

        token_val_formatted = "{:s}".format('\u0332'.join(token_val))
        client = CallfireClient(API_LOGIN, API_PASSWORD)
        response = client.texts.sendTexts(

            body=[
                {
                    'phoneNumber': phone_no,
                    'message': 'From the Federal Election Commission: The one-time code you requested is ' + token_val + '.Please use this code to login. '
                }
            ]
        ).result()
        print(response)
    except Exception as e:
        print(e.response['Error']['Message'])


def send_call(token_val, phone_no):
    try:
        token_formatted_val = " ,".join(token_val)
        client = CallfireClient(API_LOGIN, API_PASSWORD)
        response = client.calls.sendCalls(

            defaultVoice='FEMALE1',

            body=[
                {
                    'phoneNumber': phone_no,
                    'liveMessage': 'From the Federal Election Commission: The one-time code you requested is ' + token_formatted_val + ' , , , .Please use this code to login. ',
                    'machineMessage': 'From the Federal Election Commission: The one-time code you requested is ' + token_formatted_val + ', , , .Please use this code to login. '
                }
            ]

        ).result()
        print(response)
    except Exception as e:
        print(e.response['Error']['Message'])


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def authenticate_password(request):
    if request.method == "POST":

        try:
            data = request.data
            cmte_id = data.get('committee_id', None)
            email = data.get('email', None)
            is_allowed = False

            list_mandatory_fields = ["committee_id", "email"]
            check_madatory_field(data, list_mandatory_fields)
            check_email(email)
            user_list = check_account_exist(cmte_id, email)

            if user_list is None:
                response = {'is_allowed': is_allowed, 'committee_id': cmte_id,
                            'email': email}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
            else:
                is_allowed = True

                token = create_jwt_token(email, cmte_id)
                response = {'is_allowed': is_allowed, 'committee_id': cmte_id,
                            'email': email, 'token': token}

            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug("exception occurred while getting account information", str(e))
            json_result = {'message': str(e)}
            return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def reset_options_password(request):
    if request.method == "POST":

        if request.data.get("id") == 'EMAIL':
            try:
                is_allowed = False
                payload = token_verification(request)
                cmte_id = payload.get('committee_id', None)
                email = payload.get('email', None)
                data = {"committee_id": cmte_id, "email": email}

                list_mandatory_fields = ["committee_id", "email"]
                check_madatory_field(data, list_mandatory_fields)
                user_list = check_account_exist(cmte_id, email)

                if user_list is None:
                    response = {'is_allowed': is_allowed}
                    return JsonResponse(response, status=status.HTTP_200_OK, safe=False)

                username = user_list["username"]
                otp_class = TOTPVerification(username)
                token_val = otp_class.generate_token(username)
                if token_val != -1:
                    is_allowed = True

                if is_allowed:
                    send_email(token_val, email)

                response = {'is_allowed': is_allowed, 'committee_id': cmte_id,
                            'email': email}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
            except Exception as e:
                logger.debug("exception occurred while generating token for email option.", str(e))
                json_result = {'is_allowed': False}
                return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)

        elif request.data.get("id") == 'TEXT' or request.data.get("id") == 'CALL':
            try:
                is_allowed = False
                payload = token_verification(request)
                cmte_id = payload.get('committee_id', None)
                email = payload.get('email', None)
                data = {"committee_id": cmte_id, "email": email}

                list_mandatory_fields = ["committee_id", "email"]
                check_madatory_field(data, list_mandatory_fields)
                user_list = check_account_exist(cmte_id, email)

                if user_list is None:
                    response = {'is_allowed': is_allowed}
                    return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
                elif user_list is not None and not check_null_value(user_list["contact"]):
                    response = {'is_allowed': is_allowed}
                    return JsonResponse(response, status=status.HTTP_200_OK, safe=False)

                username = user_list["username"]
                otp_class = TOTPVerification(username)
                token_val = otp_class.generate_token(username)
                if token_val != -1:
                    is_allowed = True

                if is_allowed:
                    if request.data.get("id") == 'TEXT':
                        send_text(token_val, user_list["contact"])

                    elif request.data.get("id") == 'CALL':
                        send_call(token_val, user_list["contact"])
                        pass

                response = {'is_allowed': is_allowed, 'committee_id': cmte_id,
                            'email': email}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
            except Exception as e:
                logger.debug("exception occurred while getting account information", str(e))
                json_result = {'message': str(e)}
                return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)

        else:
            json_result = {'message': "Please select proper option."}
            return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def code_verify_password(request):
    if request.method == "POST":

        try:
            is_allowed = False
            code = request.data.get('code', None)
            payload = token_verification(request)
            cmte_id = payload.get('committee_id', None)
            email = payload.get('email', None)
            data = {"committee_id": cmte_id, "email": email, "code": code}

            list_mandatory_fields = ["committee_id", "email", "code"]
            check_madatory_field(data, list_mandatory_fields)
            user_list = check_account_exist(cmte_id, email)

            if user_list is None:
                is_allowed = False
                response = {'is_allowed': is_allowed}
                return JsonResponse(response, status=status.HTTP_200_OK, safe=False)

            username = user_list["username"]
            key = user_list["secret_key"]
            otp_class = TOTPVerification(username)
            token_val = otp_class.verify_token(key)

            if code == token_val:
                is_allowed = True
                reset_code_counter(key)

            response = {'is_allowed': is_allowed, 'committee_id': cmte_id,
                        'email': email}
            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug("exception occurred while verifying code", str(e))
            json_result = {'is_allowed': False}
            return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def reset_password(request):
    if request.method == "POST":
        try:
            password_reset = False
            password = request.data.get('password', None)
            payload = token_verification(request)
            cmte_id = payload.get('committee_id', None)
            email = payload.get('email', None)
            data = {"committee_id": cmte_id, "email": email, "password": password}

            list_mandatory_fields = ["committee_id", "password", "email"]
            check_madatory_field(data, list_mandatory_fields)
            account_exist = check_account_exist(cmte_id, email)
            if account_exist:
                password_reset = reset_account_password(cmte_id, password, email)

            response = {'password_reset': password_reset}
            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug("exception occurred while getting account information", str(e))
            json_result = {'message': "Password Reset was not successful."}
            return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)
