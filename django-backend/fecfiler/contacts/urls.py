from django.urls import path, include
from fecfiler.routers import register_router
from .views import ContactViewSet, DeletedContactsViewSet

router = register_router()
router.register(r"contacts", ContactViewSet, basename="contacts")
router.register(r"contacts-deleted", DeletedContactsViewSet, basename="contacts-deleted")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
