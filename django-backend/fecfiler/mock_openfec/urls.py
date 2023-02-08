from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MockCommitteeDetailViewSet, MockRecentFilingsViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"committee", MockCommitteeDetailViewSet,
                basename="committee")
router.register(r"filings", MockRecentFilingsViewSet,
                basename="filings")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("mock_openfec/", include(router.urls)),
]
