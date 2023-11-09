from django.test import TestCase
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c.views import save_hook
from fecfiler.transactions.models import Transaction
from fecfiler.reports.models import Report


class ScheduleCViewsTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
    ]

    def setUp(self):
        pass

    def test_create_loan_in_future_report(self):
        report_1 = Report(
            form_type="F3XN",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
            coverage_from_date="2023-01-01",
            coverage_through_date="2023-01-02",
        )
        report_1.save()
        report_2 = Report(
            form_type="F3XN",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
            coverage_from_date="2023-02-01",
            coverage_through_date="2023-02-02",
        )
        report_2.save()
        loan = Transaction(
            transaction_type_identifier="LOAN_BY_COMMITTEE",
            transaction_id="F487B9EDAD9A32E6CFEE",
            report_id=report_1.id,
            form_type="SC/9",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
        )
        schedule_c = ScheduleC(
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
        schedule_c.save()
        loan.schedule_c = schedule_c
        loan.save()
        save_hook(loan, False)
        carried_over = Transaction.objects.filter(report_id=report_2.id)
        self.assertEqual(carried_over.count(), 1)

    def test_update_loan_in_future_report(self):
        report_1 = Report(
            form_type="F3XN",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
            coverage_from_date="2023-01-01",
            coverage_through_date="2023-01-02",
        )
        report_1.save()
        report_2 = Report(
            form_type="F3XN",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
            coverage_from_date="2023-02-01",
            coverage_through_date="2023-02-02",
        )
        report_2.save()
        loan = Transaction(
            transaction_type_identifier="LOAN_BY_COMMITTEE",
            transaction_id="F487B9EDAD9A32E6CFEE",
            report_id=report_1.id,
            form_type="SC/9",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
        )
        schedule_c = ScheduleC(
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
        schedule_c.save()
        loan.schedule_c = schedule_c
        loan.save()
        save_hook(loan, False)
        carried_over = Transaction.objects.filter(report_id=report_2.id)
        self.assertEqual(carried_over.count(), 1)

        loan.schedule_c.loan_amount = 4321
        save_hook(loan, True)
        carried_over = Transaction.objects.filter(report_id=report_2.id)
        self.assertEqual(carried_over.count(), 1)
        self.assertEqual(carried_over.first().schedule_c.loan_amount, 4321)
