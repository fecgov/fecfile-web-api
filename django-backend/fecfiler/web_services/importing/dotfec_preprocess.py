import json
from fecfiler.imports.models import Imports, ImportStatus
import datetime
import uuid

F3X_SCHEMA = json.load(open("fecfiler/web_services/dot_fec/schema_fields/F3X.json", "r"))
SCH_A_SCHEMA = json.load(open("fecfiler/web_services/dot_fec/schema_fields/SchA.json", "r"))
TEXT_SCHEMA = json.load(open("fecfiler/web_services/dot_fec/schema_fields/Text.json", "r"))
SEP_CHAR = ""

class DotFEC_Preprocessor():
    # "records" is used both to help with building associations
    # and later to save everything once it's all been built
    import_obj: Imports | None = None
    records = {
        "report": None,
        "form_3x": None,
        "memos": [],
        "contacts": {},
        "transactions": []
    }

    def __init__(self, import_obj: Imports):
        import_obj.status = ImportStatus.PREPROCESSING.value
        import_obj.save()
        self.import_obj = import_obj

        try:
            self.preprocess()
        except Exception:
            self.import_obj.status = ImportStatus.FAILED_PREPROCESS.value
            self.import_obj.save()

        self.import_obj.status = ImportStatus.AWAITING.value
        self.import_obj.save()

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
                return str(datetime.date(year, month, day))
            if serializer == "BOOLEAN_X":
                if value == "X":
                    return True
                return False
        return value

    # Creates valid Report and Form3X objects from a row
    # returns as a tuple: report, form_3x
    def preprocess_report(self, row):
        keys_to_skip = [
            "filer_committee_id_number"
        ]
        F3X_cols = F3X_SCHEMA.keys()

        report_obj = {
            "committee_account_id": str(self.import_obj.committee_account.id)
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

        return report_obj, f3x_obj

    # Creates valid Transaction and ScheduleA objects from a row
    # returns as a tuple: transaction, schedule_a
    def preprocess_transaction(self, row):
        keys_to_skip = [
            "filer_committee_id_number",
            "donor_committee_fec_id",
            "donor_committee_name",
            "back_reference_tran_id_number",
            "back_reference_sched_name"
        ]
        sch_a_cols = SCH_A_SCHEMA.keys()

        transaction_obj = {
            "committee_account_id": str(self.import_obj.committee_account.id),
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

        contact_fields["type"] = transaction_obj["entity_type"]
        transaction_obj["contact_1"] = self.preprocess_contact(contact_fields)
        transaction_obj["schedule_a"] = sch_a_obj
        transaction_obj["children"] = []
        return transaction_obj

    # Creates a valid Contact object from a row OR matches with an earlier contact
    def preprocess_contact(self, contact_fields):
        for contact in self.records["contacts"].values():
            if (
                contact_fields.get("street_1") == contact["street_1"]
                and contact_fields.get("street_2") == contact["street_2"]
                and contact_fields.get("city") == contact["city"]
                and contact_fields.get("state") == contact["state"]
                and contact_fields.get("zip") == contact["zip"]
                and contact_fields.get("name") == contact["name"]
                and contact_fields.get("first_name") == contact["first_name"]
                and contact_fields.get("last_name") == contact["last_name"]
                and contact_fields.get("middle_name") == contact["middle_name"]
                and contact_fields.get("prefix") == contact["prefix"]
                and contact_fields.get("suffix") == contact["suffix"]
            ):
                return contact

        contact_fields["committee_account_id"] = str(self.import_obj.committee_account.id)
        temp_uuid = str(uuid.uuid4())
        contact_fields["temp_uuid"] = temp_uuid
        self.records["contacts"][temp_uuid] = contact_fields
        return contact_fields

    # preprocesss a valid MemoText object from a row, associating it to a transaction
    def preprocess_memo_transaction(self, row, transaction):
        memo_text = self.preprocess_memo_text(row)
        transaction["memo_text"] = memo_text
        return memo_text

    # preprocesss a valid MemoText object from a row, associating it to the file's report
    def preprocess_memo_report(self, row):
        memo_text = self.preprocess_memo_text(row)
        memo_text["report"] = self.records["report"]
        return memo_text

    # helper function for creating a valid MemoText
    def preprocess_memo_text(self, row):
        keys_to_skip = [
            "filer_committee_id_number",
            "back_reference_tran_id_number",
            "back_reference_sched_form_name"
        ]
        memo_cols = TEXT_SCHEMA.keys()

        memo_obj = {
            "committee_account_id": str(self.import_obj.committee_account.id)
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

        return memo_obj

    # Runs the django management command
    def preprocess(self):
        # Open the file
        filename = self.import_obj.dot_fec_file
        file = open(filename, "r")
        file.readline()  # Skip the HDR row

        # Parse the file line-by-line
        line = file.readline()
        old_row = []
        row = line.split(SEP_CHAR)
        previous_transaction = None

        while len(line) > 0:
            # Handle F3X reports
            if row[0] == "F3XN":
                report, form_3x = self.preprocess_report(row)
                self.records["report"] = report
                self.records["form_3x"] = form_3x
            # Handle Schedule A Transactions (just Individual Receipts)
            elif row[0] and "SA" in row[0]:
                # Creating a transaction also defines contacts as a by-product
                transaction = self.preprocess_transaction(row)

                # Check to see if the new transaction has a parent
                child_transaction = False
                for trans in self.records["transactions"]:
                    if trans["transaction_id"] == row[3]:
                        child_transaction = True
                        trans["children"].append(transaction)
                    for child in trans.get("children", []):
                        if child["transaction_id"] == row[3]:
                            child_transaction = True
                            child["children"].append(transaction)
                    if child_transaction:
                        break

                # Only add top-level transactions to the records
                # (the current implementation cannot handle grandchildren)
                if not child_transaction:
                    self.records["transactions"].append(transaction)
                previous_transaction = transaction

            # # Handle Memo Text
            elif row[0] == "TEXT":
                memo_text = None
                if row[4] == "SA11AI" and old_row and old_row[0] == "SA11AI":
                    memo_text = self.preprocess_memo_transaction(row, previous_transaction)
                if row[4] == "F3XN":
                    memo_text = self.preprocess_memo_report(row)

                if memo_text is not None:
                    self.records["memos"].append(memo_text)

            line = file.readline()
            old_row = row
            row = line.split(SEP_CHAR)

        print(
            "Creating records:\n"
            "1 new report\n"
            f"{len(self.records['memos'])} new memo(s)\n"
            f"{len(self.records['contacts'].keys())} new contacts(s)\n"
            f"{len(self.records['transactions'])} new top-level transaction(s)\n"
        )

        self.import_obj.report_type = "F3X"
        self.import_obj.coverage_from_date = self.records["report"].get("coverage_from_date", None)
        self.import_obj.coverage_through_date = self.records["report"].get("coverage_through_date", None)
        self.import_obj.preprocessed_json = json.dumps(self.records)
        self.import_obj.save()
