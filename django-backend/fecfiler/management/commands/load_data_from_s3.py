from django.core.management.base import BaseCommand
from fecfiler.settings import BASE_DIR, AWS_STORAGE_BUCKET_NAME
from django.core.management import call_command
from fecfiler.s3 import S3_SESSION
import os


class Command(BaseCommand):
    help = "Download django fixture from s3 and run `load_data` on it"

    def add_arguments(self, parser):
        parser.add_argument("filename", required=True)

    def handle(self, *args, **options):
        filename = options["filename"]

        """Download file from s3"""
        file_path = os.path.join(BASE_DIR, filename)
        S3_SESSION.Bucket(AWS_STORAGE_BUCKET_NAME).download_file(filename, file_path)

        """Run load_data on file"""
        call_command("load_data", filename)
