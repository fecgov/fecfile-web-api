from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommitteeViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"", CommitteeViewSet, basename="committees")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("committees/", include(router.urls))]
