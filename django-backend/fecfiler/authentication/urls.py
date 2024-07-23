from django.urls import path
from .views import (
    authenticate_login,
    authenticate_logout,
    login_redirect,
    logout_redirect,
    oidc_authenticate,
    oidc_callback,
    oidc_logout,
)


# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("user/login/authenticate", authenticate_login),
    path("auth/logout", authenticate_logout),
    path("auth/login-redirect", login_redirect),
    path("auth/logout-redirect", logout_redirect),
    path("oidc/authenticate", oidc_authenticate),
    path("oidc/callback", oidc_callback, name="oidc_callback"),
    path("oidc/logout", oidc_logout),
]
