from django.test import TestCase
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_d.views import save_hook
from fecfiler.transactions.models import Transaction
from fecfiler.reports.models import Report
from fecfiler.committee_accounts.views import create_committee_view


class ScheduleDViewsTestCase(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
    ]

    def setUp(self):
        create_committee_view("11111111-2222-3333-4444-555555555555")
        self.form3x = Form3X()
        self.form3x.save()
        self.report_1 = Report(
            form_type="F3XN",
            committee_account_id="11111111-2222-3333-4444-555555555555",
            coverage_from_date="2023-01-01",
            coverage_through_date="2023-01-02",
            form_3x=self.form3x,
        )
        self.report_1.save()
        self.report_2 = Report(
            form_type="F3XN",
            committee_account_id="11111111-2222-3333-4444-555555555555",
            coverage_from_date="2023-02-01",
            coverage_through_date="2023-02-02",
            form_3x=self.form3x,
        )
        self.report_2.save()
        self.debt = Transaction(
            transaction_type_identifier="DEBT_OWED_BY_COMMITTEE",
            transaction_id="F487B9EDAD9A32E6CFEE",
            form_type="SD10",
            committee_account_id="11111111-2222-3333-4444-555555555555",
        )
        self.schedule_d = ScheduleD(
            incurred_amount=1234,
        )
        self.schedule_d.save()
        self.debt.schedule_d = self.schedule_d
        self.debt.save()
        self.debt.reports.add(self.report_1)

    def test_create_guarantor_in_future_report(self):
        save_hook(self.debt, False)
        carried_over = Transaction.objects.filter(
            reports__id=self.report_2.id, schedule_d__isnull=False
        )
        self.assertEqual(carried_over.count(), 1)
        self.assertEqual(carried_over.first().schedule_d.incurred_amount, 0)

    def test_update_guarantor_in_future_report(self):
        save_hook(self.debt, False)
        carried_over = Transaction.objects.filter(
            reports__id=self.report_2.id, schedule_d__isnull=False
        )
        self.assertEqual(carried_over.count(), 1)

        self.debt.schedule_d.incurred_amount = 5
        save_hook(self.debt, True)
        carried_over = Transaction.objects.filter(
            reports__id=self.report_2.id, schedule_d__isnull=False
        )
        self.assertEqual(carried_over.count(), 1)
        # incurred amounts are independent across reports so they would not be updated
        # by previous ones.  same reason we set it to 0 when whe carry a debt over
        self.assertEqual(carried_over.first().schedule_d.incurred_amount, 1234)
