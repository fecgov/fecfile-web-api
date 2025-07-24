from random import choice, randrange
import json
from os import path
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.contacts.models import Contact
from fecfiler.transactions.tests.utils import create_schedule_a


class LocustDataGenerator:
    def __init__(self, committee):
        self.committee = committee

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

            coverage_from_date = f"{year}-{from_date}"
            coverage_through_date = f"{year}-{through_date}"
            form_3x_list.append(
                create_form3x(
                    self.committee, coverage_from_date, coverage_through_date, {}, quarter
                )
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
                Contact(
                    **{
                        "committee_account_id": self.committee.id,
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
            )

        return contacts

    def generate_single_transactions(self, count, reports, contacts):
        transactions = []
        for _ in range(count):
            transaction_type_identifier = "INDIVIDUAL_RECEIPT"
            contact = choice(contacts)
            report = choice(reports)
            contribution_date = report.coverage_from_date
            contribution_amount = randrange(25, 10000)
            aggregation_group = "GENERAL"
            form_type = "SA11AI"

            new_transaction = create_schedule_a(
                transaction_type_identifier,
                self.committee,
                contact,
                contribution_date,
                contribution_amount,
                aggregation_group,
                form_type,
                report=report,
            )
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
            transaction_type_identifier = "INDIVIDUAL_RECEIPT"
            contact = choice(contacts)
            report = choice(reports)
            contribution_date = report.coverage_from_date
            contribution_amount = randrange(25, 10000)
            aggregation_group = "GENERAL"
            form_type = "SA11AI"

            a = create_schedule_a(
                transaction_type_identifier,
                self.committee,
                contact,
                contribution_date,
                contribution_amount,
                aggregation_group,
                form_type,
                report=report,
            )
            b = create_schedule_a(
                transaction_type_identifier,
                self.committee,
                contact,
                contribution_date,
                contribution_amount,
                aggregation_group,
                form_type,
                report=report,
                parent_id=a.id,
            )
            create_schedule_a(
                transaction_type_identifier,
                self.committee,
                contact,
                contribution_date,
                contribution_amount,
                aggregation_group,
                form_type,
                report=report,
                parent_id=b.id,
            )
            triple_transactions.append(a)
        return triple_transactions


def save_json(values, name="data"):
    directory = path.dirname(path.abspath(__file__))
    filename = f"{name}.locust.json"
    full_filename = path.join(directory, "locust-data", filename)
    file = open(full_filename, "w")
    file.write(json.dumps(values))
    file.close()
