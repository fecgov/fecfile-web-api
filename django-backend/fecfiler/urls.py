from django.conf.urls import include
from django.urls import re_path, path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.views.generic.base import RedirectView
from fecfiler.settings import LOGIN_REDIRECT_CLIENT_URL

BASE_V1_URL = r"^api/v1/"


@api_view(["GET"])
def test_celery(request):
    from fecfiler.celery import debug_task

    debug_task.delay()
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
    re_path(BASE_V1_URL, include("fecfiler.openfec.urls")),
    re_path(BASE_V1_URL, include("fecfiler.user.urls")),
    re_path(BASE_V1_URL, include("fecfiler.feedback.urls")),
    re_path(r"^oidc/", include("mozilla_django_oidc.urls")),
    re_path(r"^celery-test/", test_celery),
    path("", RedirectView.as_view(url=LOGIN_REDIRECT_CLIENT_URL)),
]
