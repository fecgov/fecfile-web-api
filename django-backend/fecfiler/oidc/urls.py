from django.urls import path
from .views import (
    login_redirect,
    logout_redirect,
    oidc_authenticate,
    oidc_callback,
    oidc_logout,
)


# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("oidc/login-redirect", login_redirect),
    path("oidc/logout-redirect", logout_redirect),
    path("oidc/authenticate", oidc_authenticate),
    path("oidc/callback", oidc_callback, name="oidc_callback"),
    path("oidc/logout", oidc_logout),
]
