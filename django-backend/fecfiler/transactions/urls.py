from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .schedule_a.views import ScheduleATransactionViewSet
from .schedule_b.views import ScheduleBTransactionViewSet
from .schedule_c.views import ScheduleCTransactionViewSet
from .schedule_c2.views import ScheduleC2TransactionViewSet
from .views import TransactionViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"schedule-a", ScheduleATransactionViewSet, basename="schedule-a")
router.register(r"schedule-b", ScheduleBTransactionViewSet, basename="schedule-b")
router.register(r"schedule-c", ScheduleCTransactionViewSet, basename="schedule-c")
router.register(r"schedule-c2", ScheduleC2TransactionViewSet, basename="schedule-c2")
router.register(r"", TransactionViewSet, basename="transactions")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("transactions/", include(router.urls))]
