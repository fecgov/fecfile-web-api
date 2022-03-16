import datetime
import logging
import re
import secrets

from django.contrib.auth import authenticate, login, logout
from django.db import connection
from django.http import JsonResponse
from rest_framework import permissions, viewsets, status, views
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .auth_enum import Roles
from .authorization import is_not_treasurer
from .models import Account

from .permissions import IsAccountOwner
from .register import send_email_register
from .serializers import AccountSerializer
from fecfiler.forms.models import Committee
from rest_framework_jwt.settings import api_settings

from fecfiler.core.views import check_null_value, NoOPError, get_email
from fecfiler.settings import OTP_DISABLE

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
            "status": "Unauthorized",
            "message": "This account has not been authorized.",
        }

    return {
        "token": token,
    }


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


class LoginView(views.APIView):
    def post(self, request, format=None):
        data = request.data
        username = data.get("username", None)
        password = data.get("password", None)
        email = data.get("email", None)
        account = authenticate(
            request=request, username=username, password=password, email=email
        )

        # fail, bad login info
        if account is None:
            return Response(
                {
                    "status": "Unauthorized",
                    "message": "ID/Password combination invalid.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # fail, inactive account
        if not account.is_active:
            return Response(
                {
                    "status": "Unauthorized",
                    "message": "This account has been disabled.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not Committee.objects.filter(committeeid=username).exists():
            return Response(
                {
                    "status": "Unauthorized",
                    "message": "This account has not been authorized.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

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
            _sql = """
            SELECT json_agg(t)
            FROM (Select first_name, last_name, email, contact, is_active, role, id, status
            from public.authentication_account
            WHERE cmtee_id = %s AND delete_ind != 'Y' AND upper(role) != %s order by id) t
            """
            cursor.execute(_sql, [cmte_id, Roles.C_ADMIN.value])
            user_list = cursor.fetchall()
            if user_list is None:
                raise NoOPError(
                    "No users for found for committee Id  {}".format(cmte_id)
                )
            merged_list = []
            for dictL in user_list:
                merged_list = dictL[0]

        return merged_list
    except Exception as e:
        logger.error(e)
        raise e


def delete_manage_user(data):
    try:
        with connection.cursor() as cursor:
            _sql = """UPDATE public.authentication_account
                        SET delete_ind = 'Y'
                        WHERE id = %s AND cmtee_id = %s
                        AND upper(role) != %s
                    """
            _v = (data.get("user_id"), data.get("cmte_id"), Roles.C_ADMIN.value)
            cursor.execute(_sql, _v)
            if cursor.rowcount != 1:
                logger.error(
                    "deleting user for {} failed." " No record was found",
                    data.get("id"),
                )
        return cursor.rowcount
    except Exception as e:
        logger.error(e)
        logger.error(
            "exception occurred while deleting record for id" " : {}", data.get("id")
        )


def user_data_dict():
    valid_fields = ["first_name", "last_name", "email", "role", "contact"]
    return valid_fields


def check_user_present(data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """Select * from public.authentication_account WHERE cmtee_id = %s AND lower(email) = lower(%s) AND delete_ind !='Y' """
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
        logger.error("Exception occurred while checking user already present", str(e))
        raise e


def update_deleted_record(data):
    try:
        register_url_token = get_registration_token()
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET role = %s, first_name = %s, last_name = %s, delete_ind ='N',
            status='Pending', register_token= %s
            WHERE cmtee_id = %s AND lower(email) = lower(%s)
            """
            cursor.execute(
                _sql,
                [
                    data.get("role"),
                    data.get("first_name"),
                    data.get("last_name"),
                    register_url_token,
                    data.get("cmte_id"),
                    data.get("email"),
                ],
            )
            return register_url_token

    except Exception as e:
        logger.error("Exception occurred adding deleted user", str(e))
        raise e


def user_previously_deleted(data):
    try:
        with connection.cursor() as cursor:
            registration_token = ""
            # check if user already exist
            _sql = """
            Select * from public.authentication_account
            WHERE cmtee_id = %s AND lower(email) = lower(%s) AND delete_ind ='Y'
            """
            cursor.execute(_sql, [data.get("cmte_id"), data.get("email")])
            user_list = cursor.fetchone()
            if user_list is not None:
                registration_token = update_deleted_record(data)
                return True, registration_token
            else:
                return False, registration_token
    except Exception as e:
        logger.error(
            "exception occurred while checking if user was previously deleted", str(e)
        )
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


def add_new_user(data, cmte_id, register_url_token):
    try:
        user_id = get_next_user_id()
        data["user_id"] = user_id
        data["user_name"] = cmte_id + data.get("email")
        with connection.cursor() as cursor:
            # Insert data into manage user table
            cursor.execute(
                """
                INSERT INTO public.authentication_account (
                    id, last_login, is_superuser, tagline, created_at, updated_at,
                    is_staff, date_joined,username, first_name, last_name, email,
                    contact, role, is_active,cmtee_id, delete_ind, status, register_token
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    user_id,
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
                    "false",
                    cmte_id,
                    "N",
                    "Pending",
                    register_url_token,
                ],
            )
            if cursor.rowcount != 1:
                logger.debug("Inserting new user in manage table failed")

    except Exception as e:
        logger.error("Exception occurred while inserting new user", str(e))
        raise e


def put_sql_user(data):
    try:
        with connection.cursor() as cursor:
            _sql = """
            UPDATE public.authentication_account
            SET delete_ind = 'N', role = %s,is_active = %s, first_name = %s,
            last_name = %s,email = %s,contact = %s,username = %s
            WHERE id = %s
            AND cmtee_id = %s AND delete_ind != 'Y' AND status != %s
            """
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
                "Pending",
            )
            cursor.execute(_sql, _v)
            if cursor.rowcount != 1:
                logger.error("Updating user info for {} failed." " No record was found")
        return cursor.rowcount
    except Exception as e:
        logger.error("Exception occurred while updating user", str(e))
        raise e


def get_current_email(data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """
            Select email from public.authentication_account
            WHERE id = %s AND cmtee_id = %s AND delete_ind !='Y'
            """
            cursor.execute(_sql, [data.get("id"), data.get("cmte_id")])
            email = cursor.fetchone()[0]

            return email
    except Exception as e:
        logger.error("Exception occurred while toggling status", str(e))
        raise e


def update_user(data):
    try:
        logger.debug("update user record with {}".format(data))
        user_already_exist = False
        email = get_current_email(data)
        if email != data.get("email"):
            user_already_exist = check_user_present(data)
        backup_admin_exist = backup_user_exist(data)
        if not user_already_exist and not backup_admin_exist:
            rows = put_sql_user(data)

    except Exception as e:
        raise Exception(str(e))
    return rows


def check_custom_validations(email, role):
    try:
        check_email_validation(email)
        if role.upper() not in ["BC_ADMIN", "ADMIN", "REVIEWER", "EDITOR"]:
            raise Exception("Role should be BC_ADMIN,ADMIN,REVIEWER, EDITOR")
    except Exception as e:
        logger.error("Custom validation failed")
        raise e


def check_email_validation(email):
    regex = r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"
    if not re.search(regex, email):
        raise Exception("Email-id is not valid")


def backup_user_exist(data):
    try:
        if data.get("role").upper() != Roles.BC_ADMIN.value:
            return False

        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """
                Select * from public.authentication_account
                WHERE cmtee_id = %s AND lower(role) = lower(%s)
                AND delete_ind !='Y'
            """
            cursor.execute(_sql, [data.get("cmte_id"), Roles.BC_ADMIN.value])
            backup_admin_list = cursor.fetchone()
            if backup_admin_list is not None:
                raise NoOPError(
                    "Back up Admin exist for committee id:{}".format(
                        data.get("cmte_id")
                    )
                )
            else:
                return False
    except Exception as e:
        logger.error("Exception occurred while adding user.", str(e))
        raise e


def get_registration_token():
    register_url_token = secrets.token_urlsafe(20)

    with connection.cursor() as cursor:
        # check if user already exist
        _sql = """
        Select * from public.authentication_account
        WHERE register_token = %s AND delete_ind !='Y'
        """
        cursor.execute(_sql, [register_url_token])
        user_list = cursor.fetchone()
        if user_list is not None:
            get_registration_token()
        else:
            return register_url_token


def validate(data, fields, request):
    for val in fields:
        data = validate_input_data(request, val, data)
    check_custom_validations(data.get("email"), data.get("role"))
    logger.debug("manage user- all input data is valid")
    return data


def validate_input_data(request, val, data):
    if val in request.data and check_null_value(request.data.get(val)):
        data[val] = request.data.get(val)
    else:
        raise Exception("Missing Input: {} is mandatory", val)
    return data


def get_toggle_status(data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """
            Select is_active
            from public.authentication_account
            WHERE id = %s AND cmtee_id = %s AND delete_ind !='Y'
            """
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
        logger.error("Exception occurred while toggling status", str(e))
        raise e


def update_toggle_status(status, data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """
            UPDATE public.authentication_account
            SET is_active = %s
            where id = %s
            AND cmtee_id = %s AND delete_ind !='Y'
            AND upper(role) != %s AND status != %s
            """
            cursor.execute(
                _sql,
                [
                    status,
                    data.get("id"),
                    data.get("cmte_id"),
                    Roles.C_ADMIN.value,
                    "Pending",
                ],
            )

            if cursor.rowcount != 1:
                raise NoOPError(
                    "failed to toggle status for id:{}. ".format(data.get("id"))
                )
            return cursor.rowcount
    except Exception as e:
        logger.error("Exception occurred while toggling status", str(e))
        raise e


@api_view(["GET"])
def current_user(request):
    if request.method == "GET":
        try:
            user = {
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
                "phone": request.user.contact,
            }

            return JsonResponse(user, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.error("exception occurred while getting user information", str(e))
            json_result = {}
            return JsonResponse(
                json_result, status=status.HTTP_400_BAD_REQUEST, safe=False
            )
