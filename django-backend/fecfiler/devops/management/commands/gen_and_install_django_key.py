from django.core.management.base import BaseCommand
from fecfiler.devops.utils.django_key_utils import gen_and_install_django_key


class Command(BaseCommand):
    help = "Generate and install key"

    def add_arguments(self, parser):
        parser.add_argument("cf_token", type=str)
        parser.add_argument("cf_organization_name", type=str)
        parser.add_argument("cf_space_name", type=str)
        parser.add_argument("cf_service_instance_name", type=str)

    def handle(self, *args, **options):
        try:
            cf_token = options["cf_token"]
            cf_organization_name = options["cf_organization_name"]
            cf_space_name = options["cf_space_name"]
            cf_service_instance_name = options["cf_service_instance_name"]

            self.stdout.write(
                self.style.NOTICE("STARTING gen_and_install_django_key command")
            )
            gen_and_install_django_key(
                cf_token, cf_organization_name, cf_space_name, cf_service_instance_name
            )
            self.stdout.write(
                self.style.NOTICE("FINISHED gen_and_install_django_key command")
            )
        except Exception:
            self.stdout.write(
                self.style.ERROR("FAILED to execute gen_and_install_django_key command")
            )
