from datetime import datetime
from django.test import override_settings

from fecfiler.web_services.views import WebServicesViewSet
from fecfiler.user.models import User
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.cash_on_hand.tests.utils import create_cash_on_hand_yearly
from fecfiler.reports.tests.utils import (
    create_form3x,
    create_form24,
    create_form99,
    create_form1m,
)
from fecfiler.web_services.summary.tasks import CalculationState
from fecfiler.shared.viewset_test import FecfilerViewSetTest
from fecfiler.web_services.models import (
    UploadSubmission,
    WebPrintSubmission,
    FECSubmissionState,
)
from unittest.mock import patch


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
class WebServicesViewSetTest(FecfilerViewSetTest):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        user = User.objects.create(email="test@fec.gov", username="gov")
        self.committee.members.add(user)
        super().set_default_user(user)
        super().set_default_committee(self.committee)
        super().setUp()

        self.view = WebServicesViewSet()
        self.task_id = "testTaskId"

    def test_create_dot_fec(self):
        create_cash_on_hand_yearly(
            committee_account=self.committee,
            year="2024",
            cash_on_hand=1,
        )
        report = create_form3x(self.committee, "2024-01-01", "2024-02-01")

        response = self.send_viewset_post_request(
            "/api/v1/web-services/dot-fec/",
            {"report_id": report.id},
            WebServicesViewSet,
            "create_dot_fec",
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

        """view does not recalculate summary if report is not dirty"""
        report.form_3x.L6a_cash_on_hand_jan_1_ytd = 2
        report.calculation_status = CalculationState.SUCCEEDED
        report.save()

        response = self.send_viewset_post_request(
            "/api/v1/web-services/dot-fec/",
            {"report_id": report.id},
            WebServicesViewSet,
            "create_dot_fec",
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

    def test_create_dot_fec_form_24(self):
        report = create_form24(self.committee)

        response = self.send_viewset_post_request(
            "/api/v1/web-services/dot-fec/",
            {"report_id": report.id},
            WebServicesViewSet,
            "create_dot_fec",
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()

    def test_create_dot_fec_form_99(self):
        report = create_form99(self.committee)

        response = self.send_viewset_post_request(
            "/api/v1/web-services/dot-fec/",
            {"report_id": report.id},
            WebServicesViewSet,
            "create_dot_fec",
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()

    def test_create_dot_fec_form_1m(self):
        report = create_form1m(self.committee)

        response = self.send_viewset_post_request(
            "/api/v1/web-services/dot-fec/",
            {"report_id": report.id},
            WebServicesViewSet,
            "create_dot_fec",
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()

    def test_submit_to_webprint(self):
        create_cash_on_hand_yearly(
            committee_account=self.committee,
            year="2024",
            cash_on_hand=1,
        )
        report = create_form3x(self.committee, "2024-01-01", "2024-02-01")

        response = self.send_viewset_post_request(
            "/api/v1/web-services/dot-fec/",
            {"report_id": report.id},
            WebServicesViewSet,
            "submit_to_webprint",
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

        """view does not recalculate summary if report is not dirty"""
        report.form_3x.L6a_cash_on_hand_jan_1_ytd = 2
        report.calculation_status = CalculationState.SUCCEEDED
        report.save()

        response = self.send_viewset_post_request(
            "/api/v1/web-services/dot-fec/",
            {"report_id": report.id},
            WebServicesViewSet,
            "submit_to_webprint",
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

    def test_submit_to_fec(self):
        create_cash_on_hand_yearly(
            committee_account=self.committee,
            year="2024",
            cash_on_hand=1,
        )
        report = create_form3x(self.committee, "2024-01-01", "2024-02-01")

        response = self.send_viewset_post_request(
            "/api/v1/web-services/dot-fec/",
            {"report_id": report.id, "password": "123"},
            WebServicesViewSet,
            "submit_to_fec",
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

        """ Because date_signed is timezoned to the server
        the test date needs to be in the same timezone"""
        now = datetime.now().date()
        self.assertEqual(report.date_signed, now)

        """view does not recalculate summary if report is not dirty"""
        report.form_3x.L6a_cash_on_hand_jan_1_ytd = 2
        report.calculation_status = CalculationState.SUCCEEDED
        report.save()

        response = self.send_viewset_post_request(
            "/api/v1/web-services/dot-fec/",
            {"report_id": report.id, "password": "123"},
            WebServicesViewSet,
            "submit_to_fec",
        )
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        # assert that summary was caclulated
        self.assertEqual(report.form_3x.L8_cash_on_hand_at_close_period, 1)

    @patch("fecfiler.web_services.views.AsyncResult")
    def test_check_dot_fec_ready(self, mock_async_result):
        request = self.build_viewset_get_request(
            f"api/v1/web-services/dot-fec/check/{self.task_id}"
        )
        mock_instance = mock_async_result.return_value
        mock_instance.ready.return_value = True
        mock_instance.get.return_value = "testId"
        self.view.request = self.build_viewset_get_request(
            f"api/v1/web-services/dot-fec/check/{self.task_id}"
        )
        response = self.view.check_dot_fec(request, self.task_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"done": True, "id": "testId"})

    @patch("fecfiler.web_services.views.AsyncResult")
    def test_check_dot_fec_not_ready(self, mock_async_result):
        request = self.build_viewset_get_request(
            f"api/v1/web-services/dot-fec/check/{self.task_id}"
        )
        mock_instance = mock_async_result.return_value
        mock_instance.ready.return_value = False
        mock_instance.get.return_value = "testId"
        self.view.request = request
        response = self.view.check_dot_fec(request, self.task_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"done": False})

    def test_get_dot_fec_not_exists(self):
        create_cash_on_hand_yearly(
            committee_account=self.committee,
            year="2024",
            cash_on_hand=1,
        )
        report = create_form3x(self.committee, "2024-01-01", "2024-02-01")
        test_id = report.id
        request = self.build_viewset_get_request(f"api/v1/web-services/dot-fec/{test_id}")
        response = self.view.get_dot_fec(request, test_id)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, f"No .FEC was found for id: {test_id}")

    def test_submit_to_fec_already_running(self):
        """Test that a new submission is blocked if one is already in progress."""
        report = create_form3x(self.committee, "2024-01-01", "2024-02-01")
        # Create an existing submission in a "submitting" state
        upload_submission = UploadSubmission.objects.create(
            fecfile_task_state=FECSubmissionState.SUBMITTING
        )
        report.upload_submission = upload_submission
        report.save()

        response = self.send_viewset_post_request(
            "/api/v1/web-services/submit-to-fec/",
            {"report_id": report.id, "password": "123"},
            WebServicesViewSet,
            "submit_to_fec",
        )

        expected_message = {
            "status": f"""There is already an active upload
                     being generated for report {report.id}"""
        }

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, expected_message)

    def test_submit_to_webprint_already_running(self):
        """Test that a new webprint is blocked if one is already in progress."""
        report = create_form3x(self.committee, "2024-01-01", "2024-02-01")
        # Create an existing submission in a "submitting" state
        webprint_submission = WebPrintSubmission.objects.create(
            fecfile_task_state=FECSubmissionState.SUBMITTING
        )
        report.webprint_submission = webprint_submission
        report.save()

        response = self.send_viewset_post_request(
            "/api/v1/web-services/submit-to-webprint/",
            {"report_id": report.id},
            WebServicesViewSet,
            "submit_to_webprint",
        )

        expected_message = {
            "status": f"""There is already an active webprint being generated
                    for report {report.id}"""
        }

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, expected_message)
