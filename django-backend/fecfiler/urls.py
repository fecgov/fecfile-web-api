from django.conf.urls import include
from django.urls import re_path, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.views.generic.base import RedirectView
from fecfiler.settings import LOGIN_REDIRECT_CLIENT_URL, ALTERNATIVE_LOGIN
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

BASE_V1_URL = r"^api/v1/"


@api_view(["GET", "HEAD"])
@permission_classes([])
def get_api_status(_request):
    return Response(status=200)


urlpatterns = [
    re_path(r"^api/schema/", SpectacularAPIView.as_view(api_version="v1"), name="schema"),
    re_path(
        r"^api/docs/",
        SpectacularSwaggerView.as_view(
            template_name="swagger-ui.html", url_name="schema"
        ),
    ),
    re_path(BASE_V1_URL, include("fecfiler.committee_accounts.urls")),
    re_path(BASE_V1_URL, include("fecfiler.contacts.urls")),
    re_path(BASE_V1_URL, include("fecfiler.reports.urls")),
    re_path(BASE_V1_URL, include("fecfiler.memo_text.urls")),
    re_path(BASE_V1_URL, include("fecfiler.transactions.urls")),
    re_path(BASE_V1_URL, include("fecfiler.authentication.urls")),
    re_path(BASE_V1_URL, include("fecfiler.web_services.urls")),
    re_path(BASE_V1_URL, include("fecfiler.user.urls")),
    re_path(BASE_V1_URL, include("fecfiler.feedback.urls")),
    re_path(BASE_V1_URL, include("fecfiler.oidc.urls")),
    re_path(BASE_V1_URL, include("fecfiler.f3x_line6a_overrides.urls")),
    re_path(r"", include("fecfiler.devops.urls")),
    path("", RedirectView.as_view(url=LOGIN_REDIRECT_CLIENT_URL)),
    re_path(BASE_V1_URL + "status/", get_api_status),
]

if ALTERNATIVE_LOGIN == "USERNAME_PASSWORD":
    urlpatterns.append(re_path(BASE_V1_URL, include("fecfiler.mock_oidc_provider.urls")))
