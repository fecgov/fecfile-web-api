from django.contrib.auth import authenticate, logout
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from rest_framework import permissions, status, views, viewsets
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings
from fecfiler.authentication.token import jwt_payload_handler
from .models import Account
from datetime import datetime, timedelta
from django.http import JsonResponse
from .serializers import AccountSerializer
from .permissions import IsAccountOwner
import logging

logger = logging.getLogger(__name__)


def update_last_login_time(account):
    account.last_login = datetime.now()
    account.save()


def handle_invalid_login(username):
    logger.debug("Unauthorized login attempt: {}".format(username))
    return JsonResponse({
        "is_allowed": False,
        "status": "Unauthorized",
        "message": "ID/Password combination invalid.",
    }, status=401)


def handle_valid_login(account):
    update_last_login_time(account)
    payload = jwt_payload_handler(account)
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    token = jwt_encode_handler(payload)

    logger.debug("Successful login: {}".format(account))
    return JsonResponse({
        "is_allowed": True,
        "committee_id": account.cmtee_id,
        "email": account.email,
        "token": token,
    }, status=200, safe=False)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def authenticate_login(request):
    username = request.data.get("username", None)
    password = request.data.get("password", None)
    account = authenticate(
        request=request, username=username, password=password
    ) ## Returns an account if the username is found and the password is valid

    if account:
        return handle_valid_login(account)
    else:
        return handle_invalid_login(username)


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


class LogoutView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        logout(request)
        return Response({}, status=status.HTTP_204_NO_CONTENT)
