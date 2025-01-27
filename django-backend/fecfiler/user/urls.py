from django.urls import path, include
from fecfiler.routers import register_router
from .views import UserViewSet

router = register_router()
router.register(r"users", UserViewSet, basename="users")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
