from django.core.management.base import BaseCommand
from fecfiler.devops.django_key_utils import clear_fallback_django_keys


class Command(BaseCommand):
    help = "Clear fallback keys"

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
                self.style.NOTICE("STARTING clear_fallback_django_keys command")
            )
            clear_fallback_django_keys(cf_token, cf_space_name, cf_service_instance_name)
            self.stdout.write(
                self.style.NOTICE("FINISHED clear_fallback_django_keys command")
            )
        except Exception:
            self.stdout.write(
                self.style.ERROR("FAILED to execute clear_fallback_django_keys command")
            )
