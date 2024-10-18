from django.test import TestCase
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c.views import save_hook
from fecfiler.transactions.models import Transaction
from fecfiler.reports.models import Report
from fecfiler.committee_accounts.utils import create_committee_view


class ScheduleCViewsTestCase(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
    ]

    def setUp(self):
        create_committee_view("11111111-2222-3333-4444-555555555555")
        self.form_3x = Form3X()
        self.form_3x.save()
        self.report_1 = Report(
            form_type="F3XN",
            committee_account_id="11111111-2222-3333-4444-555555555555",
            coverage_from_date="2023-01-01",
            coverage_through_date="2023-01-02",
            form_3x=self.form_3x,
        )
        self.report_1.save()
        self.report_2 = Report(
            form_type="F3XN",
            committee_account_id="11111111-2222-3333-4444-555555555555",
            coverage_from_date="2023-02-01",
            coverage_through_date="2023-02-02",
            form_3x=self.form_3x,
        )
        self.report_2.save()
        self.loan = Transaction(
            transaction_type_identifier="LOAN_BY_COMMITTEE",
            transaction_id="F487B9EDAD9A32E6CFEE",
            form_type="SC/9",
            committee_account_id="11111111-2222-3333-4444-555555555555",
        )
        self.schedule_c = ScheduleC(
            loan_amount=1234,
            loan_incurred_date="2023-01-01",
            loan_due_date="123",
            loan_interest_rate="123",
            secured=True,
            personal_funds=False,
        )
        self.schedule_c.save()
        self.loan.schedule_c = self.schedule_c
        self.loan.save()
        self.loan.reports.add(self.report_1)

    def test_create_loan_in_future_report(self):
        save_hook(self.loan, False)
        carried_over = Transaction.objects.filter(reports__id=self.report_2.id)
        self.assertEqual(carried_over.count(), 1)

    def test_update_loan_in_future_report(self):
        save_hook(self.loan, False)
        carried_over = Transaction.objects.filter(reports__id=self.report_2.id)
        self.assertEqual(carried_over.count(), 1)

        self.loan.schedule_c.loan_amount = 4321
        save_hook(self.loan, True)
        carried_over = Transaction.objects.filter(reports__id=self.report_2.id)
        self.assertEqual(carried_over.count(), 1)
        self.assertEqual(carried_over.first().schedule_c.loan_amount, 4321)
