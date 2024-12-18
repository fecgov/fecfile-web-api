from django.urls import include, path
from fecfiler.routers import register_router

from .views import FeedbackViewSet

router = register_router()
router.register(r"feedback", FeedbackViewSet, basename="feedback")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
