from django.urls import path, include
from fecfiler.routers import register_router
from .views import ContactViewSet, DeletedContactsViewSet, e2e_delete_all_contacts
from django.conf import settings

router = register_router()
router.register(r"contacts", ContactViewSet, basename="contacts")
router.register(r"contacts-deleted", DeletedContactsViewSet, basename="contacts-deleted")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]

if settings.E2E_TEST:
    urlpatterns.append(
        path(
            "contact/e2e-delete-all-contacts",
            e2e_delete_all_contacts,
            name="e2e_delete_all_contacts"
        )
    )
