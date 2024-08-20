from django.core.management.base import BaseCommand
from fecfiler.devops.login_dot_gov_utils import backout_login_dot_gov_cert


class Command(BaseCommand):
    help = "Backout certificate"

    def add_arguments(self, parser):
        parser.add_argument("cf_token", type=str)
        parser.add_argument("cf_space_name", type=str)
        parser.add_argument("cf_service_instance_name", type=str)

    def handle(self, *args, **options):
        try:
            cf_token = options["cf_token"]
            cf_space_name = options["cf_space_name"]
            cf_service_instance_name = options["cf_service_instance_name"]

            self.stdout.write(self.style.NOTICE("STARTING backout_cert command"))
            backout_login_dot_gov_cert(cf_token, cf_space_name, cf_service_instance_name)
            self.stdout.write(self.style.NOTICE("FINISHED backout_cert command"))
        except Exception:
            self.stdout.write(self.style.ERROR("FAILED to execute backout_cert command"))
