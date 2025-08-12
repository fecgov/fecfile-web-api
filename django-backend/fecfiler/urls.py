from django.conf.urls import include
from django.urls import re_path, path
from django.views.generic.base import RedirectView
from fecfiler.settings import MOCK_OIDC_PROVIDER

BASE_V1_URL = r"^api/v1/"


urlpatterns = [
    re_path(r"^api/", include("fecfiler.openapi.urls")),
    re_path(BASE_V1_URL, include("fecfiler.committee_accounts.urls")),
    re_path(BASE_V1_URL, include("fecfiler.contacts.urls")),
    re_path(BASE_V1_URL, include("fecfiler.reports.urls")),
    re_path(BASE_V1_URL, include("fecfiler.imports.urls")),
    re_path(BASE_V1_URL, include("fecfiler.memo_text.urls")),
    re_path(BASE_V1_URL, include("fecfiler.transactions.urls")),
    re_path(BASE_V1_URL, include("fecfiler.web_services.urls")),
    re_path(BASE_V1_URL, include("fecfiler.user.urls")),
    re_path(BASE_V1_URL, include("fecfiler.feedback.urls")),
    re_path(BASE_V1_URL, include("fecfiler.oidc.urls")),
    re_path(BASE_V1_URL, include("fecfiler.cash_on_hand.urls")),
    path("", RedirectView.as_view(url="/api/docs/")),
    re_path(r"", include("fecfiler.devops.urls")),
]

if MOCK_OIDC_PROVIDER:
    urlpatterns.append(re_path(BASE_V1_URL, include("fecfiler.mock_oidc_provider.urls")))
