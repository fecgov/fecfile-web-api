from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, DeletedContactsVeiwSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contacts")
router.register(
    r"contacts-deleted", DeletedContactsVeiwSet, basename="contacts-deleted"
)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
