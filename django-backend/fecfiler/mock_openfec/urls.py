from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MockOpenfecViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"mock_openfec", MockOpenfecViewSet, basename="mock_openfec")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
