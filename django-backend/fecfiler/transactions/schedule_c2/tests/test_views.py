from django.test import TestCase
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c.views import save_hook as c_hook
from fecfiler.transactions.schedule_c2.views import save_hook as c2_hook
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.models import Transaction
from fecfiler.reports.models import Report


class ScheduleC2ViewsTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
    ]

    def setUp(self):
        self.report_1 = Report(
            form_type="F3XN",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
            coverage_from_date="2023-01-01",
            coverage_through_date="2023-01-02",
        )
        self.report_1.save()
        self.report_2 = Report(
            form_type="F3XN",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
            coverage_from_date="2023-02-01",
            coverage_through_date="2023-02-02",
        )
        self.report_2.save()
        self.loan = Transaction(
            transaction_type_identifier="LOAN_BY_COMMITTEE",
            transaction_id="F487B9EDAD9A32E6CFEE",
            report_id=self.report_1.id,
            form_type="SC/9",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
        )
        self.schedule_c = ScheduleC(
            lender_organization_name="name",
            lender_street_1="street",
            lender_city="ville",
            lender_state="MD",
            lender_zip="111111",
            loan_amount=1234,
            loan_incurred_date="2023-01-01",
            loan_due_date="123",
            loan_interest_rate="123",
            secured=True,
            personal_funds=False,
            lender_committee_id_number="C12345678",
        )
        self.schedule_c.save()
        self.loan.schedule_c = self.schedule_c
        self.loan.save()
        c_hook(self.loan, False)

        self.guarantor = Transaction(
            parent_transaction_id=self.loan.id,
            transaction_type_identifier="C2_LOAN_GUARANTOR",
            transaction_id="12345678123456781234",
            report_id=self.report_1.id,
            form_type="SC2/9",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
        )
        self.schedule_c2 = ScheduleC2(guarantor_last_name="smith", guaranteed_amount=10)
        self.schedule_c2.save()
        self.guarantor.schedule_c2 = self.schedule_c2
        self.guarantor.save()

    def test_create_guarantor_in_future_report(self):
        c2_hook(self.guarantor, False)
        carried_over = Transaction.objects.filter(
            report_id=self.report_2.id, schedule_c2__isnull=False
        )
        self.assertEqual(carried_over.count(), 1)

    def test_update_guarantor_in_future_report(self):
        c2_hook(self.guarantor, False)
        carried_over = Transaction.objects.filter(
            report_id=self.report_2.id, schedule_c2__isnull=False
        )
        self.assertEqual(carried_over.count(), 1)

        self.guarantor.schedule_c2.guaranteed_amount = 5
        c2_hook(self.guarantor, True)
        carried_over = Transaction.objects.filter(
            report_id=self.report_2.id, schedule_c2__isnull=False
        )
        self.assertEqual(carried_over.count(), 1)
        self.assertEqual(carried_over.first().schedule_c2.guaranteed_amount, 5)
