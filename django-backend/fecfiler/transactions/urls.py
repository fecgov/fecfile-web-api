from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .schedule_a.views import ScheduleATransactionViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"schedule-a", ScheduleATransactionViewSet, basename="schedule-a")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("transactions/", include(router.urls))]
