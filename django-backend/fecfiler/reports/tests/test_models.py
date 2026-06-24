from django.test import TestCase
from fecfiler.web_services.models import UploadSubmission
from fecfiler.reports.models import Report, Form24, Form3X
from fecfiler.reports.tests.utils import create_form3x, create_form24
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.transactions.tests.utils import (
    create_ie,
    create_debt,
    create_loan_from_bank
)
from fecfiler.contacts.models import Contact
from fecfiler.contacts.tests.utils import create_test_organization_contact
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_c.utils import carry_forward_loans
from fecfiler.transactions.schedule_d.utils import carry_forward_debts
import structlog

logger = structlog.get_logger(__name__)


class ReportModelTestCase(TestCase):

    def setUp(self):
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
        new_upload_submission.save()
        self.f24_report.upload_submission = new_upload_submission

        self.f24_report.amend()

        self.assertEqual(
            self.f24_report.form_24.original_amendment_date, new_upload_submission.created
        )
        self.assertEqual(self.f24_report.form_type, "F24A")

    def test_unamending(self):
        upload_submission = UploadSubmission(fec_report_id=self.f3x_report.fec_report_id)
        upload_submission.save()
        self.f3x_report.upload_submission = upload_submission
        self.f3x_report.save()

        self.f3x_report.refresh_from_db()
        self.assertTrue(self.f3x_report.can_delete)

        self.f3x_report.amend()

        self.f3x_report.refresh_from_db()
        self.assertFalse(self.f3x_report.can_delete)

        self.f3x_report.unamend()

        self.f3x_report.refresh_from_db()
        self.assertTrue(self.f3x_report.can_delete)
        self.assertEqual(self.f3x_report.form_type, "F3XN")
        self.assertEqual(self.f3x_report.report_version, None)
        self.assertEqual(self.f3x_report.upload_submission, upload_submission)

        self.f3x_report.amend()
        new_upload_submission = UploadSubmission(
            fec_report_id=self.f3x_report.fec_report_id
        )
        new_upload_submission.save()
        self.f3x_report.upload_submission = new_upload_submission
        self.f3x_report.amend()
        self.f3x_report.unamend()
        self.assertEqual(self.f3x_report.form_type, "F3XA")
        self.assertEqual(self.f3x_report.report_version, 1)
        self.assertEqual(self.f3x_report.upload_submission, new_upload_submission)

    def test_delete_ie_f24_to_f3x_link(self):
        f24_report = create_form24(self.committee, {"name": "test 24 delete"})
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
        ie.set_reports([f24_report_id, f3x_report_id])
        ie_id = ie.id

        f3x_report.refresh_from_db()
        f24_report.refresh_from_db()

        self.assertFalse(f3x_report.can_delete)
        self.assertTrue(f24_report.can_delete)

        f24_report.delete()
        ie = Transaction.all_objects.filter(id=ie_id).first()
        self.assertIsNone(ie.deleted)
        self.assertFalse(Report.objects.filter(id=f24_report_id).exists())
        self.assertFalse(Form24.objects.filter(id=f24_id).exists())

        f3x_report.refresh_from_db()
        self.assertTrue(f3x_report.can_delete)

        f3x_report.delete()
        self.assertFalse(Report.objects.filter(id=f3x_report_id).exists())
        self.assertFalse(Form3X.objects.filter(id=f3x_id).exists())

        ie = Transaction.all_objects.filter(id=ie_id).first()
        self.assertIsNotNone(ie.deleted)

    def test_delete_report_that_starts_debt_chain(self):
        self.f3x_report.delete()

        f3x_a = create_form3x(self.committee, "2024-01-01", "2024-01-31", {})
        f3x_b = create_form3x(self.committee, "2024-02-01", "2024-02-29", {})

        test_org = create_test_organization_contact(
            "Test Organization",
            self.committee.id
        )
        test_debt = create_debt(
            self.committee,
            test_org,
            4000,
            "SD9",
            "DEBT_OWED_BY_COMMITTEE",
            f3x_a
        )

        carry_forward_debts(f3x_b)

        test_debt.refresh_from_db()

        f3x_a.refresh_from_db()
        f3x_b.refresh_from_db()

        self.assertFalse(f3x_a.can_delete)
        self.assertTrue(f3x_b.can_delete)
        self.assertFalse(f3x_b.can_delete_previous)

        f3x_b.delete()

        f3x_a.refresh_from_db()
        self.assertTrue(f3x_a.can_delete)

    def test_delete_report_that_starts_loan_chain(self):
        self.f3x_report.delete()

        f3x_a = create_form3x(self.committee, "2024-01-01", "2024-01-31", {})
        f3x_b = create_form3x(self.committee, "2024-02-01", "2024-02-29", {})
        f3x_c = create_form3x(self.committee, "2024-03-01", "2024-03-21", {})

        test_org = create_test_organization_contact(
            "Test Organization",
            self.committee.id
        )
        test_loan = create_loan_from_bank(
            self.committee,
            test_org,
            20000,
            "TOMORROW",
            "MORE",
            False,
            None,
            f3x_a
        )[0]

        carry_forward_loans(f3x_b)
        carry_forward_loans(f3x_c)

        test_loan.refresh_from_db()

        f3x_a.refresh_from_db()
        f3x_b.refresh_from_db()
        f3x_c.refresh_from_db()

        self.assertFalse(f3x_a.can_delete)
        self.assertFalse(f3x_b.can_delete)
        self.assertTrue(f3x_c.can_delete)
        self.assertFalse(f3x_b.can_delete_previous)
        self.assertFalse(f3x_c.can_delete_previous)

        f3x_c.delete()

        f3x_a.refresh_from_db()
        f3x_b.refresh_from_db()

        self.assertFalse(f3x_a.can_delete)
        self.assertTrue(f3x_b.can_delete)
        self.assertFalse(f3x_b.can_delete_previous)

        f3x_b.delete()

        f3x_a.refresh_from_db()
        self.assertTrue(f3x_a.can_delete)
