from .fecfile_base import FECCommand
from fecfiler.devops.utils.django_key import gen_and_install_django_key


class Command(FECCommand):
    help = "Generate and install key"
    command_name = "gen_and_install_django_key"

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
        gen_and_install_django_key(
            cf_token, cf_organization_name, cf_space_name, cf_service_instance_name
        )
