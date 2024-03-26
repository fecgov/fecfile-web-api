from django.test import TestCase
from django.core.management import call_command
from fecfiler.settings import MOCK_OPENFEC_REDIS_URL
import redis
import json
from fecfiler.mock_openfec.mock_endpoints import COMMITTEE_DETAILS_REDIS_KEY


class LoadTestDataCommandTest(TestCase):

    def test_load_test_details(self):
        call_command("load_committee_details")
        redis_instance = redis.Redis.from_url(MOCK_OPENFEC_REDIS_URL)
        committee_details = redis_instance.get(COMMITTEE_DETAILS_REDIS_KEY)
        self.assertGreaterEqual(len(json.loads(committee_details)), 1)
