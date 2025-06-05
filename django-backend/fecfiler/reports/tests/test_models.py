from django.test import TestCase
from fecfiler.web_services.models import UploadSubmission
from fecfiler.reports.models import Report, Form24, Form3X
from fecfiler.reports.tests.utils import create_form3x, create_form24
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.transactions.tests.utils import create_ie
from fecfiler.contacts.models import Contact
from fecfiler.transactions.models import Transaction
import structlog

logger = structlog.get_logger(__name__)


class ReportModelTestCase(TestCase):

    def setUp(self):
        self.missing_type_transaction = {}
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.f24_report = create_form24(self.committee)
        self.f3x_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.contact_1 = Contact.objects.create(committee_account_id=self.committee.id)

    def test_amending(self):
        self.f3x_report.amend()
        self.assertEqual(self.f3x_report.form_type, "F3XA")
        self.assertEqual(self.f3x_report.report_version, 1)

        self.f3x_report.amend()
        self.assertEqual(self.f3x_report.report_version, 2)

    def test_amending_f24(self):
        new_upload_submission = UploadSubmission()
        self.f24_report.upload_submission = new_upload_submission

        self.f24_report.amend()

        self.assertEqual(
            self.f24_report.form_24.original_amendment_date, new_upload_submission.created
        )
        self.assertEqual(self.f24_report.form_type, "F24A")

    def test_unamending(self):
        upload_submission = UploadSubmission(fec_report_id=self.f3x_report.report_id)
        upload_submission.save()
        self.f3x_report.upload_submission = upload_submission
        self.f3x_report.save()

        self.f3x_report.amend()
        self.f3x_report.unamend(upload_submission)
        self.assertEqual(self.f3x_report.form_type, "F3XN")
        self.assertEqual(self.f3x_report.report_version, None)
        self.assertEqual(self.f3x_report.upload_submission, upload_submission)

        self.f3x_report.amend()
        new_upload_submission = UploadSubmission(fec_report_id=self.f3x_report.report_id)
        new_upload_submission.save()
        self.f3x_report.upload_submission = new_upload_submission
        self.f3x_report.amend()
        self.f3x_report.unamend(new_upload_submission)
        self.assertEqual(self.f3x_report.form_type, "F3XA")
        self.assertEqual(self.f3x_report.report_version, 1)
        self.assertEqual(self.f3x_report.upload_submission, new_upload_submission)

    def test_delete(self):
        f24_report = create_form24(self.committee)
        f24_report_id = f24_report.id
        f24_id = f24_report.form_24.id
        f3x_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        f3x_report_id = f3x_report.id
        f3x_id = f3x_report.form_3x.id
        candidate_a = Contact.objects.create(
            committee_account_id=self.committee.id,
            candidate_office="H",
            candidate_state="MD",
            candidate_district="99",
        )
        ie = create_ie(
            self.committee,
            candidate_a,
            "2023-01-01",
            "2023-02-01",
            "2023-02-01",
            "123.45",
            "H2024",
            candidate_a,
        )
        ie.reports.set([f24_report_id, f3x_report_id])
        ie.save()
        ie_id = ie.id

        f24_report.delete()
        ie = Transaction.all_objects.filter(id=ie_id).first()
        self.assertIsNone(ie.deleted)
        self.assertFalse(Report.objects.filter(id=f24_report_id).exists())
        self.assertFalse(Form24.objects.filter(id=f24_id).exists())

        f3x_report.delete()
        self.assertFalse(Report.objects.filter(id=f3x_report_id).exists())
        self.assertFalse(Form3X.objects.filter(id=f3x_id).exists())

        ie = Transaction.all_objects.filter(id=ie_id).first()
        self.assertIsNotNone(ie.deleted)
