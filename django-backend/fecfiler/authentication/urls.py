from django.urls import path
from .authenticate_login import authenticate_login, LogoutView
from .verify_login import verify_login
from .views import (
    LoginDotGovSuccessSpaRedirect,
    LoginDotGovSuccessLogoutSpaRedirect
)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("user/login/authenticate", authenticate_login,
         name="login_authenticate"),
    path("user/login/verify", verify_login, name="code-verify-login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/login-redirect", LoginDotGovSuccessSpaRedirect.as_view(),
         name="login-redirect"),
    path("auth/logout-redirect", LoginDotGovSuccessLogoutSpaRedirect.as_view(),
         name="logout-redirect"),
]
