from .fecfile_base import FECCommand
from fecfiler.devops.utils.login_dot_gov_cert_utils import cleanup_login_dot_gov_certs


class Command(FECCommand):
    help = "Cleanup certificates"
    command_name = "cleanup_login_dot_gov_certs"

    def command(self, *args, **options):
        cleanup_login_dot_gov_certs()
