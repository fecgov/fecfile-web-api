import json
import datetime
import logging

from django.contrib.auth import authenticate, login, logout
from django.db import connection
from django.http import JsonResponse
from rest_framework import permissions, viewsets, status, views, generics
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from .models import Account
import re
from .permissions import IsAccountOwner
from .serializers import AccountSerializer
from fecfiler.forms.models import Committee

from rest_framework_jwt.settings import api_settings

from ..core.transaction_util import do_transaction
from ..core.views import check_null_value, NoOPError

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

def jwt_response_payload_handler(token, user=None, request=None):
    """
    JWT TOKEN handler. 
    Checks if Committee ID exists in forms.models.Committee first before allowing access.
    """
    if not Committee.objects.filter(committeeid=user.username).exists():
        return {
            'status': 'Unauthorized',
            'message': 'This account has not been authorized.'
        }

    return {
        'token': token
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
            _sql = """SELECT json_agg(t) FROM (Select first_name, last_name,userName, email, is_active, role, id from public.authentication_account WHERE username = %s AND delete_ind != 'Y') t"""
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
    _sql = """UPDATE public.authentication_account
                SET delete_ind = 'Y' 
                WHERE id = %s AND username = %s
            """
    _v = (data.get("id"), data.get("cmte_id"))
    do_transaction(_sql, _v)


def user_data_dict():
    valid_fields = [
        "first_name",
        "last_name",
        "email",
        "role",
        "is_active"
    ]
    return valid_fields


def check_user_present(data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """Select * from public.authentication_account WHERE username = %s AND email = %s AND delete_ind !='Y' """
            cursor.execute(_sql, [data.get("cmte_id"), data.get("email")])
            user_list = cursor.fetchone()
            if user_list is not None:
                raise NoOPError(
                    "User already exist for committee Id  {}".format(
                        data.get("cmte_id")
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
            _sql = """UPDATE public.auth_user SET role = %s, first_name = %s, last_name = %s,delete_ind ='N', status ='ACTIVE' WHERE cmte_id = %s AND email_id = %s"""
            cursor.execute(_sql, [data.get("role"), data.get("first_name"),
                                  data.get("last_name"), data.get("cmte_id"),
                                  data.get("email_id")])
    except Exception as e:
        logger.debug("Exception occurred adding deleted user", str(e))
        raise e


def user_previously_deleted(data):
    try:
        with connection.cursor() as cursor:
            # check if user already exist
            _sql = """Select * from public.authentication_account WHERE username = %s AND email = %s AND delete_ind ='Y'"""
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
        with connection.cursor() as cursor:
            # Insert data into manage user table
            cursor.execute(
                """INSERT INTO public.authentication_account (id,password, last_login, is_superuser, tagline, created_at, updated_at, is_staff, date_joined,username, first_name, last_name, email, role, is_active, delete_ind)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    user_id,
                    "Test",
                    datetime.datetime.now(),
                    "false",
                    " ",
                    datetime.datetime.now(),
                    datetime.datetime.now(),
                    "false",
                    datetime.datetime.now(),
                    cmte_id,
                    data.get("first_name"),
                    data.get("last_name"),
                    data.get("email"),
                    (data.get("role")).upper(),
                    (data.get("is_active")),
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
            _sql = """UPDATE public.authentication_account SET delete_ind = 'N', role = %s,is_Active = %s,first_name = %s,last_name = %s,email = %s WHERE id = %s AND username = %s AND delete_ind != 'Y'"""
            _v = (
                data.get("role"),
                data.get("is_active"),
                data.get("first_name"),
                data.get("last_name"),
                data.get("email"),
                data.get("id"),
                data.get("cmte_id"),
            )
            cursor.execute(_sql, _v)
            if cursor.rowcount != 1:
                logger.debug("Inserting new user in manage table failed")

    except Exception as e:
        logger.debug("Exception occurred while inserting new user", str(e))
        raise e


def update_user(data):
    try:
        logger.debug("update user record with {}".format(data))
        put_sql_user(data)
    except Exception as e:
        # print(e)
        raise Exception(
            "The user update sql is throwing an error: " + str(e)
        )
    return data


def check_custom_validations(email, status, role):
    try:
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if not re.search(regex, email):
            raise Exception("Email-id is not valid")
        if status in ["null", "NULL"]:
            raise Exception("Status value should be either ACTIVE or INACTIVE")
        if role.upper() not in ["ADMIN", "READ-ONLY", "UPLOADER"]:
            raise Exception("Role should be ADMIN, READ-ONLY, UPLOADER")
    except Exception as e:
        logger.debug("Custom validation failed")
        raise e


@api_view(["POST", "GET", "DELETE", "PUT"])
def manage_user(request):
    if request.method == "GET":
        try:
            cmte_id = request.user.username
            if not check_null_value(cmte_id):
                raise Exception("Committe id is missing from request data")

            datum = get_users_list(cmte_id)
            return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
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
            data = {"cmte_id": request.user.username}
            if "id" in request.data and check_null_value(
                    request.data.get("id")
            ):
                data["user_id"] = request.data.get("id")
            else:
                raise Exception("Missing Input: ID is mandatory")

            delete_manage_user(data)
            return Response(
                "The User ID: {} has been successfully deleted".format(
                    data.get("user_id")
                ),
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                "The Manage User API - DELETE is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )
    elif request.method == "POST":
        try:
            cmte_id = request.user.username
            data = {"cmte_id": request.user.username}
            fields = user_data_dict()
            data = validate(data, fields, request)
            # check if user already exsist
            user_exist = check_user_present(data)
            # check if user was previously deleted, then reactivate
            user_reactivated = user_previously_deleted(data)
            if not user_exist and not user_reactivated:
                data = add_new_user(data, cmte_id)

            output = get_users_list(cmte_id)
            return JsonResponse(output, status=status.HTTP_201_CREATED, safe=False)
        except Exception as e:
            return Response(
                "Adding new user - POST is throwing an exception: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    elif request.method == "PUT":
        try:
            cmte_id = request.user.username
            data = {"cmte_id": request.user.username}
            fields = user_data_dict()
            fields.append("id")
            data = validate(data, fields, request)
            data_returned = update_user(data)
            output = get_users_list(cmte_id)
            return JsonResponse(output, status=status.HTTP_200_OK, safe=False)
        except Exception as e:
            logger.debug(e)
            return Response(
                "The schedL API - PUT is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )


def validate(data, fields, request):
    for val in fields:
        data = validate_input_data(request, val, data)
    check_custom_validations(data.get("email"), data.get("is_active"), data.get("role"))
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
