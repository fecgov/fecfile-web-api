from django.urls import path, include
from fecfiler.routers import register_router
from .views import SystemAdministrationViewset

router = register_router()
router.register(r"admin", SystemAdministrationViewset, basename="admin")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
