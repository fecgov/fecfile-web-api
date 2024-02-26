from fecfiler.user.models import User
from django.test import RequestFactory, TestCase
from .views import CommitteeMembershipViewSet


class CommitteeMemberViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def xtest_remove_member(self):
        request = self.factory.get(
            "/api/v1/committee-members/12345678-aaaa-bbbb-cccc-111122223333/remove-member"
        )
        request.user = self.user
        request.session = {
            "committee_uuid": "11111111-2222-3333-4444-555555555555"}
        request.method = "DELETE"
        response = CommitteeMembershipViewSet.remove_member(
            self, request, "12345678-aaaa-bbbb-cccc-111122223333")
        self.assertEqual(response.status_code, 200)
