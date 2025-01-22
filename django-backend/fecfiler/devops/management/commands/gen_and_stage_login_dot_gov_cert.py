from django.core.management.base import BaseCommand
from fecfiler.devops.utils.login_dot_gov_cert_utils import (
    gen_and_stage_login_dot_gov_cert,
)


class Command(BaseCommand):
    help = "Generate and stage certificates"

    def add_arguments(self, parser):
        parser.add_argument("cf_token", type=str)
        parser.add_argument("cf_space_name", type=str)
        parser.add_argument("cf_service_instance_name", type=str)

    def handle(self, *args, **options):
        try:
            cf_token = options["cf_token"]
            cf_space_name = options["cf_space_name"]
            cf_service_instance_name = options["cf_service_instance_name"]

            self.stdout.write(
                self.style.NOTICE("STARTING gen_and_stage_login_dot_gov_cert command")
            )
            gen_and_stage_login_dot_gov_cert(
                cf_token, cf_space_name, cf_service_instance_name
            )
            self.stdout.write(
                self.style.NOTICE("FINISHED gen_and_stage_login_dot_gov_cert command")
            )
        except Exception:
            self.stdout.write(
                self.style.ERROR(
                    "FAILED to execute gen_and_stage_login_dot_gov_cert command"
                )
            )
