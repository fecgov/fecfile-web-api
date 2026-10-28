from ..views import Form3XViewSet
from ..models import Form3X
from fecfiler.user.models import User
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.shared.viewset_test import FecfilerViewSetTest


class Form3XViewSetTest(FecfilerViewSetTest):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        user = User.objects.create(email="test@fec.gov", username="gov")
        super().set_default_user(user)
        super().set_default_committee(self.committee)
        super().setUp()

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

    def test_coverage_dates_happy_path(self):
        self.assertEqual(True, True)
        response = self.send_viewset_get_request(
            "/api/v1/reports/form-f3x/coverage_dates",
            Form3XViewSet,
            "coverage_dates",
        )

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

    def test_associated_no_dates(self):
        response = self.send_viewset_get_request(
            "/api/v1/reports/form-f3x/associated/",
            Form3XViewSet,
            "get_associated_form3x_report",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data)

    def test_associated_empty_dates(self):
        response = self.send_viewset_get_request(
            "/api/v1/reports/form-f3x/associated/?disbursement_date=&dissemination_date=",
            Form3XViewSet,
            "get_associated_form3x_report",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data)

    def test_associated_disbursement_date_happy_path(self):
        response = self.send_viewset_get_request(
            "/api/v1/reports/form-f3x/associated/?disbursement_date=2004-02-01",
            Form3XViewSet,
            "get_associated_form3x_report",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.q1_report.id))

    def test_associated_dissemination_date_happy_path(self):
        response = self.send_viewset_get_request(
            "/api/v1/reports/form-f3x/associated/?dissemination_date=2005-03-02",
            Form3XViewSet,
            "get_associated_form3x_report",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.m4_report.id))

    def test_final(self):
        request = self.build_viewset_get_request("/api/v1/reports/form-f3x/final")
        request.query_params = {"year": "2004"}
        view = Form3XViewSet.as_view({"get": "get_final_report"})
        view.request = request
        view.request.GET = {"year": "2004"}
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["coverage_from_date"], "2004-01-01")

        create_form3x(
            self.committee,
            "2004-05-28",
            "2004-05-30",
            {},
            "Q2",
        )
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["coverage_from_date"], "2004-05-28")

    def test_CRUD_committee_locked_update(self):
        other_committee = CommitteeAccount(
            committee_id="C12344321", id="55555555-4444-3333-2222-111111111111"
        )

        other_committee.save()

        report = create_form3x(
            self.committee,
            "2024-01-01",
            "2024-02-01",
            {},
            report_code="Q1",
        )

        response = self.send_viewset_put_request(
            f"/api/v1/reports/form3x/{str(report.id)}/",
            {
                "report_code": "Q2",
                "form_type": "F3XN",
                "treasurer_last_name": "Treasurer",
                "treasurer_first_name": "Mr",
                "date_signed": "2004-01-01",
                "coverage_from_date": "2025-01-01",
                "coverage_through_date": "2025-02-01",
            },
            Form3XViewSet,
            "update",
            pk=report.id,
            committee=other_committee,
        )

        self.assertEqual(response.status_code, 404)

    def test_update_ignores_id_in_request_body(self):
        """The report updated must always be the one addressed by the URL.  A
        different ``id`` in the request body must be ignored - otherwise a caller
        could overwrite (and take ownership of) another committee's report."""
        other_committee = CommitteeAccount.objects.create(committee_id="C09999999")
        other_report = create_form3x(
            other_committee, "2024-01-01", "2024-03-31", {}, report_code="Q1"
        )
        own_report = create_form3x(
            self.committee, "2024-01-01", "2024-03-31", {}, report_code="Q1"
        )

        response = self.send_viewset_put_request(
            f"/api/v1/reports/form3x/{str(own_report.id)}/",
            {
                "id": str(other_report.id),
                "report_code": "Q2",
                "form_type": "F3XN",
                "treasurer_last_name": "Changed",
                "treasurer_first_name": "Name",
                "date_signed": "2004-01-01",
                "coverage_from_date": "2025-01-01",
                "coverage_through_date": "2025-02-01",
            },
            Form3XViewSet,
            "update",
            pk=own_report.id,
        )
        self.assertEqual(response.status_code, 200)

        # The other committee's report is untouched
        other_report.refresh_from_db()
        self.assertEqual(other_report.committee_account_id, other_committee.id)
        self.assertEqual(str(other_report.coverage_from_date), "2024-01-01")
        self.assertNotEqual(other_report.treasurer_last_name, "Changed")

        # The report addressed by the URL received the update
        own_report.refresh_from_db()
        self.assertEqual(own_report.treasurer_last_name, "Changed")
        self.assertEqual(str(own_report.coverage_from_date), "2025-01-01")
        self.assertEqual(response.data["id"], str(own_report.id))
