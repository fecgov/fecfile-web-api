from ..views import Form24ViewSet
from fecfiler.user.models import User
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.models import Report
from fecfiler.reports.tests.utils import create_form24
from fecfiler.shared.viewset_test import FecfilerViewSetTest
from fecfiler.web_services.models import FECStatus, UploadSubmission


class Form24ViewSetTest(FecfilerViewSetTest):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        user = User.objects.create(email="test@fec.gov", username="gov")
        super().set_default_user(user)
        super().set_default_committee(self.committee)
        super().setUp()

        self.test_name_1 = "test_name_1"
        self.test_name_2 = "test_name_2"
        self.test_name_3 = "test_name_3"

        self.f24_report_1 = create_form24(self.committee, data={"name": self.test_name_1})
        self.f24_report_2 = create_form24(self.committee, data={"name": self.test_name_2})
        self.f24_report_3 = create_form24(self.committee, data={"name": self.test_name_3})

    def test_validation_check_email_is_valid(self):
        params = f"?name=test_does_not_exist&exclude_ids={self.f24_report_1.id}"
        response = self.send_viewset_get_request(
            "/api/v1/reports/form-24/validation_check/" + params,
            Form24ViewSet,
            "validation_check",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["valid"])

    def test_validation_check_email_is_invalid(self):
        params = "?name=test_name_2&exclude_ids=" + str(self.f24_report_1.id)
        response = self.send_viewset_get_request(
            "/api/v1/reports/form-24/validation_check/" + params,
            Form24ViewSet,
            "validation_check",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["valid"])

    def test_list_in_progress(self):
        submission = UploadSubmission.objects.create(
            fec_status=FECStatus.ACCEPTED,
        )
        self.f24_report_1.upload_submission = submission
        self.f24_report_1.save()
        response = self.send_viewset_get_request(
            "/api/v1/reports/form-24/?in_progress=true",
            Form24ViewSet,
            "list",
        )
        self.assertEqual(response.status_code, 200)
        report_ids = [r["id"] for r in response.data["results"]]
        self.assertNotIn(str(self.f24_report_1.id), report_ids)
        self.assertIn(str(self.f24_report_2.id), report_ids)
        self.assertIn(str(self.f24_report_3.id), report_ids)

    def test_pagination_page_size(self):
        from fecfiler.reports.views import ReportViewSet

        self.assertEqual(Form24ViewSet.pagination_class.page_size, 100)
        self.assertEqual(ReportViewSet.pagination_class.page_size, 10)
