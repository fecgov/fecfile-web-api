from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommitteeMembershipViewSet, CommitteeViewSet

# Create a router and register our viewsets with it.
committee_router = DefaultRouter()
committee_router.register(r"", CommitteeViewSet, basename="committees")

members_router = DefaultRouter()
members_router.register(r"", CommitteeMembershipViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [path(r"committees/", include(committee_router.urls)), path(r"committee-members/", include(members_router.urls))]
