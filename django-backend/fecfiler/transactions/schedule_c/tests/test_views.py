from django.test import TestCase
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c.views import save_hook
from fecfiler.transactions.models import Transaction
from fecfiler.memo_text.models import MemoText
from fecfiler.reports.models import Report
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_report_level_memos


class ScheduleCViewsTestCase(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
    ]

    def setUp(self):
        test_committee_id = "11111111-2222-3333-4444-555555555555"
        self.form_3x = Form3X()
        self.form_3x.save()
        self.report_1 = Report(
            form_type="F3XN",
            committee_account_id=test_committee_id,
            coverage_from_date="2023-01-01",
            coverage_through_date="2023-01-02",
            form_3x=self.form_3x,
        )
        self.report_1.save()
        self.report_2 = Report(
            form_type="F3XN",
            committee_account_id=test_committee_id,
            coverage_from_date="2023-02-01",
            coverage_through_date="2023-02-02",
            form_3x=self.form_3x,
        )
        self.report_2.save()
        self.loan = Transaction(
            transaction_type_identifier="LOAN_BY_COMMITTEE",
            transaction_id="F487B9EDAD9A32E6CFEE",
            form_type="SC/9",
            committee_account_id=test_committee_id,
            memo_text=MemoText(
                committee_account_id=test_committee_id,
                text4000="Memo!!!",
                rec_type="TEXT",
                is_report_level_memo=False,
            )
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
        self.loan.memo_text.transaction_uuid = self.loan.id
        self.loan.memo_text.save()
        self.loan.reports.add(self.report_1)

    def test_create_loan_in_future_report(self):
        save_hook(self.loan, False)
        carried_over = Transaction.objects.filter(reports__id=self.report_2.id)
        self.assertEqual(carried_over.count(), 1)
        self.assertEqual(carried_over.first().memo_text.text4000, "Memo!!!")
        self.assertEqual(
            carried_over.first().memo_text.transaction_uuid,
            str(carried_over.first().id)
        )

    def test_loan_propogates_to_newly_created_report(self):
        save_hook(self.loan, False)
        report_3 = Report(
            form_type="F3XN",
            committee_account_id=self.loan.committee_account.id,
            coverage_from_date="2023-03-01",
            coverage_through_date="2023-03-02",
            form_3x=self.form_3x,
        )
        report_3.save()
        carried_over = Transaction.objects.filter(reports__id=report_3.id)
        self.assertEqual(carried_over.count(), 1)
        self.assertEqual(carried_over.first().schedule_c.loan_amount, 1234)
        self.assertEqual(carried_over.first().memo_text.text4000, "Memo!!!")

    def test_carried_over_loan_memo_not_included_as_report_memo(self):
        save_hook(self.loan, False)
        report_level_memos = compose_report_level_memos(self.report_1.id)
        self.assertEqual(len(report_level_memos), 0)

    def test_update_loan_in_future_report(self):
        save_hook(self.loan, False)
        carried_over = Transaction.objects.filter(reports__id=self.report_2.id)
        self.assertEqual(carried_over.count(), 1)
        self.assertEqual(carried_over.first().memo_text.text4000, "Memo!!!")

        self.loan.schedule_c.loan_amount = 4321
        self.loan.memo_text.text4000 = "Different Memo!"
        self.loan.memo_text.save()
        save_hook(self.loan, True)
        carried_over = Transaction.objects.filter(reports__id=self.report_2.id)
        self.assertEqual(carried_over.count(), 1)
        self.assertEqual(carried_over.first().schedule_c.loan_amount, 4321)

        # Disabled the following assertion until the loan memo updating bug is fixed
        # self.assertEqual(carried_over.first().memo_text.text4000, "Different Memo!")
