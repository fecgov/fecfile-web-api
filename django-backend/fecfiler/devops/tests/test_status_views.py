from unittest.mock import patch
from django.test import TestCase, override_settings
from fecfiler.devops.views import (
    get_celery_status,
    get_database_status,
    get_redis_value,
    get_scheduler_status,
    update_status_cache,
    redis_instance,
)
import json


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
class SystemStatusViewTest(TestCase):
    def test_get_celery_status(self):
        status = get_celery_status()
        self.assertTrue(status.get("celery_is_running"))

    @patch("fecfiler.devops.views.redis_instance.get")
    def test_get_scheduler_status(self, mock_redis_get):
        mock_redis_get.return_value = "some_value"
        status = get_scheduler_status()
        self.assertTrue(status.get("scheduler_is_running"))

        mock_redis_get.assert_called_once_with("scheduler_status")

    def test_get_database_satus(self):
        status = get_database_status()
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
        update_status_cache(key, lambda: value)
        self.assertEqual(get_redis_value(key), value)
        redis_instance.delete(key)
        self.assertIsNone(get_redis_value(key))
