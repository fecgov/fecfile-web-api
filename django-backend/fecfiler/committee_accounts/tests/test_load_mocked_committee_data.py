from django.test import TestCase
from django.core.management import call_command
from fecfiler.settings import MOCK_OPENFEC_REDIS_URL
import redis
import json
from fecfiler.committee_accounts.utils.accounts import COMMITTEE_DATA_REDIS_KEY


class LoadTestMockedDataCommandTest(TestCase):
    def test_load_test_data(self):
        call_command("load_mocked_committee_data")
        redis_instance = redis.Redis.from_url(MOCK_OPENFEC_REDIS_URL)
        committee_data = redis_instance.get(COMMITTEE_DATA_REDIS_KEY)
        self.assertEqual(len(json.loads(committee_data)), 3)
