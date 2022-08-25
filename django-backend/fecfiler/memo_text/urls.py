from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MemoTextViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"memo-text", MemoTextViewSet,
                basename="memo-text")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
