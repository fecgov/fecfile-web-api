from django.conf.urls import url, include
from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from rest_framework_nested import routers
from .authentication.authenticate_login import AccountViewSet, LogoutView

router = routers.SimpleRouter()
router.register(r"accounts", AccountViewSet, basename="Accounts")

accounts_router = routers.NestedSimpleRouter(router, r"accounts", lookup="account")

urlpatterns = [
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    url(r"^api/v1/", include(router.urls)),
    url(r"^api/v1/", include(accounts_router.urls)),
    url(r"^api/v2/", include("fecfiler.contacts.urls")),
    url(r"^api/v1/auth/logout/$", LogoutView.as_view(), name="logout"),
    url(r"^api/v1/token/obtain$", obtain_jwt_token),
    url(r"^api/v1/token/refresh$", refresh_jwt_token),
    path("api/v1/", include("fecfiler.triage.urls")),
    path("api/v1/", include("fecfiler.authentication.urls")),
]
