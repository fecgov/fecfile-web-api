from django.core.management.base import BaseCommand
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.models import Report
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.contacts.models import Contact
from fecfiler.memo_text.models import MemoText
import datetime
import json


F3X_SCHEMA = json.load(open("fecfiler/web_services/dot_fec/schema_fields/F3X.json", "r"))
SCH_A_SCHEMA = json.load(open("fecfiler/web_services/dot_fec/schema_fields/SchA.json", "r"))
TEXT_SCHEMA = json.load(open("fecfiler/web_services/dot_fec/schema_fields/Text.json", "r"))
SEP_CHAR = ""


class Command(BaseCommand):
    help = (
        'Import a dot FEC file (WARNING PROTOTYPE: '
        'cannot handle grandchild transactions; '
        'only supports F3X reports and Individual Receipts; '
        ')'
    )

    # Defines arguments for the django management command
    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help="path to the target dot_fec file")

    # Runs the django management command
    def handle(self, *args, **options):
        # Open the file
        file = open(options.get("file"), "r")
        file.readline()  # Skip the HDR row

        # Parse the file line-by-line
        line = file.readline()
        old_row = []
        row = line.split(SEP_CHAR)
        previous_transaction = None

        while len(line) > 0:
            # Handle F3X reports
            if row[0] == "F3XN":
                report, form_3x = self.create_report(row)
                self.records["report"] = report
                self.records["form_3x"] = form_3x
                form_3x.save()
                report.form_3x = form_3x
                report.save()

            # Handle Schedule A Transactions (just Individual Receipts)
            elif row[0] == "SA11AI":
                # Creating a transaction also defines contacts as a by-product
                transaction, sch_a = self.create_transaction(row)
                transaction.schedule_a = sch_a

                transaction.contact_1.save()
                sch_a.save()
                transaction.schedule_a = sch_a
                transaction.save()
                transaction.reports.set([self.records["report"]])

                # Check to see if the new transaction has a parent
                child_transaction = False
                for trans in self.records["transactions"]:
                    if trans.transaction_id == row[3]:
                        child_transaction = True
                        trans.transaction_set.set([transaction])

                # Only add top-level transactions to the records
                # (the current implementation cannot handle grandchildren)
                if not child_transaction:
                    self.records["transactions"].append(transaction)
                previous_transaction = transaction

            # Handle Memo Text
            elif row[0] == "TEXT":
                memo_text = None
                if row[4] == "SA11AI" and old_row and old_row[0] == "SA11AI":
                    memo_text = self.create_memo_transaction(row, previous_transaction)
                if row[4] == "F3XN":
                    memo_text = self.create_memo_report(row)

                if memo_text is not None:
                    self.records["memos"].append(memo_text)

            line = file.readline()
            old_row = row
            row = line.split(SEP_CHAR)

        print(
            "Creating records:\n"
            "1 new report\n"
            f"{len(self.records['memos'])} new memo(s)\n"
            f"{len(self.records['contacts'])} new contacts(s)\n"
            f"{len(self.records['transactions'])} new top-level transaction(s)\n"
        )

        for memo_text in self.records["memos"]:
            memo_text.save()