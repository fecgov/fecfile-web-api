from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .schedule_a.views import ScheduleATransactionViewSet, ScheduleAViewSet
from .schedule_b.views import ScheduleBTransactionViewSet
from .views import TransactionViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"schedule-a", ScheduleATransactionViewSet, basename="schedule-a")
router.register(r"a", ScheduleAViewSet, basename="a")
router.register(r"schedule-b", ScheduleBTransactionViewSet, basename="schedule-b")
router.register(r"", TransactionViewSet, basename="transactions")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("transactions/", include(router.urls))]
