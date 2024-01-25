from django.urls import path, include
from .views import (
    authenticate_login,
    authenticate_logout,
    login_redirect,
    logout_redirect,
)


# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("user/login/authenticate", authenticate_login),
    path("auth/logout", authenticate_logout),
    path("auth/login-redirect", login_redirect),
    path("auth/logout-redirect", logout_redirect),
]
