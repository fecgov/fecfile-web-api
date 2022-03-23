from django.conf.urls import url, include
from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .authentication.authenticate_login import AccountViewSet, LogoutView


urlpatterns = [
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    url(r"^api/schema/", SpectacularAPIView.as_view(api_version="v1"), name="schema"),
    url(
        r"^api/docs/",
        SpectacularSwaggerView.as_view(
            template_name="swagger-ui.html", url_name="schema"
        ),
    ),
    url(r"^api/v1/", include("fecfiler.contacts.urls")),
    url(r"^api/v1/auth/logout/$", LogoutView.as_view(), name="logout"),
    url(r"^api/v1/token/obtain$", obtain_jwt_token),
    url(r"^api/v1/token/refresh$", refresh_jwt_token),
    path("api/v1/", include("fecfiler.triage.urls")),
    path("api/v1/", include("fecfiler.authentication.urls")),
]
