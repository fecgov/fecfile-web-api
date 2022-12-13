from django.views.generic import View
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, logout
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from fecfiler.settings import (
    LOGIN_REDIRECT_CLIENT_URL,
    FFAPI_COMMITTEE_ID_COOKIE_NAME,
    FFAPI_EMAIL_COOKIE_NAME,
    FFAPI_COOKIE_DOMAIN,
    OIDC_RP_CLIENT_ID,
    LOGOUT_REDIRECT_URL,
    OIDC_OP_LOGOUT_ENDPOINT,
    E2E_TESTING_LOGIN,
)

from rest_framework.response import Response
from rest_framework import filters, permissions, views, status
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from .models import Account
from .serializers import AccountSerializer
from urllib.parse import urlencode
from datetime import datetime
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class AccountViewSet(GenericViewSet, ListModelMixin):
    """
        The Account ViewSet allows the user to retrieve the users in the same committee

        The CommitteeOwnedViewset could not be inherited due to the different structure
        of a user object versus other objects.
            (IE - having a "cmtee_id" field instead of "committee_id")
    """

    serializer_class = AccountSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "last_name",
        "first_name",
        "id",
        "email",
        "role",
        "is_active",
        "name",
    ]
    ordering = ["name"]

    def get_queryset(self):
        queryset = (
            Account.objects.annotate(
                name=Concat(
                    "last_name", Value(", "), "first_name", output_field=CharField()
                )
            )
            .filter(cmtee_id=self.request.user.cmtee_id)
            .all()
        )

        return queryset


# class AccountViewSet(viewsets.ModelViewSet):
#     lookup_field = "username"
#     serializer_class = AccountSerializer

#     def get_queryset(self):
#         queryset = Account.objects.all()
#         queryset = queryset.filter(self.request.user)
#         serializer_class = AccountSerializer(Account, many=True)
#         return JsonResponse(serializer_class.data, safe=False)

#     def get_permissions(self):
#         if self.request.method in permissions.SAFE_METHODS:
#             return (permissions.AllowAny(),)
#         if self.request.method == "POST":
#             return (permissions.AllowAny(),)
#         return permissions.IsAuthenticated(), IsAccountOwner()

#     def create(self, request):
#         serializer = self.serializer_class(data=request.data)

#         if serializer.is_valid():
#             Account.objects.create_user(**serializer.validated_data)
#             return Response(serializer.validated_data, status=status.HTTP_201_CREATED)

#         return Response(
#             {
#                 "status": "Bad request",
#                 "message": "Account could not be created with received data.",
#                 "details": str(serializer.errors),
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )


class LoginDotGovSuccessSpaRedirect(View):
    def get(self, request, *args, **kwargs):
        request.session["user_id"] = request.user.pk
        redirect = HttpResponseRedirect(LOGIN_REDIRECT_CLIENT_URL)
        redirect.set_cookie(
            FFAPI_COMMITTEE_ID_COOKIE_NAME,
            request.user.cmtee_id,
            domain=FFAPI_COOKIE_DOMAIN,
            secure=True,
        )
        redirect.set_cookie(
            FFAPI_EMAIL_COOKIE_NAME,
            request.user.email,
            domain=FFAPI_COOKIE_DOMAIN,
            secure=True,
        )
        return redirect


class LoginDotGovSuccessLogoutSpaRedirect(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponseRedirect(LOGIN_REDIRECT_CLIENT_URL)
        response.delete_cookie(
            FFAPI_COMMITTEE_ID_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN
        )
        response.delete_cookie(FFAPI_EMAIL_COOKIE_NAME, domain=FFAPI_COOKIE_DOMAIN)
        response.delete_cookie("csrftoken", domain=FFAPI_COOKIE_DOMAIN)
        return response


class IsAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, account):
        if request.session.get("user_id"):
            return account.pk == request.session.get("user_id")
        return False


def login_dot_gov_logout(request):
    client_id = OIDC_RP_CLIENT_ID
    post_logout_redirect_uri = LOGOUT_REDIRECT_URL
    state = request.get_signed_cookie("oidc_state")

    params = {
        "client_id": client_id,
        "post_logout_redirect_uri": post_logout_redirect_uri,
        "state": state,
    }
    query = urlencode(params)
    op_logout_url = OIDC_OP_LOGOUT_ENDPOINT
    redirect_url = "{url}?{query}".format(url=op_logout_url, query=query)

    return redirect_url


def generate_username(uuid):
    return uuid


def update_last_login_time(account):
    account.last_login = datetime.now()
    account.save()


def handle_invalid_login(username):
    logger.debug("Unauthorized login attempt: {}".format(username))
    return JsonResponse(
        {
            "is_allowed": False,
            "status": "Unauthorized",
            "message": "ID/Password combination invalid.",
        },
        status=401,
    )


def handle_valid_login(account):
    update_last_login_time(account)

    logger.debug("Successful login: {}".format(account))
    return JsonResponse(
        {"is_allowed": True, "committee_id": account.cmtee_id, "email": account.email},
        status=200,
        safe=False,
    )


@api_view(["POST", "GET"])
@authentication_classes([])
@permission_classes([])
def authenticate_login(request):
    if request.method == "GET":
        return JsonResponse({"endpoint_available": E2E_TESTING_LOGIN})

    if not E2E_TESTING_LOGIN:
        return JsonResponse(status=405, safe=False)

    username = request.data.get("username", None)
    password = request.data.get("password", None)
    account = authenticate(
        request=request, username=username, password=password
    )  # Returns an account if the username is found and the password is valid

    if account:
        return handle_valid_login(account)
    else:
        return handle_invalid_login(username)


class LogoutView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        logout(request)
        return Response({}, status=status.HTTP_204_NO_CONTENT)
