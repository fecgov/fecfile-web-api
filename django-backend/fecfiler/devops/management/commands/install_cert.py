from django.core.management.base import BaseCommand
from fecfiler.devops.login_dot_gov_utils import install_login_dot_gov_cert


class Command(BaseCommand):
    help = "Install certificate"

    def add_arguments(self, parser):
        parser.add_argument("cf_token", type=str)
        parser.add_argument("cf_space_name", type=str)
        parser.add_argument("cf_service_instance_name", type=str)

    def handle(self, *args, **options):
        try:
            cf_token = options["cf_token"]
            cf_space_name = options["cf_space_name"]
            cf_service_instance_name = options["cf_service_instance_name"]

            self.stdout.write(self.style.NOTICE("STARTING install_cert command"))
            install_login_dot_gov_cert(cf_token, cf_space_name, cf_service_instance_name)
            self.stdout.write(self.style.NOTICE("FINISHED install_cert command"))
        except Exception:
            self.stdout.write(self.style.ERROR("FAILED to execute install_cert command"))
