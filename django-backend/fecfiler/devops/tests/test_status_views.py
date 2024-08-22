from django.test import TestCase, override_settings
from fecfiler.devops.views import (
    get_celery_status,
    get_database_status,
    get_redis_value,
    redis_instance,
)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
class SystemStatusViewTest(TestCase):
    def test_get_celery_status(self):
        status = get_celery_status()
        self.assertTrue(status.get("celery_is_running"))

    def test_get_database_satus(self):
        status = get_database_status()
        self.assertTrue(status.get("database_is_running"))

    def get_redis_value(self):
        key, value = "test_key", "test_value"
        redis_instance.set(key, value)
        self.assertEqual(get_redis_value(key), value)
        redis_instance.delete(key)
        self.assertIsNone(get_redis_value(key))
