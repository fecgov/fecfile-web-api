from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FeedbackViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"feedback", FeedbackViewSet, basename="feedback")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
