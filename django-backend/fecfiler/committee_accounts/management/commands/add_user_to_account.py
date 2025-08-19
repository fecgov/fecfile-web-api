from fecfiler.devops.management.commands.fecfile_base import FECCommand
from fecfiler.devops.utils.load_test_utils import LoadTestUtils


class Command(FECCommand):
    help = "Generate Locust load test data"
    command_name = "gen_locust_load_test_data"

    def add_arguments(self, parser):
        parser.add_argument("user_email", type=str)
        parser.add_argument("committee_id", type=str)

    def command(self, *args, **options):
        load_test_utils = LoadTestUtils()
        load_test_utils.create_load_test_committees_and_data(
            options["test_user_email"],
            options["number_of_committees"],
            options["number_of_reports"],
            options["number_of_contacts"],
            options["number_of_transactions"],
            options["single_to_triple_transaction_ratio"],
        )
