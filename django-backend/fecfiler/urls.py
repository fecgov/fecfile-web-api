from django.conf.urls import url, include
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .authentication.authenticate_login import LogoutView

BASE_V1_URL = r"^api/v1/"


@api_view(["GET"])
def test_celery(request):
    from fecfiler.celery import debug_task

    debug_task.delay()
    return Response(status=200)


urlpatterns = [
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    url(r"^api/schema/", SpectacularAPIView.as_view(api_version="v1"), name="schema"),
    url(
        r"^api/docs/",
        SpectacularSwaggerView.as_view(
            template_name="swagger-ui.html", url_name="schema"
        ),
    ),
    url(BASE_V1_URL, include("fecfiler.contacts.urls")),
    url(BASE_V1_URL, include("fecfiler.f3x_summaries.urls")),
    url(BASE_V1_URL, include("fecfiler.scha_transactions.urls")),
    url(r"^api/v1/auth/logout/$", LogoutView.as_view(), name="logout"),
    url(r"^api/v1/token/obtain$", obtain_jwt_token),
    url(r"^api/v1/token/refresh$", refresh_jwt_token),
    path(BASE_V1_URL, include("fecfiler.triage.urls")),
    path(BASE_V1_URL, include("fecfiler.authentication.urls")),
    path(BASE_V1_URL, include("fecfiler.web_services.urls")),
    url(r"^celery-test/", test_celery),
]
