from random import choice, randrange
from fecfiler.reports.models import Report
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.reports.models import ReportTransaction
from fecfiler.contacts.models import Contact


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
        report_list = []
        dates_taken = set()
        collision_count = 0

        for _ in range(count):
            form_3x_list.append(Form3X())
        form_3x_list = Form3X.objects.bulk_create(form_3x_list)

        while len(report_list) < count and collision_count < collision_maximum:
            quarter, from_date, through_date = choice(reports_and_dates)
            year = randrange(1000, 9999)
            hashable_date = f"{year}, {quarter}"
            if hashable_date in dates_taken:
                collision_count += 1
                continue
            dates_taken.add(hashable_date)

            coverage_from_date = f"{year}-{from_date}"
            coverage_through_date = f"{year}-{through_date}"
            report_list.append(
                Report(
                    **{
                        "form_type": "F3XN",
                        "committee_account_id": self.committee.id,
                        "coverage_from_date": coverage_from_date,
                        "coverage_through_date": coverage_through_date,
                        "report_code": quarter,
                        "form_3x_id": form_3x_list[len(report_list)].id,
                    }
                )
            )

        return Report.objects.bulk_create(report_list)

    def generate_contacts(self, count):
        street_names = ["Main", "Test", "Place", "Home", "Domain", "Victory", "Word"]
        street_types = ["St", "Dr", "Ln", "Way"]
        last_names = ["Testerson", "Smith", "Worker", "Menace", "Wonder"]
        first_names = ["Bill", "George", "Madeline", "May", "Alex"]
        prefixes = ["Mr", "Mrs", "Ms", "Mz", "Sir", None]
        suffixes = ["I", "II", "III", "IV", "V", None]

        contact_list = []
        for _ in range(count):
            street_1 = (
                f"{randrange(1, 999)} {choice(street_names)} {choice(street_types)}"
            )
            contact_list.append(
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

        return Contact.objects.bulk_create(contact_list)

    def generate_single_schedule_a_transactions(self, count, reports, contacts):
        schedule_a_list = []
        transaction_list = []
        report_transaction_list = []
        for _ in range(count):
            transaction_type_identifier = "INDIVIDUAL_RECEIPT"
            contact = choice(contacts)
            report = choice(reports)
            contribution_date = report.coverage_from_date
            contribution_amount = randrange(25, 10000)
            aggregation_group = "GENERAL"
            form_type = "SA11AI"

            schedule_a_list.append(
                ScheduleA(
                    **{
                        "contribution_date": contribution_date,
                        "contribution_amount": contribution_amount,
                        # Store report ID in purpose field
                        "contribution_purpose_descrip": report.id,
                    }
                )
            )

        schedule_a_list = ScheduleA.objects.bulk_create(schedule_a_list)
        for schedule_a in schedule_a_list:
            transaction_list.append(
                Transaction(
                    **{
                        "transaction_type_identifier": transaction_type_identifier,
                        "committee_account_id": self.committee.id,
                        "contact_1_id": contact.id,
                        "aggregation_group": aggregation_group,
                        "form_type": form_type,
                        "schedule_a_id": schedule_a.id,
                    }
                )
            )

        transaction_list = Transaction.objects.bulk_create(transaction_list)

        for transaction in transaction_list:
            report_transaction_list.append(
                ReportTransaction(
                    **{
                        # Retrieve report ID from purpose field
                        "report_id": transaction.schedule_a.contribution_purpose_descrip,
                        "transaction_id": transaction.id,
                    }
                )
            )
        ReportTransaction.objects.bulk_create(report_transaction_list)

        return transaction_list

    def generate_triple_schedule_a_transactions(self, count, reports, contacts):
        tier1_transactions = self.generate_single_schedule_a_transactions(
            count, reports, contacts
        )
        tier2_transactions = self.generate_single_schedule_a_transactions(
            count, reports, contacts
        )
        tier3_transactions = self.generate_single_schedule_a_transactions(
            count, reports, contacts
        )

        for index in range(count):
            tier3_transactions[index].parent_transaction_id = tier2_transactions[index].id
            tier2_transactions[index].parent_transaction_id = tier1_transactions[index].id
        Transaction.objects.bulk_update(
            tier3_transactions + tier2_transactions, ["parent_transaction_id"]
        )

        return tier1_transactions

    def generate_single_schedule_b_transactions(self, count, reports, contacts):
        schedule_b_list = []
        transaction_list = []
        report_transaction_list = []
        for _ in range(count):
            transaction_type_identifier = "OPERATING_EXPENDITURE"
            contact = choice(contacts)
            report = choice(reports)
            contribution_date = report.coverage_from_date
            contribution_amount = randrange(25, 10000)
            aggregation_group = "GENERAL"
            form_type = "SB21B"

            schedule_b_list.append(
                ScheduleB(
                    **{
                        "expenditure_date": contribution_date,
                        "expenditure_amount": contribution_amount,
                        # Store report ID in purpose field
                        "expenditure_purpose_descrip": report.id,
                    }
                )
            )

        schedule_b_list = ScheduleB.objects.bulk_create(schedule_b_list)
        for schedule_b in schedule_b_list:
            transaction_list.append(
                Transaction(
                    **{
                        "transaction_type_identifier": transaction_type_identifier,
                        "committee_account_id": self.committee.id,
                        "contact_1_id": contact.id,
                        "aggregation_group": aggregation_group,
                        "form_type": form_type,
                        "schedule_b_id": schedule_b.id,
                    }
                )
            )

        transaction_list = Transaction.objects.bulk_create(transaction_list)

        for transaction in transaction_list:
            report_transaction_list.append(
                ReportTransaction(
                    **{
                        # Retrieve report ID from purpose field
                        "report_id": transaction.schedule_b.expenditure_purpose_descrip,
                        "transaction_id": transaction.id,
                    }
                )
            )
        ReportTransaction.objects.bulk_create(report_transaction_list)

        return transaction_list

    def generate_triple_schedule_b_transactions(self, count, reports, contacts):
        tier1_transactions = self.generate_single_schedule_b_transactions(
            count, reports, contacts
        )
        tier2_transactions = self.generate_single_schedule_b_transactions(
            count, reports, contacts
        )
        tier3_transactions = self.generate_single_schedule_b_transactions(
            count, reports, contacts
        )

        for index in range(count):
            tier3_transactions[index].parent_transaction_id = tier2_transactions[index].id
            tier2_transactions[index].parent_transaction_id = tier1_transactions[index].id
        Transaction.objects.bulk_update(
            tier3_transactions + tier2_transactions, ["parent_transaction_id"]
        )

        return tier1_transactions
