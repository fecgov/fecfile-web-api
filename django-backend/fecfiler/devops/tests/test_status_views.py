from django.test import TestCase, override_settings
from ..tasks import (
    check_database_running,
    get_devops_status_report,
    CELERY_STATUS,
    SCHEDULER_STATUS
)
from ..utils.redis_utils import (
    get_redis_value,
    set_redis_value,
    redis_instance,
)
import json


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
class SystemStatusViewTest(TestCase):
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
        set_redis_value(key, value, age=None)
        self.assertEqual(get_redis_value(key), value)
        redis_instance.delete(key)
        self.assertIsNone(get_redis_value(key))

    def test_status_report(self):
        self.assertIsNone(get_redis_value(CELERY_STATUS))
        self.assertIsNone(get_redis_value(SCHEDULER_STATUS))
        get_devops_status_report()
        self.assertIsNotNone(get_redis_value(CELERY_STATUS))
        self.assertIsNotNone(get_redis_value(SCHEDULER_STATUS))

