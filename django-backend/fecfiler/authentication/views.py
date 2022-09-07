from django.views.generic import View
from django.http import HttpResponseRedirect

from fecfiler.settings import (
    LOGIN_REDIRECT_CLIENT_URL,
    FFAPI_COMMITTEE_ID_COOKIE_NAME,
    FFAPI_EMAIL_COOKIE_NAME,
    FFAPI_COOKIE_DOMAIN,
)

from rest_framework import filters
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from .models import Account
from .serializers import AccountSerializer
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
        "name"
    ]
    ordering = ["name"]

    def get_queryset(self):
        queryset = Account.objects.annotate(
            name=Concat('last_name', Value(', '), 'first_name', output_field=CharField())
        ).filter(cmtee_id=self.request.user.cmtee_id).all()

        return queryset


class LoginDotGovSuccessSpaRedirect(View):
    def get(self, request, *args, **kwargs):
        redirect = HttpResponseRedirect(LOGIN_REDIRECT_CLIENT_URL)
        redirect.set_cookie(FFAPI_COMMITTEE_ID_COOKIE_NAME,
                            request.user.cmtee_id,
                            domain=FFAPI_COOKIE_DOMAIN,
                            secure=True)
        redirect.set_cookie(FFAPI_EMAIL_COOKIE_NAME,
                            request.user.email,
                            domain=FFAPI_COOKIE_DOMAIN,
                            secure=True)
        return redirect


class LoginDotGovSuccessLogoutSpaRedirect(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponseRedirect(LOGIN_REDIRECT_CLIENT_URL)
        response.delete_cookie(FFAPI_COMMITTEE_ID_COOKIE_NAME,
                               domain=FFAPI_COOKIE_DOMAIN)
        response.delete_cookie(FFAPI_EMAIL_COOKIE_NAME,
                               domain=FFAPI_COOKIE_DOMAIN)
        return response
