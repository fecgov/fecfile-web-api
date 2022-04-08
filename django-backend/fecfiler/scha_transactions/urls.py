from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SchATransaction

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"sch-a-transactions", SchATransaction, basename="sch-a-transactions")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
