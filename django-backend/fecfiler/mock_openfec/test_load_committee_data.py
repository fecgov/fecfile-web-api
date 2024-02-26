from django.test import TestCase
from django.core.management import call_command
from fecfiler.settings import MOCK_OPENFEC_REDIS_URL, MOCK_OPENFEC
import redis
from fecfiler.mock_openfec.mock_endpoints import COMMITTEE_DATA_REDIS_KEY


class LoadTestDataCommandTest(TestCase):

    def setUp(self):
        pass

    def test_load_test_data(self):
        call_command("load_committee_data")
        print(f"MOCK_OPENFEC {MOCK_OPENFEC}")
        redis_instance = redis.Redis.from_url(MOCK_OPENFEC_REDIS_URL)
        committee_data = redis_instance.get(COMMITTEE_DATA_REDIS_KEY)
        self.assertEqual(len(committee_data), 1)
