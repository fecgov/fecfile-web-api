from django.core.management.base import BaseCommand
from fecfiler.settings import MOCK_OPENFEC_REDIS_URL, BASE_DIR, AWS_STORAGE_BUCKET_NAME
import redis
import os
from fecfiler.s3 import S3_SESSION
from fecfiler.mock_openfec.mock_endpoints import COMMITTEE_DATA_REDIS_KEY


class Command(BaseCommand):
    help = "Load mock committee data into redis"

    def add_arguments(self, parser):
        parser.add_argument("--s3", action="store_true")

    def handle(self, *args, **options):
        if MOCK_OPENFEC_REDIS_URL:
            redis_instance = redis.Redis.from_url(MOCK_OPENFEC_REDIS_URL)
            if not options.get("s3"):
                path = os.path.join(
                    BASE_DIR, "mock_openfec/management/commands/committee_data.json"
                )
                with open(path) as file:
                    committee_data = file.read()
            else:
                s3_object = S3_SESSION.Object(
                    AWS_STORAGE_BUCKET_NAME, "mock_committee_data.json"
                )
                file = s3_object.get()["Body"]
                committee_data = file.read()
            redis_instance.set(COMMITTEE_DATA_REDIS_KEY, committee_data)

            self.stdout.write(self.style.SUCCESS("Successfully loaded committees"))
