from django.core.management.base import BaseCommand
from fecfiler import settings
import redis
import os
from fecfiler.s3 import S3_SESSION
from fecfiler.committee_accounts.utils import COMMITTEE_DATA_REDIS_KEY


class Command(BaseCommand):
    help = "Load mock committee data into redis"

    def add_arguments(self, parser):
        parser.add_argument("--s3", action="store_true")

    def handle(self, *args, **options):
        if settings.FLAG__COMMITTEE_DATA_SOURCE == "MOCKED":
            print("MOCK")
            redis_instance = redis.Redis.from_url(settings.MOCK_OPENFEC_REDIS_URL)
            if not options.get("s3"):
                path = os.path.join(
                    settings.BASE_DIR,
                    "committee_accounts/management/commands/committee_data.json"
                )
                with open(path) as file:
                    committee_data = file.read()
            else:
                s3_object = S3_SESSION.Object(
                    settings.AWS_STORAGE_BUCKET_NAME, "mock_committee_data.json"
                )
                file = s3_object.get()["Body"]
                committee_data = file.read()
            redis_instance.set(settings.COMMITTEE_DATA_REDIS_KEY, committee_data)

            self.stdout.write(self.style.SUCCESS("Successfully loaded committees"))
