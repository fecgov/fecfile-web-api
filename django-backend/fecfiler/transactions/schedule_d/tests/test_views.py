from django.test import TestCase
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_d.views import save_hook
from fecfiler.transactions.models import Transaction
from fecfiler.reports.models import Report


class ScheduleDViewsTestCase(TestCase):
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
        self.debt = Transaction(
            transaction_type_identifier="DEBT_OWED_BY_COMMITTEE",
            transaction_id="F487B9EDAD9A32E6CFEE",
            report_id=self.report_1.id,
            form_type="SD10",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
        )
        self.schedule_d = ScheduleD(
            creditor_organization_name="name",
            creditor_street_1="street",
            creditor_city="ville",
            creditor_state="MD",
            creditor_zip="111111",
            incurred_amount=1234,
        )
        self.schedule_d.save()
        self.debt.schedule_d = self.schedule_d
        self.debt.save()

    def test_create_guarantor_in_future_report(self):
        save_hook(self.debt, False)
        carried_over = Transaction.objects.filter(
            report_id=self.report_2.id, schedule_d__isnull=False
        )
        self.assertEqual(carried_over.count(), 1)
        self.assertEqual(carried_over.first().schedule_d.incurred_amount, 0)

    def test_update_guarantor_in_future_report(self):
        save_hook(self.debt, False)
        carried_over = Transaction.objects.filter(
            report_id=self.report_2.id, schedule_d__isnull=False
        )
        self.assertEqual(carried_over.count(), 1)

        self.debt.schedule_d.incurred_amount = 5
        save_hook(self.debt, True)
        carried_over = Transaction.objects.filter(
            report_id=self.report_2.id, schedule_d__isnull=False
        )
        self.assertEqual(carried_over.count(), 1)
        # incurred amounts are independent across reports so they would not be updated
        # by previous ones.  same reason we set it to 0 when whe carry a debt over
        self.assertEqual(carried_over.first().schedule_d.incurred_amount, 1234)
