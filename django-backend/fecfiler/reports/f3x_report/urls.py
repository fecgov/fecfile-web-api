from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import F3XReportViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"f3x-reports", F3XReportViewSet, basename="f3x-reports")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
