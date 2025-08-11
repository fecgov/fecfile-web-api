from fecfiler.routers import register_router
from django.urls import include, path
from .views import SSEViewSet

router = register_router()
router.register(r"sse", SSEViewSet, basename="sse")
urlpatterns = [path("", include(router.urls))]
