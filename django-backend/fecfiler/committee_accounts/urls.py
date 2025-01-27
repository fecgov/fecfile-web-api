from fecfiler.routers import register_router
from .views import CommitteeMembershipViewSet, CommitteeViewSet

router = register_router()
router.register(r"committees", CommitteeViewSet, basename="committees")
router.register(
    r"committee-members", CommitteeMembershipViewSet, basename="committee-members"
)

# The API URLs are now determined automatically by the router.
urlpatterns = []
urlpatterns += router.urls
