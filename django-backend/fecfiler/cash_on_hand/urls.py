from django.urls import path, include
from fecfiler.routers import register_router
from .views import CashOnHandYearlyViewSet

router = register_router()
router.register(r"cash_on_hand", CashOnHandYearlyViewSet, basename="cash_on_hand")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
