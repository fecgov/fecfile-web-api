from fecfiler.devops.utils.login_dot_gov_cert_utils import backout_login_dot_gov_cert
from .fecfile_base import FECCommand


class Command(FECCommand):
    help = "Backout certificate"
    command_name = "backout_login_dot_gov_cert"

    def add_arguments(self, parser):
        parser.add_argument("cf_token", type=str)
        parser.add_argument("cf_organization_name", type=str)
        parser.add_argument("cf_space_name", type=str)
        parser.add_argument("cf_service_instance_name", type=str)

    def command(self, *args, **options):
        cf_token = options["cf_token"]
        cf_organization_name = options["cf_organization_name"]
        cf_space_name = options["cf_space_name"]
        cf_service_instance_name = options["cf_service_instance_name"]
        backout_login_dot_gov_cert(
            cf_token, cf_organization_name, cf_space_name, cf_service_instance_name
        )
