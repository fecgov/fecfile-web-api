from django.urls import path
from .authenticate_login import authenticate_login, LogoutView
from .verify_login import verify_login

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("user/login/authenticate", authenticate_login, name="login_authenticate"),
    path("user/login/verify", verify_login, name="code-verify-login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
]
