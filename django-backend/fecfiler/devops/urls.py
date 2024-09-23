from django.urls import include, path
from rest_framework.routers import DefaultRouter
from fecfiler.devops.views import SystemStatusViewSet


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"devops", SystemStatusViewSet, basename="devops")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
