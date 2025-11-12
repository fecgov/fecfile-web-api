from .fecfile_base import FECCommand
from fecfiler.devops.utils.cf_api import update_credentials
import json


class Command(FECCommand):
    help = "Update cf credential service with cred(s)"
    command_name = "update_creds_service"

    def add_arguments(self, parser):
        parser.add_argument("cf_token", type=str)
        parser.add_argument("cf_organization_name", type=str)
        parser.add_argument("cf_space_name", type=str)
        parser.add_argument("cf_service_instance_name", type=str)
        parser.add_argument("credentials_dict", type=json.loads)

    def command(self, *args, **options):
        cf_token = options["cf_token"]
        cf_organization_name = options["cf_organization_name"]
        cf_space_name = options["cf_space_name"]
        cf_service_instance_name = options["cf_service_instance_name"]
        credentials_dict = options["credentials_dict"]
        update_credentials(
            cf_token,
            cf_organization_name,
            cf_space_name,
            cf_service_instance_name,
            credentials_dict,
        )
