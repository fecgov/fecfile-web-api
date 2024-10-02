from django.urls import path
from .views import (
    discovery,
    certs,
    authorize,
    token,
    userinfo,
    logout,
)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path(
        "mock_oidc_provider/.well-known/openid-configuration",
        discovery,
        name="discovery",
    ),
    path("mock_oidc_provider/certs", certs, name="certs"),
    path("mock_oidc_provider/authorize", authorize, name="authorize"),
    path("mock_oidc_provider/token", token, name="token"),
    path("mock_oidc_provider/userinfo", userinfo, name="userinfo"),
    path("mock_oidc_provider/logout", logout, name="logout"),
]
