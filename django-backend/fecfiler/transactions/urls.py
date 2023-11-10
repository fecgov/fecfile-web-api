from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"", TransactionViewSet, basename="transactions")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("transactions/", include(router.urls))]
