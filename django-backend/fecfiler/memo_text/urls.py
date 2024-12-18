from django.urls import path, include
from fecfiler.routers import register_router
from .views import MemoTextViewSet

router = register_router()
router.register(r"memo-text", MemoTextViewSet, basename="memo-text")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
