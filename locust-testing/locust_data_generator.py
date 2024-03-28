from random import choice, randrange
import json
from os import path


def generate_form_3x(count=1, collision_maximum=1000):
    reports_and_dates = [
        ["Q1", "01-01", "03-31"],
        ["Q2", "04-01", "06-30"],
        ["Q3", "07-01", "09-30"],
        ["Q4", "10-01", "12-31"]
    ]
    form_3x_list = []
    dates_taken = set()
    collision_count = 0

    while len(form_3x_list) < count and collision_count < collision_maximum:
        quarter, from_date, through_date = choice(reports_and_dates)
        year = randrange(1000, 9999)
        hashable_date = f"{year}, {quarter}"
        if (hashable_date in dates_taken):
            collision_count+=1
            continue

        dates_taken.add(hashable_date)
        alert_text = "Are you sure you want to submit this form \
                electronically? Please note that you cannot undo this action. \
                Any changes needed will need to be filed as an amended report."

        form_3x_list.append(
            {
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


def generate_contacts(count=1):
    street_names = ["Main", "Test", "Place", "Home", "Domain", "Victory", "Word"]
    street_types = ["St", "Dr", "Ln", "Way"]
    last_names = ["Testerson", "Smith", "Worker", "Menace", "Wonder"]
    first_names = ["Bill", "George", "Madeline", "May", "Alex"]
    prefixes = ["Mr", "Mrs", "Ms", "Mz", "Sir", None]
    suffixes = ["I", "II", "III", "IV", "V", None]

    return [
        {
            "type": "IND",
            "street_1": f"{randrange(100, 999)} {choice(street_names)} {choice(street_types)}",
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
            "occupation": "Job"
        } for _ in range(count)
    ]


def generate_single_transactions(count=1, contacts=None, report_ids=None):
    transactions = []
    for _ in range(count):
        contact = choice(contacts) if contacts else generate_contacts()[0]
        new_transaction = {
            "children": [],
            "form_type": "SA11AI",
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT",
            "aggregation_group": "GENERAL",
            "schema_name": "INDIVIDUAL_RECEIPT",
            "report_ids": [choice(report_ids)] if report_ids else None,
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
            "contribution_date": "2024-02-01",
            "contribution_amount": randrange(25,10000),
            "contribution_purpose_descrip": None,
            "contributor_employer": contact["employer"],
            "contributor_occupation": contact["occupation"],
            "memo_code": None,
            "contact": contact,
            "contact_id": contact.get("id", None),
            "schedule_id": "A"
        }

        transactions.append(new_transaction)

    return transactions


def generate_triple_transactions(count=1, contacts=None, report_ids=None):
    triple_transactions = []
    for _ in range(count):
        a, b, c = generate_single_transactions(3, contacts, report_ids)
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


class LocustDataGenerator:
    form3x_count = 0
    form3x_list = []
    contact_count = 0
    contact_list = []
    single_transaction_count = 0
    single_transaction_list = []
    triple_transaction_count = 0
    triple_transaction_list = []

    def __init__(self, args):
        try:
            self.form3x_count = int(args.form_3x)
            self.contact_count = int(args.contacts)
            self.single_transaction_count = int(args.single_transactions)
            self.triple_transaction_count = int(args.triple_transactions)
        except:
            print("Non-integer value passed as argument")

        if self.form3x_count + self.contact_count + self.single_transaction_count + self.triple_transaction_count == 0:
            print("No arguments provided.  Run with --help or -h for instructions")

    def build(self):
        if self.form3x_count > 0:
            self.form3x_list = generate_form_3x(self.form3x_count)
        if self.contact_count > 0:
            self.contact_list = generate_contacts(self.contact_count)
        if self.single_transaction_count > 0:
            self.single_transaction_list = generate_single_transactions(self.single_transaction_count, self.contact_list)
        if self.triple_transaction_count > 0:
            self.triple_transaction_list = generate_triple_transactions(self.triple_transaction_count, self.contact_list)

    def dump(self):
        if self.form3x_count > 0:
            save_json(self.form3x_list, "form-3x")
        if self.contact_count > 0:
            save_json(self.contact_list, "contacts")
        if self.single_transaction_count > 0:
            save_json(self.single_transaction_list, "single-transactions")
        if self.triple_transaction_count > 0:
            save_json(self.triple_transaction_list, "triple-transactions")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="This script generates test data as json files for use in locust swarm testing"
    )
    parser.add_argument(
        "--form-3x",
        default=0,
        help="The number of form-3x reports to be defined",
    )
    parser.add_argument(
        "--contacts",
        default=0,
        help="The number of contacts to be defined",
    )
    parser.add_argument(
        "--single-transactions",
        default=0,
        help="The number of transactions to be created without any children",
    )
    parser.add_argument(
        "--triple-transactions",
        default=0,
        help="The number of transactions to be created with children and grandchildren",
    )
    args = parser.parse_args()

    generator = LocustDataGenerator(args)
    generator.build()
    generator.dump()