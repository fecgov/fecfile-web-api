from django.urls import path, include
from fecfiler.routers import register_router
from .views import OidcViewSet

router = register_router(trailing_slash=False)
router.register(r"oidc", OidcViewSet, basename="oidc")


# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
