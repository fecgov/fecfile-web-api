from random import choice, randrange
import json
from os import path


class LocustDataGenerator:
    def __init__(self, committee_id):
        self.committee_id = committee_id

    def generate_form_3x(self, count, collision_maximum=1000):
        reports_and_dates = [
            ["Q1", "01-01", "03-31"],
            ["Q2", "04-01", "06-30"],
            ["Q3", "07-01", "09-30"],
            ["YE", "10-01", "12-31"],
        ]
        form_3x_list = []
        dates_taken = set()
        collision_count = 0

        while len(form_3x_list) < count and collision_count < collision_maximum:
            quarter, from_date, through_date = choice(reports_and_dates)
            year = randrange(1000, 9999)
            hashable_date = f"{year}, {quarter}"
            if hashable_date in dates_taken:
                collision_count += 1
                continue

            dates_taken.add(hashable_date)
            alert_text = "Are you sure you want to submit this form \
                    electronically? Please note that you cannot undo this action. \
                    Any changes needed will need to be filed as an amended report."

            form_3x_list.append(
                {
                    "committee_account_id": self.committee_id,
                    "hasChangeOfAddress": "true",
                    "submitAlertText": alert_text,
                    "report_type": "F3X",
                    "form_type": "F3XN",
                    "report_code": quarter,
                    "date_of_election": None,
                    "state_of_election": None,
                    "coverage_from_date": f"{year}-{from_date}",
                    "coverage_through_date": f"{year}-{through_date}",
                }
            )

        return form_3x_list

    def generate_contacts(self, count):
        street_names = ["Main", "Test", "Place", "Home", "Domain", "Victory", "Word"]
        street_types = ["St", "Dr", "Ln", "Way"]
        last_names = ["Testerson", "Smith", "Worker", "Menace", "Wonder"]
        first_names = ["Bill", "George", "Madeline", "May", "Alex"]
        prefixes = ["Mr", "Mrs", "Ms", "Mz", "Sir", None]
        suffixes = ["I", "II", "III", "IV", "V", None]

        contacts = []
        for _ in range(count):
            street_1 = (
                f"{randrange(1, 999)} {choice(street_names)} {choice(street_types)}"
            )
            contacts.append(
                {
                    "committee_account_id": self.committee_id,
                    "type": "IND",
                    "street_1": street_1,
                    "city": "Testville",
                    "state": "AK",
                    "zip": "12345",
                    "country": "USA",
                    "last_name": choice(last_names),
                    "first_name": choice(first_names),
                    "middle_name": choice(first_names),
                    "prefix": choice(prefixes),
                    "suffix": choice(suffixes),
                    "street_2": None,
                    "telephone": None,
                    "employer": "Business Inc.",
                    "occupation": "Job",
                }
            )

        return contacts

    def generate_single_transactions(self, count, reports, contacts):
        transactions = []
        for _ in range(count):
            report = choice(reports)
            contact = choice(contacts)
            new_transaction = {
                "committee_account_id": self.committee_id,
                "children": [],
                "form_type": "SA11AI",
                "transaction_type_identifier": "INDIVIDUAL_RECEIPT",
                "aggregation_group": "GENERAL",
                "schema_name": "INDIVIDUAL_RECEIPT",
                "report_ids": [report["id"]],
                "entity_type": "IND",
                "contributor_last_name": contact["last_name"],
                "contributor_first_name": contact["first_name"],
                "contributor_middle_name": contact["middle_name"],
                "contributor_prefix": contact["prefix"],
                "contributor_suffix": contact["suffix"],
                "contributor_street_1": contact["street_1"],
                "contributor_street_2": None,
                "contributor_city": contact["city"],
                "contributor_state": contact["state"],
                "contributor_zip": contact["zip"],
                "contribution_date": report["coverage_from_date"],
                "contribution_amount": randrange(25, 10000),
                "contribution_purpose_descrip": None,
                "contributor_employer": contact["employer"],
                "contributor_occupation": contact["occupation"],
                "memo_code": None,
                "contact_1": contact,
                "contact_1_id": contact.get("id", None),
                "schedule_id": "A",
            }

            transactions.append(new_transaction)

        return transactions

    def generate_triple_transactions(
        self,
        count,
        reports,
        contacts,
    ):
        triple_transactions = []
        for _ in range(count):
            a, b, c = self.generate_single_transactions(3, reports, contacts)
            b["children"].append(c)
            a["children"].append(b)
            triple_transactions.append(a)
        return triple_transactions


def save_json(values, name="data"):
    directory = path.dirname(path.abspath(__file__))
    filename = f"{name}.locust.json"
    full_filename = path.join(directory, "locust-data", filename)
    file = open(full_filename, "w")
    file.write(json.dumps(values))
    file.close()
