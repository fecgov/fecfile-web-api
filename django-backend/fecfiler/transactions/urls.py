from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .schedule_a.views import ScheduleATransactionViewSet
from .schedule_b.views import ScheduleBTransactionViewSet
from .schedule_c.views import ScheduleCTransactionViewSet
from .schedule_c1.views import ScheduleC1TransactionViewSet
from .schedule_c2.views import ScheduleC2TransactionViewSet
from .schedule_d.views import ScheduleDTransactionViewSet
from .schedule_e.views import ScheduleETransactionViewSet
from .views import TransactionViewSet, TransactionViewSet2

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"schedule-a", ScheduleATransactionViewSet, basename="schedule-a")
router.register(r"schedule-b", ScheduleBTransactionViewSet, basename="schedule-b")
router.register(r"schedule-c", ScheduleCTransactionViewSet, basename="schedule-c")
router.register(r"schedule-c1", ScheduleC1TransactionViewSet, basename="schedule-c1")
router.register(r"schedule-c2", ScheduleC2TransactionViewSet, basename="schedule-c2")
router.register(r"schedule-d", ScheduleDTransactionViewSet, basename="schedule-d")
router.register(r"schedule-e", ScheduleETransactionViewSet, basename="schedule-e")
router.register(r"transactions2", TransactionViewSet2, basename="transactions2")
router.register(r"", TransactionViewSet, basename="transactions")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("transactions/", include(router.urls))]
