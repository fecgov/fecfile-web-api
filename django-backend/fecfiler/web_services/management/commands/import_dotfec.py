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

    # "records" is used both to help with building associations
    # and later to save everything once it's all been built
    records = {
        "report": None,
        "form_3x": None,
        "memos": [],
        "contacts": [],
        "transactions": []
    }

    # Converts a value to a necessary form-factor based on the
    # rules defined in the mapping for that specific column
    def encode(self, value, column_map):
        if value == "":
            return None

        if "serializer" in column_map:
            serializer = column_map["serializer"]
            if serializer == "DATE":
                year = int(value[0:4])
                month = int(value[4:6])
                day = int(value[6:8])
                return datetime.date(year, month, day)
            if serializer == "BOOLEAN_X":
                if value == "X":
                    return True
                return False
        return value

    # Creates valid Report and Form3X objects from a row
    # returns as a tuple: report, form_3x
    def create_report(self, row):
        keys_to_skip = [
            "filer_committee_id_number"
		]
        committee_account = CommitteeAccount.objects.get(id="c94c5d1a-9e73-464d-ad72-b73b5d8667a9")
        F3X_cols = F3X_SCHEMA.keys()

        report_obj = {
            "committee_account": committee_account
        }
        f3x_obj = {}
        for c in range(len(F3X_cols)):
            column_key = list(F3X_cols)[c]
            column_map = F3X_SCHEMA[column_key]
            val = row[c]

            if column_key in keys_to_skip:
                continue

            encoded_value = self.encode(val, column_map)
            if encoded_value is not None:
                if "path" not in column_map:
                    report_obj[column_key] = encoded_value
                else:
                    path = column_map["path"].split("form_3x.")[1]
                    f3x_obj[path] = encoded_value

        form_3x = Form3X(**f3x_obj)
        report = Report(**report_obj)
        return report, form_3x

    # Creates valid Transaction and ScheduleA objects from a row
    # returns as a tuple: transaction, schedule_a
    def create_transaction(self, row):
        keys_to_skip = [
            "filer_committee_id_number"
		]
        committee_account = CommitteeAccount.objects.get(id="c94c5d1a-9e73-464d-ad72-b73b5d8667a9")
        sch_a_cols = SCH_A_SCHEMA.keys()

        transaction_obj = {
            "committee_account": committee_account,
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT"
        }
        sch_a_obj = {}
        contact_fields = {}

        for c in range(len(sch_a_cols)):
            column_key = list(sch_a_cols)[c]
            column_map = SCH_A_SCHEMA[column_key]
            val = row[c]

            if column_key in keys_to_skip:
                continue

            if column_key.split("_")[0] == "contributor":
                contact_key = "_".join(column_key.split("_")[1:])
                if contact_key in ["organization_name", "committee_name"]:
                    contact_key = "name"
                contact_fields[contact_key] = self.encode(val, column_map)
                continue

            encoded_value = self.encode(val, column_map)
            if encoded_value is not None:
                if "path" not in column_map:
                    transaction_obj[column_key] = encoded_value
                else:
                    pathing = column_map["path"].split(".")
                    path = pathing[-1]
                    if len(pathing) > 1:
                        sch_a_obj[path] = encoded_value
                    else:
                        transaction_obj[path] = encoded_value

        schedule_a = ScheduleA(**sch_a_obj)
        transaction = Transaction(**transaction_obj)
        transaction.contact_1 = self.create_contact(contact_fields)
        return transaction, schedule_a

    # Creates a valid Contact object from a row OR matches with an earlier contact
    def create_contact(self, fields):
        for contact in self.records["contacts"]:
            if (
                fields.get("street_1") == contact.street_1
                and fields.get("street_2") == contact.street_2
                and fields.get("city") == contact.city
                and fields.get("state") == contact.state
                and fields.get("zip") == contact.zip
                and fields.get("name") == contact.name
                and fields.get("first_name") == contact.first_name
                and fields.get("last_name") == contact.last_name
                and fields.get("middle_name") == contact.middle_name
                and fields.get("prefix") == contact.prefix
                and fields.get("suffix") == contact.suffix
            ):
                return contact

        new_contact = Contact(**fields)
        self.records["contacts"].append(new_contact)
        return new_contact

    # Creates a valid MemoText object from a row, associating it to a transaction
    def create_memo_transaction(self, row, transaction):
        memo_text = self.create_memo_text(row)
        transaction.memo_text = memo_text
        return memo_text

    # Creates a valid MemoText object from a row, associating it to the file's report
    def create_memo_report(self, row):
        memo_text = self.create_memo_text(row)
        memo_text.report = self.records["report"]
        return memo_text

    # helper function for creating a valid MemoText
    def create_memo_text(self, row):
        keys_to_skip = [
            "filer_committee_id_number",
            "back_reference_tran_id_number",
            "back_reference_sched_form_name"
        ]
        committee_account = CommitteeAccount.objects.get(id="c94c5d1a-9e73-464d-ad72-b73b5d8667a9")
        memo_cols = TEXT_SCHEMA.keys()

        memo_obj = {
            "committee_account": committee_account
        }
        for c in range(len(memo_cols)):
            column_key = list(memo_cols)[c]
            column_map = TEXT_SCHEMA[column_key]
            val = row[c]

            if column_key in keys_to_skip:
                continue

            encoded_value = self.encode(val, column_map)
            if encoded_value is not None:
                memo_obj[column_key] = encoded_value

        return MemoText(**memo_obj)

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

            # Handle Schedule A Transactions (just Individual Receipts)
            elif row[0] == "SA11AI":
                # Creating a transaction also defines contacts as a by-product
                transaction, sch_a = self.create_transaction(row)
                transaction.schedule_a = sch_a

                # Check to see if the new transaction has a parent
                child_transaction = False
                for trans in self.records["transactions"]:
                    if trans.transaction_id == row[3]:
                        child_transaction = True
                        trans.children.append(transaction)

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
            f"{len(self.records['memos'])} report-level memo(s)\n"
            f"{len(self.records['contacts'])} new contacts(s)\n"
            f"{len(self.records['transactions'])} new top-level transaction(s)\n"
        )

        self.records["form_3x"].save()
        self.records["report"].form_3x = self.records["form_3x"]
        self.records["report"].save()

        for memo_text in self.records["memos"]:
            memo_text.save()

        for transaction in self.records["transactions"]:
            transaction.contact_1.save()
            transaction.schedule_a.save()
            transaction.save()
            transaction.reports.set([self.records["report"]])