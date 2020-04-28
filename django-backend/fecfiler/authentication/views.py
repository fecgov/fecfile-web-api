import json
import datetime
import logging
import warnings
from calendar import timegm

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.http import JsonResponse
from django.utils.crypto import salted_hmac
from rest_framework import permissions, viewsets, status, views, generics
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework_jwt.compat import get_username_field, get_username

from .models import Account
import re
from .permissions import IsAccountOwner
from .serializers import AccountSerializer
from fecfiler.forms.models import Committee

from rest_framework_jwt.settings import api_settings

from ..core.transaction_util import do_transaction
from ..core.views import check_null_value, NoOPError

#jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


def jwt_response_payload_handler(token, user=None, request=None):
    """
    JWT TOKEN handler. 
    Checks if Committee ID exists in forms.models.Committee first before allowing access.
    """
    if len(user.username) > 9:
        user.username = user.username[0:9]
    if not Committee.objects.filter(committeeid=user.username).exists():
        return {
            'status': 'Unauthorized',
            'message': 'This account has not been authorized.'
        }

    return {
        'token': token,
        #'user': AccountSerializer(user, context={'request':request}).data
    }

# payload = jwt_response_payload_handler(user)
# token = jwt_encode_handler(payload)

class AccountViewSet(viewsets.ModelViewSet):
    lookup_field = 'username'

    serializer_class = AccountSerializer

    def get_queryset(self):
        queryset = Account.objects.all()
        queryset = queryset.filter(self.request.user)
        serializer_class = AccountSerializer(Account, many=True)
        return JsonResponse(serializer_class.data, safe=False)

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return permissions.AllowAny(),
        if self.request.method == 'POST':
            return permissions.AllowAny(),
        return permissions.IsAuthenticated(), IsAccountOwner()

    def create(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            Account.objects.create_user(**serializer.validated_data)
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'Bad request',
            'message': 'Account could not be created with received data.',
            'details': str(serializer.errors),
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(views.APIView):

    def post(self, request, format=None):
        data = request.data
        username = data.get('username', None)
        password = data.get('password', None)
        email = data.get('email', None)
        # import ipdb; ipdb.set_trace()
        account = authenticate(request=request, username=username, password=password, email=email)

        # fail, bad login info
        if account is None:
            return Response({
                'status': 'Unauthorized',
                'message': 'ID/Password combination invalid.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # fail, inactive account
        if not account.is_active:
            return Response({
                'status': 'Unauthorized',
                'message': 'This account has been disabled.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not Committee.objects.filter(committeeid=username).exists():
            return Response({
                'status': 'Unauthorized',
                'message': 'This account has not been authorized.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # success, login and respond
        login(request, account)
        serialized = AccountSerializer(account)
        return Response(serialized.data)


class LogoutView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        logout(request)
        return Response({}, status=status.HTTP_204_NO_CONTENT)


logger = logging.getLogger(__name__)


def get_users_list(cmte_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from manage user table
            _sql = """SELECT json_agg(t) FROM (Select first_name, last_name, email, contact, is_active, role, id from public.authentication_account WHERE cmtee_id = %s AND delete_ind != 'Y' order by id) t"""
            cursor.execute(_sql, [cmte_id])
            user_list = cursor.fetchall()
            if user_list is None:
                raise NoOPError(
                    "No users for found for committee Id  {}".format(
                        cmte_id
                    )
                )
            merged_list = []
            for dictL in user_list:
                merged_list = dictL[0]

        return merged_list
    except Exception as e:
        logger.debug(e)
        raise e


def delete_manage_user(data):
    try:
        with connection.cursor() as cursor:
            _sql = """UPDATE public.authentication_account
                        SET delete_ind = 'Y' 
                        WHERE id = %s AND cmtee_id = %s
                    """
            _v = (data.get("user_id"), data.get("cmte_id"))
            cursor.execute(_sql, _v)
            if cursor.rowcount != 1:
                logger.debug("deleting user for {} failed."
                             " No record was found", data.get("id"))
        return cursor.rowcount
    except Exception as e:
        logger.debug("exception occurred while deleting record for id"
                     " : {}", data.get("id"))


def user_data_dict():
    valid_fields = [
        "first_name",
        "last_name",
        "email",
        "role",
        "contact"
    ]
    return valid_fields


def check_user_present(data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """Select * from public.authentication_account WHERE cmtee_id = %s AND email = %s AND delete_ind !='Y' """
            cursor.execute(_sql, [data.get("cmte_id"), data.get("email")])
            user_list = cursor.fetchone()
            if user_list is not None:
                raise NoOPError(
                    "User already exist for committee id:{} and email id:{}".format(
                        data.get("cmte_id"), data.get("email")
                    )
                )
            else:
                return False
    except Exception as e:
        logger.debug("Exception occurred while checking user already present", str(e))
        raise e


def update_deleted_record(data):
    try:
        with connection.cursor() as cursor:
            _sql = """UPDATE public.authentication_account SET role = %s, first_name = %s, last_name = %s,delete_ind ='N', is_active ='true' WHERE cmtee_id = %s AND email = %s"""
            cursor.execute(_sql, [data.get("role"), data.get("first_name"),
                                  data.get("last_name"), data.get("cmte_id"),
                                  data.get("email")])
    except Exception as e:
        logger.debug("Exception occurred adding deleted user", str(e))
        raise e


def user_previously_deleted(data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """Select * from public.authentication_account WHERE cmtee_id = %s AND email = %s AND delete_ind ='Y'"""
            cursor.execute(_sql, [data.get("cmte_id"), data.get("email")])
            user_list = cursor.fetchone()
            if user_list is not None:
                update_deleted_record(data)
                return True
            else:
                return False
    except Exception as e:
        logger.debug("exception occurred while checking if user was previously deleted", str(e))
        raise e


def get_next_user_id():
    default_sequence = 1
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT max(id) from public.authentication_account""")
            user_id = cursor.fetchone()[0]
            if user_id is None:
                default_sequence
            else:
                default_sequence = int(user_id) + 1

        return default_sequence
    except Exception:
        raise


def add_new_user(data, cmte_id):
    try:
        user_id = get_next_user_id()
        data["user_id"] = user_id
        data["user_name"] = cmte_id + data.get("email")
        with connection.cursor() as cursor:
            # Insert data into manage user table
            cursor.execute(
                """INSERT INTO public.authentication_account (id,password, last_login, is_superuser, tagline, created_at, updated_at, is_staff, date_joined,username, first_name, last_name, email, contact, role, is_active,cmtee_id, delete_ind)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    user_id,
                    make_password("test"),
                    datetime.datetime.now(),
                    "false",
                    " ",
                    datetime.datetime.now(),
                    datetime.datetime.now(),
                    "false",
                    datetime.datetime.now(),
                    data.get("user_name"),
                    data.get("first_name"),
                    data.get("last_name"),
                    data.get("email"),
                    data.get("contact"),
                    (data.get("role")).upper(),
                    "true",
                    cmte_id,
                    'N'
                ],
            )
            if cursor.rowcount != 1:
                logger.debug("Inserting new user in manage table failed")

    except Exception as e:
        logger.debug("Exception occurred while inserting new user", str(e))
        raise


def put_sql_user(data):
    try:
        with connection.cursor() as cursor:
            _sql = """UPDATE public.authentication_account SET delete_ind = 'N', role = %s,is_active = %s,first_name = %s,last_name = %s,email = %s,contact = %s,username = %s WHERE id = %s AND cmtee_id = %s AND delete_ind != 'Y'"""
            _v = (
                data.get("role"),
                "true",
                data.get("first_name"),
                data.get("last_name"),
                data.get("email"),
                data.get("contact"),
                data.get("new_user_name"),
                data.get("id"),
                data.get("cmte_id"),
            )
            cursor.execute(_sql, _v)
            if cursor.rowcount != 1:
                logger.debug("Updating user info for {} failed."
                             " No record was found")
        return cursor.rowcount
    except Exception as e:
        logger.debug("Exception occurred while updating user", str(e))
        raise e


def get_current_email(data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """Select email from public.authentication_account WHERE id = %s AND cmtee_id = %s AND delete_ind !='Y' """
            cursor.execute(_sql, [data.get("id"), data.get("cmte_id")])
            email = cursor.fetchone()[0]

            return email
    except Exception as e:
        logger.debug("Exception occurred while toggling status", str(e))
        raise e


def update_user(data):
    try:
        logger.debug("update user record with {}".format(data))
        user_already_exist = False
        email = get_current_email(data)
        if email != data.get("email"):
            user_already_exist = check_user_present(data)
        if not user_already_exist:
            rows = put_sql_user(data)
        else:
            raise Exception("user already present with "
                            "committee id{} and email id{}", data.get("cmte_id"),
                            data.get("email"))
    except Exception as e:
        # print(e)
        raise Exception(
            "The user update sql is throwing an error: " + str(e)
        )
    return rows


def check_custom_validations(email, status, role):
    try:
        check_email_validation(email)
        if role.upper() not in ["ADMIN", "READ_ONLY", "UPLOADER", "ENTRY"]:
            raise Exception("Role should be ADMIN, READ-ONLY, UPLOADER")
    except Exception as e:
        logger.debug("Custom validation failed")
        raise e


def check_email_validation(email):
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    if not re.search(regex, email):
        raise Exception("Email-id is not valid")


@api_view(["POST", "GET", "DELETE", "PUT"])
def manage_user(request):
    if request.method == "GET":
        try:
            cmte_id = request.user.username
            if len(cmte_id) > 9:
                cmte_id = cmte_id[0:9]
            if not check_null_value(cmte_id):
                raise Exception("Committe id is missing from request data")

            datum = get_users_list(cmte_id)
            json_result = {'users': datum, 'rows': len(datum)}
            return JsonResponse(json_result, status=status.HTTP_200_OK, safe=False)
        except NoOPError as e:
            logger.debug(e)
            forms_obj = []
            return JsonResponse(
                forms_obj, status=status.HTTP_400_BAD_REQUEST, safe=False
            )
        except Exception as e:
            logger.debug(e)
            return Response(
                "The manageUser API - GET is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )
    elif request.method == "DELETE":
        try:
            cmte_id = request.user.username
            if len(cmte_id) > 9:
                cmte_id = cmte_id[0:9]
            data = {"cmte_id": cmte_id}
            if "id" in request.data and check_null_value(
                    request.data.get("id")
            ):
                data["user_id"] = request.data.get("id")
            else:
                raise Exception("Missing Input: ID is mandatory")

            row = delete_manage_user(data)
            if row > 0:
                msg = "The User ID: {} has been successfully deleted"
            else:
                msg = "The User ID: {} has not been successfully deleted." \
                      "No matching record was found."
            return JsonResponse(msg.format(data.get("user_id")),
                                status=status.HTTP_200_OK,
                                safe=False)
        except Exception as e:
            return JsonResponse(
                "The Manage User API - DELETE is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST, safe=False
            )
    elif request.method == "POST":
        try:
            cmte_id = request.user.username
            if len(cmte_id) > 9:
                cmte_id = cmte_id[0:9]
            else:
                username = cmte_id + request.data.get("email")

            data = {"cmte_id": cmte_id}

            fields = user_data_dict()
            data = validate(data, fields, request)
            # check if user already exsist
            user_exist = check_user_present(data)
            # check if user was previously deleted, then reactivate
            user_reactivated = user_previously_deleted(data)
            if not user_exist and not user_reactivated:
                data = add_new_user(data, cmte_id)

            output = get_users_list(cmte_id)
            json_result = {'users': output}
            return JsonResponse(json_result, status=status.HTTP_201_CREATED, safe=False)
        except Exception as e:
            return Response(
                "Adding new user - POST is throwing an exception: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    elif request.method == "PUT":
        try:
            cmte_id = request.user.username
            if len(cmte_id) > 9:
                old_email = cmte_id[9:]
                cmte_id = cmte_id[0:9]
                username = cmte_id + request.data.get("email")
            else:
                username = cmte_id
            data = {"cmte_id": cmte_id, "user_name": request.user.username}
            fields = user_data_dict()
            fields.append("id")
            data = validate(data, fields, request)
            data["new_user_name"] = username
            data["old_email"] = old_email
            rows = update_user(data)
            output = get_users_list(cmte_id)
            json_result = {'users': output, "rows_updated": rows}
            return JsonResponse(json_result, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response(
                "The schedL API - PUT is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )


def validate(data, fields, request):
    for val in fields:
        data = validate_input_data(request, val, data)
    check_custom_validations(data.get("email"), data.get("role"))
    logger.debug("manage user- all input data is valid")
    return data


def validate_input_data(request, val, data):
    if val in request.data and check_null_value(
            request.data.get(val)
    ):
        data[val] = request.data.get(val)
    else:
        raise Exception("Missing Input: {} is mandatory", val)
    return data


def get_toggle_status(data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """Select is_active from public.authentication_account WHERE id = %s AND cmtee_id = %s AND delete_ind !='Y' """
            cursor.execute(_sql, [data.get("id"), data.get("cmte_id")])
            current_status = cursor.fetchone()[0]
            if current_status is None:
                raise NoOPError(
                    "No status set for id:{}. Can't toggle it. ".format(data.get("id"))
                )
            else:
                if current_status:
                    return False
                else:
                    return True
    except Exception as e:
        logger.debug("Exception occurred while toggling status", str(e))
        raise e


def update_toggle_status(status, data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """UPDATE public.authentication_account SET is_active = %s where id = %s AND cmtee_id = %s AND delete_ind !='Y' """
            cursor.execute(_sql, [status, data.get("id"), data.get("cmte_id")])

            if cursor.rowcount != 1:
                raise NoOPError(
                    "failed to toggle status for id:{}. ".format(data.get("id"))
                )
            return cursor.rowcount
    except Exception as e:
        logger.debug("Exception occurred while toggling status", str(e))
        raise e


@api_view(["PUT"])
def toggle_user(request):
    if request.method == "PUT":
        try:
            username = request.user.username
            if len(username) > 9:
                cmte_id = username[0:9]
            data = {"username": username, "id": request.data.get("id"),
                    "cmte_id": cmte_id}
            toggle_status = get_toggle_status(data)
            rows = update_toggle_status(toggle_status, data)
            output = get_users_list(cmte_id)
            json_result = {'users': output, "rows_updated": rows}
            return JsonResponse(json_result, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug("exception occured while toggling status", str(e))
            raise e
