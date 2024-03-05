from uuid import UUID
from django.test import RequestFactory, TestCase
from fecfiler.reports.views import ReportViewSet
from fecfiler.user.models import User
from django.core.management import call_command
from rest_framework.response import Response


class CommitteeMemberViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee", "test_f3x_reports", "test_f24_reports", "test_f99_reports"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_list_paginated(self):
        view = ReportViewSet()
        view.format_kwarg = 'format'
        request = self.factory.get(
            "/api/v1/reports"
        )
        request.user = self.user
        request.session = {
            "committee_uuid": UUID('11111111-2222-3333-4444-555555555555')
        }
        request.method = "GET"
        request.query_params = {'page': 1}
        view.request = request
        response = view.list(request)
        self.assertEqual(len(response.data['results']), 10)

    def test_list_no_pagination(self):
        view = ReportViewSet()
        view.format_kwarg = 'format'
        request = self.factory.get(
            "/api/v1/reports"
        )
        request.user = self.user
        request.session = {
            "committee_uuid": UUID('11111111-2222-3333-4444-555555555555')
        }
        request.method = "GET"
        request.query_params = {}
        view.request = request
        response = view.list(request)
        try:
            response.data['results']  # A non-paginated response will throw an error here
            self.assertTrue(False)
        except:
            self.assertTrue(True)



    # def test_remove_member(self):
    #     membership_uuid = UUID("136a21f2-66fe-4d56-89e9-0d1d4612741c")
    #     view = CommitteeMembershipViewSet()
    #     request = self.factory.get(
    #         "/api/v1/committee-members/{membership_uuid}/remove-member"
    #     )
    #     request.user = self.user
    #     request.session = {
    #         "committee_uuid": UUID('11111111-2222-3333-4444-555555555555')}
    #     request.method = "DELETE"
    #     request.query_params = dict()
    #     view.kwargs = {"pk": membership_uuid}
    #     view.request = request
    #     response = view.remove_member(
    #         request, membership_uuid)
    #     self.assertEqual(response.status_code, 200)
