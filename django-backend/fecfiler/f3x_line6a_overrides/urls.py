from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import F3xLine6aOverrideViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(
    r"f3x_line6a_overrides", F3xLine6aOverrideViewSet, basename="f3x_line6a_overrides"
)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
