from pathlib import Path
from django.test import TestCase
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.scha_transactions.models import SchATransaction
from fecfiler.web_services.web_service_storage import (
    store_file,
    get_file,
    get_file_bytes,
)
from fecfiler.settings import CELERY_LOCAL_STORAGE_DIRECTORY


class WebServiceStorageTestCase(TestCase):
    def test_store_file(self):
        store_file("Store Test Content", "store_test.txt", True)
        path = Path(CELERY_LOCAL_STORAGE_DIRECTORY) / "store_test.txt"
        self.assertTrue(path.exists())

    def test_get_file(self):
        store_file("Get Test Content", "get_test.txt", True)
        with get_file("get_test.txt", True) as file:
            file_bytes = bytearray(file.read())
            self.assertEqual(b"Get Test Content", file_bytes)

    def test_get_file_bytes(self):
        store_file("Test Content", "test.txt", True)
        file_bytes = get_file_bytes("test.txt", True)
        self.assertEqual(b"Test Content", file_bytes)
