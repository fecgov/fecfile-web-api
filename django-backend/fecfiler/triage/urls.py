from django.urls import path
from .get_committee import get_committee_details
from .authenticate_login import authenticate_login
from .verify_login import verify_login

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("core/get_committee_details", get_committee_details),
    path("user/login/authenticate", authenticate_login, name="login_authenticate"),
    path("user/login/verify", verify_login, name="code-verify-login"),
]
