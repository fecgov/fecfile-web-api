from django.core.management.base import BaseCommand, CommandError
from fecfiler.settings import (
    BASE_DIR,
    AWS_STORAGE_BUCKET_NAME,
)
from fecfiler.s3 import S3_SESSION
from django.core import serializers

from fecfiler.committee_accounts.models import CommitteeAccount

# Reports
from fecfiler.reports.models import Report, ReportTransaction
from fecfiler.reports.form_1m.models import Form1M
from fecfiler.reports.form_24.models import Form24
from fecfiler.reports.form_3.models import Form3
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.reports.form_99.models import Form99
FORM_MODELS = [Form1M, Form24, Form3, Form3X, Form99]

# Contacts
from fecfiler.contacts.models import Contact

# Transactions
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_e.models import ScheduleE
from fecfiler.transactions.schedule_f.models import ScheduleF
SCHEDULE_MODELS = [ScheduleA, ScheduleB, ScheduleC, ScheduleC1, ScheduleC2, ScheduleD, ScheduleE, ScheduleF]

# Memos
from fecfiler.memo_text.models import MemoText

# Cash On Hand
from fecfiler.cash_on_hand.models import CashOnHandYearly

# Submissions
from fecfiler.web_services.models import DotFEC, UploadSubmission, WebPrintSubmission
SUBMISSION_MODELS = [UploadSubmission, WebPrintSubmission]


class Command(BaseCommand):
    help = "Dump all data for a given committee into redis"

    def add_arguments(self, parser):
        parser.add_argument("--s3", action="store_true")
        parser.add_argument("committee_id")

    def serialize(self, queryset):
        return serializers.serialize("json", queryset)[1:-1] # Strip square brackets

    def dump_committee(self, committee):
            return self.serialize(CommitteeAccount.objects.filter(id=committee.id))

    def dump_contacts(self, committee):
        dumped_contacts = self.serialize(
            Contact.objects.filter(committee_account=committee)
        )
        if len(dumped_contacts) > 0:
            return [dumped_contacts]
        return []

    def dump_reports(self, committee):
        dumped_data = []
        for FormModel in FORM_MODELS:
            dumped_form = self.serialize(
                FormModel.objects.filter(report__committee_account=committee)
            )
            if len(dumped_form) > 0:
                dumped_data.append(dumped_form)

        dumped_reports = self.serialize(Report.objects.filter(committee_account=committee))
        if len(dumped_reports) > 0:
            dumped_data.append(dumped_reports)

        return dumped_data

    def dump_transactions(self, committee):
        dumped_data = []
        for ScheduleModel in SCHEDULE_MODELS:
            dumped_schedule = self.serialize(
                ScheduleModel.objects.filter(transaction__committee_account=committee)
            )
            if len(dumped_schedule) > 0:
                dumped_data.append(dumped_schedule)

        dumped_transactions = self.serialize(
            Transaction.objects.filter(
                committee_account=committee
            ).order_by("created")  # Ensure that parents are loaded before children
        )
        if len(dumped_transactions) > 0:
            dumped_data.append(dumped_transactions)

        dumped_report_transactions = self.serialize(
            ReportTransaction.objects.filter(
                transaction__committee_account=committee
            )
        )
        if len(dumped_report_transactions) > 0:
            dumped_data.append(dumped_report_transactions)

        return dumped_data

    def dump_memos(self, committee):
        dumped_memos = self.serialize(
            MemoText.objects.filter(committee_account=committee)
        )
        if len(dumped_memos) > 0:
            return [dumped_memos]
        return []

    def dump_cash_on_hand(self, committee):
        dumped_cash_on_hand = self.serialize(
            CashOnHandYearly.objects.filter(committee_account=committee)
        )
        if len(dumped_cash_on_hand) > 0:
            return [dumped_cash_on_hand]
        return []

    def dump_submissions(self, committee):
        dumped_data = []
        dumped_dot_fec = self.serialize(
            DotFEC.objects.filter(
                report__committee_account=committee
            )
        )
        if len(dumped_dot_fec) > 0:
            dumped_data.append(dumped_dot_fec)

        for SubmissionModel in SUBMISSION_MODELS:
            dumped_submission = self.serialize(
                SubmissionModel.objects.filter(
                    dot_fec__report__committee_account=committee
                )
            )
            if len(dumped_submission) > 0:
                dumped_data.append(dumped_submission)

        return dumped_data

    def dump_all_committee_data(self, committee):
        dumplist = [
            self.dump_committee(committee),
            *self.dump_contacts(committee),
            *self.dump_reports(committee),
            *self.dump_transactions(committee),
            *self.dump_memos(committee),
            *self.dump_cash_on_hand(committee),
            *self.dump_submissions(committee)
        ]

        return dumplist

    def handle(self, *args, **options):
        committee_id = options.get("committee_id")
        if committee_id is None:
            raise CommandError("Committee ID is a required parameter")
 
        committee = CommitteeAccount.objects.filter(committee_id=committee_id).first()
        if committee is None:
            raise CommandError("No Committee Account found matching that Committee ID")

        dumplist = self.dump_all_committee_data(committee)

        final_json = f"[{','.join(dumplist)}]"

        file = open("test_fixture.json", "w")
        file.write(final_json)
        file.close()
