#!/usr/bin/env python
import os
import sys
import structlog
from fecfiler import settings

logger = structlog.get_logger(__name__)

allowed_commands = [
    "help",
    "migrate",
    "lintmigrations",
    "makemigrations",
    "showmigrations",
    # DEVOPS COMMANDS #
    "backout_login_dot_gov_cert",
    "cleanup_login_dot_gov_certs",
    "clear_fallback_django_keys",
    "gen_and_install_django_key",
    "gen_and_stage_login_dot_gov_cert",
    "install_login_dot_gov_cert",
    "update_creds_service",
    "disable_user",
    "gen_locust_load_test_data",
]
restricted_commands = [
    "loaddata",
    "test",
    "shell",
    # COMMITTEE ACCOUNT COMMANDS #
    "load_committee_data",
    "delete_committee_account",
    # REPORT COMMANDS #
    "delete_committee_reports",
    # users
    "reset_security_consent_date",
]

if __name__ == "__main__":
    subcommand = sys.argv[1]
    if subcommand in allowed_commands or (
        settings.ENABLE_RESTRICTED_COMMANDS and subcommand in restricted_commands
    ):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fecfiler.settings")
        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)
    else:
        logger.error(f"Command '{subcommand}' is not allowed")
        sys.exit(1)
