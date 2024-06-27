from decimal import Decimal
from django.test import TestCase
from fecfiler.web_services.models import UploadSubmission
from fecfiler.reports.models import Report, Form24, Form3X
from fecfiler.reports.tests.utils import create_form, create_form3x, create_form24
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.transactions.tests.utils import create_ie, create_debt
from fecfiler.contacts.models import Contact
from fecfiler.transactions.models import Transaction
import structlog

logger = structlog.get_logger(__name__)


class ReportModelTestCase(TestCase):

    def setUp(self):
        self.missing_type_transaction = {}
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
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

        self.assertEquals(
            self.f24_report.form_24.original_amendment_date, new_upload_submission.created
        )
        self.assertEquals(self.f24_report.form_type, "F24A")

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

    def test_can_delete(self):
        q1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        # Test when conditions are met for deletion
        self.assertTrue(q1_report.can_delete())

        # Test when upload_submission exists
        upload_submission = UploadSubmission()
        q1_report.upload_submission = upload_submission
        self.assertFalse(q1_report.can_delete())
        q1_report.upload_submission = None

        # Test when report_version is not None, "0", or 0
        q1_report.report_version = "1"
        self.assertFalse(q1_report.can_delete())
        q1_report.report_version = "0"

        # Test when form_24, form_1m, or form_99 exists with Form 3x
        f24_form = create_form(Form24, {})
        q1_report.form_24 = f24_form
        self.assertFalse(q1_report.can_delete())
        q1_report.form_24 = None

        # Test when there exists a transaction in this report
        # where any transactions in a different report back reference to them
        debt = create_debt(self.committee, self.contact_1, Decimal("123.00"))
        q2_report = create_form3x(self.committee, "2024-03-01", "2024-05-01", {})
        debt.reports.add(q1_report)
        debt.reports.add(q2_report)
        self.assertFalse(q2_report.can_delete())
