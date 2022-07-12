from django.urls import re_path, include
from rest_framework.routers import DefaultRouter
from .views import WebServicesViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"web-services", WebServicesViewSet, basename="web-services")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    re_path("", include(router.urls)),
]
