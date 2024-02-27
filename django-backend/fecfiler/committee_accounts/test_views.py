from uuid import UUID
from django.test import RequestFactory, TestCase
from .views import CommitteeMembershipViewSet
from rest_framework import viewsets
from fecfiler.user.models import User


class CommitteeMemberViewSetTest(TestCase, viewsets.ModelViewSet):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_remove_member(self):
        membership_uuid = UUID("136a21f2-66fe-4d56-89e9-0d1d4612741c")
        view = CommitteeMembershipViewSet()
        request = self.factory.get(
            "/api/v1/committee-members/{membership_uuid}/remove-member"
        )
        request.user = self.user
        request.session = {
            "committee_uuid": UUID('11111111-2222-3333-4444-555555555555')}
        request.method = "DELETE"
        request.query_params = dict()
        view.kwargs = {"pk": membership_uuid}
        view.request = request
        response = view.remove_member(
            request, membership_uuid)
        self.assertEqual(response.status_code, 200)
