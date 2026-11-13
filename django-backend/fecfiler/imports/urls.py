from django.urls import path, include
from fecfiler.routers import register_router
from .views import ImportViewSet

router = register_router()
router.register(r"imports", ImportViewSet, basename="imports")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
