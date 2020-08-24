import logging
from binascii import unhexlify
from datetime import time

import jwt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_jwt.serializers import jwt_encode_handler
from rest_framework_jwt.views import obtain_jwt_token, ObtainJSONWebToken

from fecfiler.authentication.models import Account
from fecfiler.authentication.token import jwt_payload_handler
from fecfiler.password_management.otp import TOTPVerification
from fecfiler.password_management.views import check_madatory_field, check_email, check_account_exist, create_jwt_token, \
    reset_code_counter, token_verification
from fecfiler.settings import SECRET_KEY, JWT_PASSWORD_EXPIRY

logger = logging.getLogger(__name__)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def verify_login(request):
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
                # call obtain token here and check
                request.data['username'] = username
                request.data['password'] = "test1"
                unhexlify(user_list["password"].decode())

                user = Account.objects.filter(username=username).first()
                payload = jwt_payload_handler(user)

                token = jwt_encode_handler(payload)

            response = {'is_allowed': is_allowed, 'committee_id': cmte_id,
                        'email': email, 'token': token}
            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug("exception occurred while verifying code", str(e))
            json_result = {'is_allowed': False}
            return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def authenticate_login(request):
    if request.method == "POST":

        try:
            data = request.data
            username = data.get('username', None)
            password = data.get('password', None)
            is_allowed = False

            list_mandatory_fields = ["username", "password"]
            check_madatory_field(data, list_mandatory_fields)

            account = authenticate(request=request, username=username, password=password)

            # fail, bad login info
            if account is None:
                return JsonResponse({
                    'status': 'Unauthorized',
                    'message': 'ID/Password combination invalid.'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # fail, inactive account
            if not account.is_active:
                return JsonResponse({
                    'status': 'Unauthorized',
                    'message': 'This account has been disabled.'
                }, status=status.HTTP_401_UNAUTHORIZED)

            is_allowed = True
            token = create_jwt_token(account.email, account.cmtee_id)
            response = {'is_allowed': is_allowed, 'committee_id': account.cmtee_id,
                        'email': account.email, 'token': token}

            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug("exception occurred while getting account information", str(e))
            json_result = {'message': str(e)}
            return JsonResponse(json_result, status=status.HTTP_400_BAD_REQUEST, safe=False)
