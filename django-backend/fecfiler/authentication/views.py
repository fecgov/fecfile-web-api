from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect

from fecfiler.settings import (
    LOGIN_REDIRECT_CLIENT_URL,
    FFAPI_JWT_COOKIE_NAME,
    FFAPI_COMMITTEE_ID_COOKIE_NAME,
    FFAPI_EMAIL_COOKIE_NAME,
)


class LoginDotGovSuccessSpaRedirect(View):
    def get(self, request, *args, **kwargs):
        redirect = HttpResponseRedirect(LOGIN_REDIRECT_CLIENT_URL)
        redirect.set_cookie(FFAPI_JWT_COOKIE_NAME,
                            self.request.session.get("oidc_id_token"))
        redirect.set_cookie(FFAPI_COMMITTEE_ID_COOKIE_NAME,
                            request.user.cmtee_id)
        redirect.set_cookie(FFAPI_EMAIL_COOKIE_NAME, request.user.email)
        return redirect


class LoginDotGovSuccessLogoutSpaRedirect(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=204)  # no content
