from .fecfile_base import FECCommand
from fecfiler.devops.utils.login_dot_gov_cert import install_login_dot_gov_cert


class Command(FECCommand):
    help = "Install certificate"
    command_name = "install_login_dot_gov_cert"

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
        install_login_dot_gov_cert(
            cf_token, cf_organization_name, cf_space_name, cf_service_instance_name
        )
