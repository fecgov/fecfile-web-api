from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CashOnHandYearlyViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"cash_on_hand", CashOnHandYearlyViewSet, basename="cash_on_hand")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
