from django.core.management.base import BaseCommand
from fecfiler.devops.utils.login_dot_gov_cert_utils import cleanup_login_dot_gov_certs


class Command(BaseCommand):
    help = "Cleanup certificates"

    def handle(self):
        try:
            self.stdout.write(
                self.style.NOTICE("STARTING cleanup_login_dot_gov_certs command")
            )
            cleanup_login_dot_gov_certs()
            self.stdout.write(
                self.style.NOTICE("FINISHED cleanup_login_dot_gov_certs command")
            )
        except Exception:
            self.stdout.write(
                self.style.ERROR("FAILED to execute cleanup_login_dot_gov_certs command")
            )
