from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebServicesViewSet
from .summary.views import SummaryViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"web-services", WebServicesViewSet, basename="web-services")
router.register(r"web-services/summary", SummaryViewSet, basename="summary")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
