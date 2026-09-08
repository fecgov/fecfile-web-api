from django.core.management.base import CommandError

from .fecfile_base import FECCommand
from fecfiler.devops.utils.load_test import LoadTestUtils


class Command(FECCommand):
    help = "Delete Locust load test data"
    command_name = "delete_locust_load_test_data"

    def command(self, *args, **options):
        load_test_utils = LoadTestUtils()
        try:
            load_test_utils.validate_load_mirror_runtime()
        except ValueError as error:
            raise CommandError(str(error)) from error

        load_test_utils.delete_load_test_committees_and_data()
