from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import force_authenticate

from fecfiler.web_services.views import WebServicesViewSet
from fecfiler.user.models import User
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.web_services.summary.tasks import CalculationState

import math
from unittest.mock import patch
from uuid import UUID


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
class WebServicesViewSetTest(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
        "test_f3x_reports",
    ]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        self.committee.members.add(self.user)
        self.factory = RequestFactory()
        self.view = WebServicesViewSet()
        self.task_id = "testTaskId"

    def test_create_dot_fec(self):
        report = create_form3x(
            self.committee, "2024-01-01", "2024-02-01", {"L6a_cash_on_hand_jan_1_ytd": 1}
        )

        request = self.factory.post(
            "/api/v1/web-services/dot-fec/", {"report_id": report.id}
        )
        force_authenticate(request, self.user)
        request.session = {"committee_uuid": self.committee.id}

        response = WebServicesViewSet.as_view({"post": "create_dot_fec"})(request)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

        """view does not recalculate summary if report is not dirty"""
        report.form_3x.L6a_cash_on_hand_jan_1_ytd = 2
        report.calculation_status = CalculationState.SUCCEEDED
        report.save()
        response = WebServicesViewSet.as_view({"post": "create_dot_fec"})(request)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

    def test_submit_to_webprint(self):
        report = create_form3x(
            self.committee, "2024-01-01", "2024-02-01", {"L6a_cash_on_hand_jan_1_ytd": 1}
        )

        request = self.factory.post(
            "/api/v1/web-services/dot-fec/", {"report_id": report.id}
        )
        force_authenticate(request, self.user)
        request.session = {"committee_uuid": self.committee.id}
        response = WebServicesViewSet.as_view({"post": "submit_to_webprint"})(request)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

        """view does not recalculate summary if report is not dirty"""
        report.form_3x.L6a_cash_on_hand_jan_1_ytd = 2
        report.calculation_status = CalculationState.SUCCEEDED
        report.save()
        response = WebServicesViewSet.as_view({"post": "submit_to_webprint"})(request)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

    def test_submit_to_fec(self):
        report = create_form3x(
            self.committee, "2024-01-01", "2024-02-01", {"L6a_cash_on_hand_jan_1_ytd": 1}
        )

        request = self.factory.post(
            "/api/v1/web-services/dot-fec/", {"report_id": report.id, "password": "123"}
        )
        force_authenticate(request, self.user)
        request.session = {"committee_uuid": self.committee.id}
        response = WebServicesViewSet.as_view({"post": "submit_to_fec"})(request)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

        """view does not recalculate summary if report is not dirty"""
        report.form_3x.L6a_cash_on_hand_jan_1_ytd = 2
        report.calculation_status = CalculationState.SUCCEEDED
        report.save()
        response = WebServicesViewSet.as_view({"post": "submit_to_fec"})(request)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

    @patch("fecfiler.web_services.views.AsyncResult")
    def test_check_dot_fec_ready(self, mock_async_result):
        request = self.factory.get(f"api/v1/web-services/dot-fec/check/{self.task_id}")
        mock_instance = mock_async_result.return_value
        mock_instance.ready.return_value = True
        mock_instance.get.return_value = "testId"
        self.view.request = request
        response = self.view.check_dot_fec(request, self.task_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"done": True, "id": "testId"})

    @patch("fecfiler.web_services.views.AsyncResult")
    def test_check_dot_fec_not_ready(self, mock_async_result):
        request = self.factory.get(f"api/v1/web-services/dot-fec/check/{self.task_id}")
        mock_instance = mock_async_result.return_value
        mock_instance.ready.return_value = False
        mock_instance.get.return_value = "testId"
        self.view.request = request
        response = self.view.check_dot_fec(request, self.task_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"done": False})

    def test_get_dot_fec_not_exists(self):
        id = "b6d60d2d-d926-4e89-ad4b-c47d152a66ae"

        request = self.factory.get(f"api/v1/web-services/dot-fec/{id}")
        request.session = {
            "committee_uuid": UUID("11111111-2222-3333-4444-555555555555"),
            "committee_id": "C01234567",
        }
        force_authenticate(request, user=self.user)
        response = self.view.get_dot_fec(request, id)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, f"No .FEC was found for id: {id}")
