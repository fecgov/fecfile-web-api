from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect

from fecfiler.settings import (
    LOGIN_REDIRECT_CLIENT_URL,
    FFAPI_COMMITTEE_ID_COOKIE_NAME,
    FFAPI_EMAIL_COOKIE_NAME,
    FFAPI_COOKIE_DOMAIN,
)


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
        response = HttpResponse(status=204)  # no content
        response.delete_cookie(FFAPI_COMMITTEE_ID_COOKIE_NAME,
                               domain=FFAPI_COOKIE_DOMAIN)
        response.delete_cookie(FFAPI_EMAIL_COOKIE_NAME,
                               domain=FFAPI_COOKIE_DOMAIN)
        return response
