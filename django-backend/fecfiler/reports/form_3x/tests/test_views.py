from django.test import TestCase, RequestFactory

from fecfiler.reports.models import Report
from ..views import Form3XViewSet, Form3X
from fecfiler.user.models import User
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.reports.tests.utils import create_form3x
from rest_framework.test import force_authenticate


class Form3XViewSetTest(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(email="test@fec.gov", username="gov")
        create_committee_view(self.committee.id)
        self.q1_report = create_form3x(
            self.committee,
            "2004-01-01",
            "2004-02-28",
            {},
            "Q1",
        )
        Form3X.objects.update(L6a_cash_on_hand_jan_1_ytd="333.01")

        self.m4_report = create_form3x(
            self.committee,
            "2005-03-01",
            "2005-03-31",
            {},
            "M4",
        )

        self.my_report = create_form3x(
            self.committee,
            "2006-01-30",
            "2006-02-28",
            {},
            "MY",
        )

        self.twelve_c_report = create_form3x(
            self.committee,
            "2007-01-30",
            "2007-02-28",
            {},
            "12C",
        )
        self.factory = RequestFactory()

    def test_coverage_dates_happy_path(self):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/reports/form-f3x/coverage_dates")
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }

        response = Form3XViewSet.as_view({"get": "coverage_dates"})(request)

        expected_json = [
            {
                "coverage_from_date": "2004-01-01",
                "coverage_through_date": "2004-02-28",
                "report_code": "Q1",
            },
            {
                "coverage_from_date": "2005-03-01",
                "coverage_through_date": "2005-03-31",
                "report_code": "M4",
            },
            {
                "coverage_from_date": "2006-01-30",
                "coverage_through_date": "2006-02-28",
                "report_code": "MY",
            },
            {
                "coverage_from_date": "2007-01-30",
                "coverage_through_date": "2007-02-28",
                "report_code": "12C",
            },
        ]

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf8"), expected_json)

    def test_amend(self):
        request = self.factory.post(f"/api/v1/reports/{self.q1_report.id}/amend/")
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        force_authenticate(request, self.user)
        view = Form3XViewSet.as_view({"post": "amend"})
        response = view(request, pk=self.q1_report.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Report.objects.filter(id=self.q1_report.id).first().form_type,
            "F3XA",
        )

    # get_jan1_cash_on_hand

    def test_get_jan1_cash_on_hand_missing_year(self):
        request = self.factory.get(
            f"/api/v1/reports/{self.q1_report.id}/form-3x/jan1_cash_on_hand"
        )
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        force_authenticate(request, self.user)
        view = Form3XViewSet.as_view({"get": "jan1_cash_on_hand"})
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "year query param is required")

    def test_get_jan1_cash_on_hand_happy_path(self):
        request = self.factory.get(
            f"/api/v1/reports/{self.q1_report.id}/form-3x/jan1_cash_on_hand?year=2004"
        )
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        force_authenticate(request, self.user)
        view = Form3XViewSet.as_view({"get": "jan1_cash_on_hand"})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "333.01")

    # update_jan1_cash_on_hand

    def test_update_jan1_cash_on_hand_missing_year(self):
        request = self.factory.put(
            f"/api/v1/reports/{self.q1_report.id}/form-3x/jan1_cash_on_hand",
            {
                "amount": 123,
            },
            "application/json",
        )
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        force_authenticate(request, self.user)
        view = Form3XViewSet.as_view({"put": "jan1_cash_on_hand"})
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content.decode(), "year and amount are required in request body"
        )

    def test_update_jan1_cash_on_hand_missing_no_f3xs_found(self):
        request = self.factory.put(
            f"/api/v1/reports/{self.q1_report.id}/form-3x/jan1_cash_on_hand",
            {
                "year": 1776,
                "amount": 123,
            },
            "application/json",
        )
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        force_authenticate(request, self.user)
        view = Form3XViewSet.as_view({"put": "jan1_cash_on_hand"})
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "no f3x reports found")

    def test_update_jan1_cash_on_hand_happy_path(self):
        request = self.factory.put(
            f"/api/v1/reports/{self.q1_report.id}/form-3x/jan1_cash_on_hand",
            {
                "year": 2004,
                "amount": 123,
            },
            "application/json",
        )
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        force_authenticate(request, self.user)
        view = Form3XViewSet.as_view({"put": "jan1_cash_on_hand"})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        updated_form_3x = Form3X.objects.get(pk=self.q1_report.form_3x.id)
        self.assertEqual(updated_form_3x.L6a_cash_on_hand_jan_1_ytd, 123)
