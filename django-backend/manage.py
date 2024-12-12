#!/usr/bin/env python
import os
import sys
from fecfiler import settings

core = [
    "help",
    "create_committee_views",
    "migrate",
    "makemigrations",
    "showmigrations",
    # devops
    "backout_login_dot_gov_cert",
    "clear_fallback_django_keys",
    "gen_and_install_django_key",
    "gen_and_stage_login_dot_gov_cert",
    "install_login_dot_gov_cert",
    "update_creds_service",
]
developer = [
    "loaddata",
    "test",
    "shell",
    # committee_accounts
    "load_committee_data",
    "delete_committee_account",
    # reports
    "delete_committee_reports",
    # users
    "reset_security_consent_date"
]

if __name__ == "__main__":
    subcommand = sys.argv[1]
    if subcommand in core or (
        settings.ENABLE_DEVELOPER_COMMANDS and subcommand in developer
    ):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fecfiler.settings")
        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)
