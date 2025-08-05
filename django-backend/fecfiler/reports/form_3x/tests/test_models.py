from django.test import TestCase
from ..models import Form3X
from fecfiler.reports.models import ReportTransaction
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.models import CommitteeAccount


class F3XTestCase(TestCase):
    fixtures = ["C01234567_user_and_committee", "test_f3x_reports"]

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.q1_report = create_form3x(
            self.committee,
            "2024-01-01",
            "2024-02-01",
            {"election_code": "test_string_value"},
        )
        self.valid_f3x_summary = Form3X(
            change_of_address=False,
            election_code="P2020",
            date_of_election="2020-12-31",
            state_of_election="AK",
            qualified_committee=True,
        )

    def test_get_f3x_summary(self):
        self.assertEqual(self.q1_report.form_3x.election_code, "test_string_value")

    def test_save_and_delete(self):
        self.valid_f3x_summary.save()
        f3x_summary_from_db = Form3X.objects.get(election_code="P2020")
        self.assertIsInstance(f3x_summary_from_db, Form3X)
        f3x_summary_from_db.delete()
        self.assertRaises(
            Form3X.DoesNotExist,
            Form3X.objects.get,
            election_code="P2020",
        )

    def test_pull_report_forward(self):
        committee_account = CommitteeAccount.objects.get(
            id="11111111-2222-3333-4444-555555555555"
        )
        new_report = create_form3x(committee_account, "2007-04-01", "2007-06-30")

        new_report.save()
        new_loan = (
            ReportTransaction.objects.filter(
                report=new_report,
                transaction__transaction_type_identifier="LOAN_RECEIVED_FROM_INDIVIDUAL",
            )
            .first()
            .transaction
        )

        new_guarantor = (
            ReportTransaction.objects.filter(
                report=new_report,
                transaction__transaction_type_identifier="C2_LOAN_GUARANTOR",
            )
            .first()
            .transaction
        )

        self.assertNotEqual(new_loan.id, "474a1a10-da68-4d71-9a11-9509df48e1aa")
        self.assertEqual(new_loan.transaction_id, "9147A12D265AADCAB2D0")
        self.assertNotEqual(new_guarantor.id, "90e268b5-ee0a-40e9-bc0b-459c097d46d7")
        self.assertEqual(new_guarantor.transaction_id, "EF3D872B9863DBEC1376")
        self.assertEqual(new_guarantor.schedule_c2.guaranteed_amount, 111.00)

        new_debt_count = ReportTransaction.objects.filter(
            report=new_report,
            transaction__schedule_d_id__isnull=False,
        ).count()
        self.assertEqual(new_debt_count, 1)

        new_debt = (
            ReportTransaction.objects.filter(
                report=new_report,
                transaction__transaction_type_identifier="DEBT_OWED_TO_COMMITTEE",
            )
            .first()
            .transaction
        )

        self.assertNotEqual(new_debt.id, "474a1a10-da68-4d71-9a11-9509df4ddddd")
        self.assertEqual(new_debt.transaction_id, "C9718E935534853B488D")
        self.assertEqual(new_debt.schedule_d.incurred_amount, 0)
