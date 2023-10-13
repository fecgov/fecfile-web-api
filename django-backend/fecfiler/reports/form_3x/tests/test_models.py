from django.test import TestCase
from ..models import Form3X
import datetime
from decimal import Decimal


class F3XTestCase(TestCase):
    fixtures = ["test_committee_accounts", "test_f3x_reports"]

    def setUp(self):
        self.valid_f3x_summary = Form3X(
            form_type="F3XN",
            treasurer_last_name="Validlastname",
            treasurer_first_name="Validfirstname",
            date_signed="2022-01-01",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
            coverage_through_date="2023-07-31",
        )

    def test_get_f3x_summary(self):
        f3x_summary = Form3X.objects.get(L6a_year_for_above_ytd="2005")
        self.assertEquals(f3x_summary.form_type, "F3XN")

    def test_save_and_delete(self):
        self.valid_f3x_summary.save()
        f3x_summary_from_db = Form3X.objects.get(date_signed="2022-01-01")
        self.assertIsInstance(f3x_summary_from_db, Form3X)
        self.assertEquals(f3x_summary_from_db.date_signed, datetime.date(2022, 1, 1))
        f3x_summary_from_db.delete()
        self.assertRaises(
            Form3X.DoesNotExist,
            Form3X.objects.get,
            date_signed="2022-01-01",
        )

        soft_deleted_f3x_summary = Form3X.all_objects.get(date_signed="2022-01-01")
        self.assertEquals(
            soft_deleted_f3x_summary.date_signed, datetime.date(2022, 1, 1)
        )
        self.assertIsNotNone(soft_deleted_f3x_summary.deleted)
        soft_deleted_f3x_summary.hard_delete()
        self.assertRaises(
            Form3X.DoesNotExist,
            Form3X.all_objects.get,
            date_signed="2022-01-01",
        )

    def test_pull_report_forward(self):
        self.assertEquals(True, True)

        new_report = Form3X(
            form_type="F3XN",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
            coverage_through_date="2007-03-31",
        )

        new_report.save()
        new_loan = new_report.transaction_set.filter(
            transaction_type_identifier="LOAN_RECEIVED_FROM_INDIVIDUAL"
        ).first()
        new_guarantor = new_report.transaction_set.filter(
            transaction_type_identifier="C2_LOAN_GUARANTOR"
        ).first()

        self.assertNotEquals(new_loan.id, "474a1a10-da68-4d71-9a11-9509df48e1aa")
        self.assertEquals(new_loan.transaction_id, "9147A12D265AADCAB2D0")
        self.assertNotEquals(new_guarantor.id, "90e268b5-ee0a-40e9-bc0b-459c097d46d7")
        self.assertEquals(new_guarantor.transaction_id, "EF3D872B9863DBEC1376")
        self.assertEquals(new_guarantor.schedule_c2.guarantor_state, "CA")

        new_debt_count = new_report.transaction_set.filter(
            schedule_d_id__isnull=False,
        ).count()
        self.assertEquals(new_debt_count, 1)

        new_debt = new_report.transaction_set.filter(
            transaction_type_identifier="DEBT_OWED_TO_COMMITTEE"
        ).first()

        self.assertNotEquals(new_debt.id, "474a1a10-da68-4d71-9a11-9509df4ddddd")
        self.assertEquals(new_debt.transaction_id, "C9718E935534853B488D")
        self.assertEquals(new_debt.schedule_d.incurred_amount, Decimal(0))
