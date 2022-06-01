from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect


class LoginDotGovSuccessSpaRedirect(View):
    def get(self, request, *args, **kwargs):
        redirect = HttpResponseRedirect("http://localhost:4200/dashboard")
        redirect.set_cookie("ffapi_jwt", self.request.session.get("oidc_id_token"))
        return redirect

class LoginDotGovSuccessLogoutSpaRedirect(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(status=204) # no content