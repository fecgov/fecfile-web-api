from django.core.management.base import BaseCommand
from fecfiler.devops.utils.cf_api_utils import update_credentials
import json


class Command(BaseCommand):
    help = "Update cf credential service with cred(s)"

    def add_arguments(self, parser):
        parser.add_argument("cf_token", type=str)
        parser.add_argument("cf_space_name", type=str)
        parser.add_argument("cf_service_instance_name", type=str)
        parser.add_argument("credentials_dict", type=json.loads)

    def handle(self, *args, **options):
        try:
            cf_token = options["cf_token"]
            cf_space_name = options["cf_space_name"]
            cf_service_instance_name = options["cf_service_instance_name"]
            credentials_dict = options["credentials_dict"]

            self.stdout.write(self.style.NOTICE("STARTING update_creds_service command"))
            update_credentials(
                cf_token, cf_space_name, cf_service_instance_name, credentials_dict
            )
            self.stdout.write(self.style.NOTICE("FINISHED update_creds_service command"))
        except Exception:
            self.stdout.write(
                self.style.ERROR("FAILED to execute update_creds_service command")
            )
