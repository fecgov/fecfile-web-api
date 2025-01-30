from django.test import TestCase, override_settings
from ..tasks import get_celery_status, check_database_running
from ..utils.redis_utils import (
	get_redis_value,
	refresh_cache,
	redis_instance,
)
import json


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
class SystemStatusViewTest(TestCase):
    def test_get_celery_status(self):
        status = get_celery_status()
        self.assertTrue(status.get("celery_is_running"))

    def test_check_database_running(self):
        status = check_database_running()
        self.assertTrue(status.get("database_is_running"))

    def test_get_redis_value(self):
        key, value = "test_key", {"test": "value"}
        redis_instance.set(key, json.dumps(value))
        self.assertEqual(get_redis_value(key), value)
        redis_instance.delete(key)
        self.assertIsNone(get_redis_value(key))

    def test_update_status_cache(self):
        key, value = "test_key", "test_value"
        self.assertIsNone(get_redis_value(key))
        refresh_cache(key, lambda: value)
        self.assertEqual(get_redis_value(key), value)
        redis_instance.delete(key)
        self.assertIsNone(get_redis_value(key))
