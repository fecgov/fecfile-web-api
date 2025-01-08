from django.urls import path, include
from fecfiler.routers import register_router
from .views import WebServicesViewSet
from .summary.views import SummaryViewSet

router = register_router()
router.register(r"web-services", WebServicesViewSet, basename="web-services")
router.register(r"web-services/summary", SummaryViewSet, basename="summary")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
