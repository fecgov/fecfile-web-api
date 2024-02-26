from rest_framework.routers import DefaultRouter
from .views import CommitteeMembershipViewSet, CommitteeViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"committees", CommitteeViewSet, basename="committees")
router.register(r"committee-members", CommitteeMembershipViewSet,
                basename="committee-members")

# The API URLs are now determined automatically by the router.
urlpatterns = []
urlpatterns += router.urls
