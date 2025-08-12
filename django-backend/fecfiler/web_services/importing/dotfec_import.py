from fecfiler.imports.models import Imports, ImportStatus
from fecfiler.reports.models import Report
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.contacts.models import Contact
from fecfiler.memo_text.models import MemoText
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from django.db import transaction
import json

class DotFEC_Importer():
    import_obj: Imports | None = None
    records: dict = {}
    report: Report | None = None
    contacts = {}
    transactions = []

    def __init__(self, import_obj: Imports):
        self.import_obj = import_obj
        self.import_obj.status = ImportStatus.IMPORTING.value
        self.records = json.loads(import_obj.preprocessed_json)
        with transaction.atomic():
            self.import_records()

    def import_records(self):
        print("Keys:", self.records.keys())
        print("Contacts", len(self.records["contacts"]))
        print("Memos", len(self.records["memos"]))
        print("Transactions", len(self.records["transactions"]))
        print("SubTransactons", len(self.records["transactions"][0]["children"]))
        print("SubSubTransactons", len(self.records["transactions"][0]["children"][0]["children"]))
        print(self.records["form_3x"])

        try:
            self.import_report()
            for contact in self.records["contacts"].values():
                self.import_contact(contact)

            for transaction in self.records["transactions"]:
                self.import_transaction(transaction)

            for memo_obj in self.records["memos"]:
                self.import_memo(memo_obj)
        except Exception:
            self.import_obj.status = ImportStatus.FAILED_CREATION.value
            self.import_obj.save()

        self.import_obj.status = ImportStatus.SUCCESS.value
        self.import_obj.report = self.report.id
        self.import_obj.save()

    def import_report(self):
        f3x = Form3X(**self.records["form_3x"])
        f3x.save()
        report = Report(**self.records["report"])
        report.form_3x = f3x
        report.save()
        self.report = report

    def import_contact(self, contact_obj):
        temp_uuid = contact_obj.pop("temp_uuid")
        new_contact = Contact(**contact_obj)
        new_contact.save()
        self.contacts[temp_uuid] = new_contact

    def import_memo(self, memo_obj):
        if "report" in memo_obj:
            memo_obj.pop("report")
            memo_obj["report_id"] = self.report.id

        memo = MemoText(**memo_obj)
        memo.save()

        if "transaction_id_number" in memo_obj:
            for transaction in self.transactions:
                print(transaction.transaction_id, memo_obj["transaction_id_number"])
                if transaction.transaction_id == memo_obj["transaction_id_number"]:
                    print("MEMO <-> TRANSACTION LINK ESTABLISHED")
                    transaction.memo_text = memo
                    transaction.save()
                    break

    def import_transaction(self, transaction_obj):
        schedule_a_obj = transaction_obj.pop("schedule_a")
        new_schedule_a = ScheduleA(**schedule_a_obj)
        new_schedule_a.save()
        children = transaction_obj.pop("children")

        if "memo_text" in transaction_obj:
            transaction_obj.pop("memo_text")

        contact_obj = transaction_obj.pop("contact_1")
        temp_uuid = contact_obj["temp_uuid"]
        transaction_obj["contact_1_id"] = self.contacts[temp_uuid].id

        transaction_obj["schedule_a"] = new_schedule_a

        try:
            new_transaction = Transaction(**transaction_obj)
        except Exception as e:
            print(e)

        new_transaction.save()
        new_transaction.reports.set([self.report])
        self.transactions.append(new_transaction)
        for child in children:
            child = self.import_transaction(child)
            new_transaction.transaction_set.add(child)

        return new_transaction