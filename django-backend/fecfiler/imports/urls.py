from django.urls import path, include
from fecfiler.routers import register_router
from .views import ImportsViewSet

router = register_router()
router.register(r"imports", ImportsViewSet, basename="imports")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
