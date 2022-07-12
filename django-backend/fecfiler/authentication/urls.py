from django.urls import re_path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet
from .authenticate_login import authenticate_login, LogoutView
from .verify_login import verify_login

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"committee/users", AccountViewSet, basename="committee/users")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    re_path("user/login/authenticate", authenticate_login, name="login_authenticate"),
    re_path("user/login/verify", verify_login, name="code-verify-login"),
    re_path("auth/logout/", LogoutView.as_view(), name="logout"),
    re_path("", include(router.urls))
]
