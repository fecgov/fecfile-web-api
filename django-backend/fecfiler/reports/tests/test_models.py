from django.test import TestCase
from fecfiler.web_services.models import UploadSubmission
from fecfiler.reports.models import Report


class ReportModelTestCase(TestCase):
    fixtures = ["C01234567_user_and_committee", "test_f3x_reports", "test_f24_reports"]

    def setUp(self):
        self.missing_type_transaction = {}

    def test_amending(self):
        f3x_report = Report.objects.get(id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae")

        f3x_report.amend()
        self.assertEqual(f3x_report.form_type, "F3XA")
        self.assertEqual(f3x_report.report_version, 1)

        f3x_report.amend()
        self.assertEqual(f3x_report.report_version, 2)

    def test_amending_f24(self):
        f24_report = Report.objects.get(id="10000f24-d926-4e89-ad4b-000000000001")
        new_upload_submission = UploadSubmission()
        f24_report.upload_submission = new_upload_submission

        f24_report.amend()

        self.assertEquals(
            f24_report.form_24.original_amendment_date, new_upload_submission.created
        )
        self.assertEquals(f24_report.form_type, "F24A")

    def test_delete(self):
        f24_report = Report.objects.get(id="10000f24-d926-4e89-ad4b-000000000001")
        f24_report.delete()

        self.assertFalse(
            Report.objects.filter(id="10000f24-d926-4e89-ad4b-000000000001").exists()
        )

        f3x_report = Report.objects.get(id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae")
        f3x_report.delete()

        self.assertFalse(
            Report.objects.filter(id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae").exists()
        )
