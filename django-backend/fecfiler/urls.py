from django.conf.urls import include
from django.urls import re_path
from rest_framework.decorators import api_view
from rest_framework.response import Response
#from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .authentication.authenticate_login import LogoutView

BASE_V1_URL = r"^api/v1/"


@api_view(["GET"])
def test_celery(request):
    from fecfiler.celery import debug_task

    debug_task.delay()
    return Response(status=200)


urlpatterns = [
    re_path(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    re_path(r"^api/schema/", SpectacularAPIView.as_view(api_version="v1"), name="schema"),
    re_path(
        r"^api/docs/",
        SpectacularSwaggerView.as_view(
            template_name="swagger-ui.html", url_name="schema"
        ),
    ),
    re_path(BASE_V1_URL, include("fecfiler.contacts.urls")),
    re_path(BASE_V1_URL, include("fecfiler.f3x_summaries.urls")),
    re_path(BASE_V1_URL, include("fecfiler.scha_transactions.urls")),
    re_path(BASE_V1_URL, include("fecfiler.memo_text.urls")),
    re_path(r"^api/v1/auth/logout/$", LogoutView.as_view(), name="logout"),
#    re_path(r"^api/v1/token/obtain$", obtain_jwt_token),
#    re_path(r"^api/v1/token/refresh$", refresh_jwt_token),
    re_path(r"^api/v1/token/obtain$", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path(r"^api/v1/token/refresh$", TokenRefreshView.as_view(), name='token_refresh'),
    re_path(BASE_V1_URL, include("fecfiler.triage.urls")),
    re_path(BASE_V1_URL, include("fecfiler.authentication.urls")),
    re_path(BASE_V1_URL, include("fecfiler.web_services.urls")),
    re_path(r"^oidc/", include('mozilla_django_oidc.urls')),
    re_path(r"^celery-test/", test_celery),
]
