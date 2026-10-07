from django.urls import path, include
from fecfiler.routers import register_router
from .views import ElectionCyclesViewSet

router = register_router()
router.register(r"election-cycles", ElectionCyclesViewSet, basename="election-cycles")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
