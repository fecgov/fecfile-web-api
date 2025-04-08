from fecfiler.routers import register_router, register_read_only_router
from .views import CommitteeManagementEventViewSet, CommitteeMembershipViewSet, CommitteeViewSet

router = register_router()
router.register(r"committees", CommitteeViewSet, basename="committees")
router.register(
    r"committee-members", CommitteeMembershipViewSet, basename="committee-members"
)

read_only_router = register_read_only_router()
read_only_router.register(
    r"committee-management-events", CommitteeManagementEventViewSet, basename="committee-management-events"
)

# The API URLs are now determined automatically by the router.
urlpatterns = []
urlpatterns += router.urls
urlpatterns += read_only_router.urls
