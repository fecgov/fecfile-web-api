from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet
from .authenticate_login import authenticate_login, LogoutView
from .views import (
    LoginDotGovSuccessSpaRedirect,
    LoginDotGovSuccessLogoutSpaRedirect
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"committee/users", AccountViewSet, basename="committee/users")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/login-redirect", LoginDotGovSuccessSpaRedirect.as_view(),
         name="login-redirect"),
    path("auth/logout-redirect", LoginDotGovSuccessLogoutSpaRedirect.as_view(),
         name="logout-redirect"),
    path("", include(router.urls)),
    path("user/login/authenticate", authenticate_login, name="login_authenticate")
]