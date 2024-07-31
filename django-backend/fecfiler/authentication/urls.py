from django.urls import path
from .views import (
    authenticate_login,
    authenticate_logout,
)


# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("user/login/authenticate", authenticate_login),
    path("auth/logout", authenticate_logout),
]
