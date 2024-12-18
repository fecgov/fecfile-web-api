from django.urls import include, path
from fecfiler.routers import register_router
from fecfiler.devops.views import SystemStatusViewSet

router = register_router()
router.register(r"devops", SystemStatusViewSet, basename="devops")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
