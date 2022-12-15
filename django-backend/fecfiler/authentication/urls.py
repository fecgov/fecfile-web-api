from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, authenticate_login

# Create a router and register our viewsets with it.
router = DefaultRouter()

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("auth/logout/", AccountViewSet.as_view({"post": "logout"})),
    path("auth/login-redirect", AccountViewSet.as_view({"get": "login_redirect"}),),
    path("auth/logout-redirect", AccountViewSet.as_view({"get": "logout_redirect"}),),
    path("", include(router.urls)),
    path("user/login/authenticate", authenticate_login),
]
