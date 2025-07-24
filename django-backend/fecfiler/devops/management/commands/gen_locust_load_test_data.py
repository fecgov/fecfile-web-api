from .fecfile_base import FECCommand
from fecfiler.devops.utils.load_test_utils import LoadTestUtils


class Command(FECCommand):
    help = "Generate Locust load test data"
    command_name = "gen_locust_load_test_data"

    def add_arguments(self, parser):
        parser.add_argument("test_user_email", type=str)
        parser.add_argument("--new_committee_id", type=str, default="C33333333")
        parser.add_argument("--number_of_reports", type=int, default=10)
        parser.add_argument("--number_of_contacts", type=int, default=100)
        parser.add_argument("--number_of_transactions", type=int, default=500)
        parser.add_argument(
            "--single_to_triple_transaction_ratio", type=float, default=9 / 10
        )

    def command(self, *args, **options):
        load_test_utils = LoadTestUtils()
        load_test_utils.create_load_test_committee_and_data(
            options["test_user_email"],
            options["new_committee_id"],
            options["number_of_reports"],
            options["number_of_contacts"],
            options["number_of_transactions"],
            options["single_to_triple_transaction_ratio"],
        )
