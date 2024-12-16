from django.urls import path, include
from fecfiler.routers import register_router
from .views import TransactionViewSet

router = register_router()
router.register(r"", TransactionViewSet, basename="transactions")

# The API URLs are now determined automatically by the router.
urlpatterns = [path("transactions/", include(router.urls))]
