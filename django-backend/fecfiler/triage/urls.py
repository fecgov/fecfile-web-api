from django.urls import path
from .get_committee import get_committee_details

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("core/get_committee_details", get_committee_details),
]
