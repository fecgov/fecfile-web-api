from django.core.management.base import BaseCommand
from fecfiler.reports.models import Report
from fecfiler.reports.views import delete_all_reports
from fecfiler.transactions.models import Transaction
from fecfiler.memo_text.models import MemoText
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.web_services.models import DotFEC, UploadSubmission, WebPrintSubmission
import re


class Command(BaseCommand):
    help = "Delete all reports (and transactions) for a given committee"

    def add_arguments(self, parser):
        parser.add_argument("committee_id", nargs=1, type=str)

    def handle(self, *args, **options):
        committee_ids = options.get('committee_id', None)
        if committee_ids is None or len(committee_ids) == 0:
            self.stderr.write("Error: no committee id provided")
            return
        committee_id = committee_ids[0]

        cid_regex = re.compile("^C[0-9]{8}$")
        if not cid_regex.match(str(committee_id)):
            self.stderr.write(f'Error: invalid committee id "{committee_id}"')
            return

        committee = CommitteeAccount.objects.filter(committee_id=committee_id).first()
        if committee is None:
            self.stderr.write("Error: no matching committee")
            return

        self.delete_committee_reports(committee_id)

    def delete_committee_reports(self, committee_id):
        reports = Report.objects.filter(committee_account__committee_id=committee_id)
        report_count = reports.count()
        transactions = Transaction.objects.filter(
            committee_account__committee_id=committee_id
        )
        transaction_count = transactions.count()
        memo_count = MemoText.objects.filter(
            report__committee_account__committee_id=committee_id
        ).count()
        dot_fec_count = DotFEC.objects.filter(
            report__committee_account__committee_id=committee_id
        ).count()
        upload_submission_count = UploadSubmission.objects.filter(
            dot_fec__report__committee_account__committee_id=committee_id
        ).count()
        web_print_submission_count = WebPrintSubmission.objects.filter(
            dot_fec__report__committee_account__committee_id=committee_id
        ).count()

        self.stdout.write(self.style.SUCCESS(f"Deleting Reports: {report_count}"))
        self.stdout.write(self.style.SUCCESS(
            f"Deleting Transactions: {transaction_count}"
        ))
        self.stdout.write(self.style.SUCCESS(f"Memos: {memo_count}"))
        self.stdout.write(self.style.SUCCESS(f"Dot Fecs: {dot_fec_count}"))
        self.stdout.write(self.style.SUCCESS(
            f"Upload Submissions: {upload_submission_count}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"WebPrint Submissions: {web_print_submission_count}"
        ))

        delete_all_reports(committee_id)