from django.core.management.base import BaseCommand, CommandError
from fecfiler.settings import MOCK_OPENFEC_REDIS_URL, BASE_DIR
import redis
import os
import json


class Command(BaseCommand):
    help = "Load mock committee data into redis"

    # def add_arguments(self, parser):
    #     parser.add_argument("source")

    def handle(self, *args, **options):
        if MOCK_OPENFEC_REDIS_URL:
            redis_instance = redis.Redis.from_url(MOCK_OPENFEC_REDIS_URL)
            COMMITTEE_DATA_REDIS_KEY = "COMMITTEE_DATA"
            if not options.get("source"):
                path = os.path.join(
                    BASE_DIR, "mock_openfec/management/commands/committee_data.json"
                )
                with open(path) as file:
                    committee_data = file.read()
                redis_instance.set(COMMITTEE_DATA_REDIS_KEY, committee_data)

            self.stdout.write(self.style.SUCCESS(f"Successfully loaded committees"))
