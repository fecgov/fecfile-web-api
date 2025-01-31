from django.urls import re_path
from drf_spectacular.views import SpectacularAPIView
from fecfiler.openapi.views import FecfileSpectacularSwaggerView

urlpatterns = [
    re_path(r"schema", SpectacularAPIView.as_view(api_version="v1"), name="schema"),
    re_path(
        r"docs",
        FecfileSpectacularSwaggerView.as_view(
            template_name="swagger-ui.html", url_name="schema"
        ),
    ),
]
