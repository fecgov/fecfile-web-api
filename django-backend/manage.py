#!/usr/bin/env python
import os
import sys
from fecfiler import settings

core = [
    "create_committee_views",
    "migrate",
    "makemigrations",
]
developer = ["loaddata", "load_committee_data", "test"]

if __name__ == "__main__":
    subcommand = sys.argv[1]
    if subcommand in core or (
        settings.ENABLE_DEVELOPER_COMMANDS and subcommand in developer
    ):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fecfiler.settings")
        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)
