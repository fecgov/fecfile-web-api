from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from ..tasks import (
    get_database_connections,
    check_database_size,
    log_database_size,
    log_s3_bucket_size,
    get_devops_status_report,
    delete_expired_s3_objects,
    LOGGED_DB_SIZE_REDIS_KEY,
    LOGGED_S3_SIZE_REDIS_KEY,
)
from ..utils.redis_utils import get_redis_value, set_redis_value
from django.test import TestCase
from django.utils import timezone
from fecfiler.settings import (
    S3_OBJECTS_MAX_AGE_DAYS,
)


class DevopsTasksTestCase(TestCase):
    @patch("fecfiler.devops.tasks.connection")
    @patch("fecfiler.devops.tasks.logger")
    def test_get_database_connections(self, mock_logger, mock_connection):
        # Mock database cursor and query results
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Define mock results from the database query
        mock_cursor.fetchall.return_value = [
            ("10", "5", "100", "10.00"),
        ]

        # Call the task
        connection_results = get_database_connections()

        # Verify that the SQL query was executed
        mock_cursor.execute.assert_called_once()
        executed_sql = mock_cursor.execute.call_args[0][0]
        self.assertIn("SELECT", executed_sql)
        self.assertIn("pg_stat_activity", executed_sql)
        self.assertIn("pg_settings", executed_sql)

        # Verify the processed results
        expected_results_dict = {
            "results": {
                "total_connections": "10",
                "non_idle_connections": "5",
                "max_connections": "100",
                "connections_utilization_pctg": "10.00",
            }
        }
        self.assertEqual(connection_results, expected_results_dict)

    def test_get_db_size(self):
        self.assertGreater(check_database_size(), 0)

    def test_log_db_size(self):
        redis_initial_db_size = get_redis_value(LOGGED_DB_SIZE_REDIS_KEY)
        set_redis_value(LOGGED_DB_SIZE_REDIS_KEY, None, None)

        ten_gb = 10 * 1024**3
        results = log_database_size(ten_gb)
        self.assertEqual(results["database"]["current_size_gb"], 10.0)

        stored_db_size = get_redis_value(LOGGED_DB_SIZE_REDIS_KEY)[0]
        self.assertEqual(stored_db_size, ten_gb)

        timestamp = datetime.now() - timedelta(days=10)
        set_redis_value(
            LOGGED_DB_SIZE_REDIS_KEY,
            [2 * 1024**3, timestamp.strftime("%Y%m%d%H%M%S")],
            None,
        )

        later_results = log_database_size(ten_gb)
        self.assertIsNotNone(later_results["database"]["growth"])
        self.assertIsNotNone(later_results["database"]["est_days_to_full"])

        set_redis_value(LOGGED_DB_SIZE_REDIS_KEY, redis_initial_db_size, None)

    @patch("fecfiler.devops.tasks.S3_SESSION")
    def test_get_db_status_report(self, mock_s3_session):
        redis_initial_db_size = get_redis_value(LOGGED_DB_SIZE_REDIS_KEY)
        set_redis_value(LOGGED_DB_SIZE_REDIS_KEY, None, None)
        get_devops_status_report()
        self.assertIsNotNone(get_redis_value(LOGGED_DB_SIZE_REDIS_KEY))
        set_redis_value(LOGGED_DB_SIZE_REDIS_KEY, redis_initial_db_size, None)

    @patch("fecfiler.devops.tasks.S3_SESSION")
    def test_delete_expired_s3_objects(self, mock_s3_session):
        test_s3_object_1 = {"key": "test_key_1", "last_modified": timezone.now()}
        test_s3_object_2 = {
            "key": "test_key_2",
            "last_modified": timezone.now()
            - timedelta(days=(S3_OBJECTS_MAX_AGE_DAYS + 10)),
        }
        test_s3_objects = [test_s3_object_1, test_s3_object_2]
        mock_s3_session.Bucket.return_value.objects.all.return_value = test_s3_objects

        delete_expired_s3_objects()
        mock_s3_session.Bucket.return_value.delete_objects.assert_called_once()

        # Remove object that would have been deleted in S3 and test again
        # to confirm no more should be deleted
        test_s3_objects = [test_s3_object_1]
        mock_s3_session.Bucket.return_value.objects.all.return_value = test_s3_objects
        delete_expired_s3_objects()
        mock_s3_session.Bucket.return_value.delete_objects.assert_called_once()

    @patch("fecfiler.devops.tasks.S3_SESSION")
    def test_log_s3_bucket_size(self, mock_s3_session):
        redis_initial_s3_size = get_redis_value(LOGGED_S3_SIZE_REDIS_KEY)
        set_redis_value(LOGGED_S3_SIZE_REDIS_KEY, None, None)

        results = log_s3_bucket_size()
        self.assertGreaterEqual(results["s3_bucket"]["current_size_gb"], 0)

        stored_db_size = get_redis_value(LOGGED_S3_SIZE_REDIS_KEY)[0]
        self.assertGreaterEqual(stored_db_size, 0)

        timestamp = datetime.now() - timedelta(days=10)
        set_redis_value(
            LOGGED_S3_SIZE_REDIS_KEY,
            [100, timestamp.strftime("%Y%m%d%H%M%S")],
            None,
        )

        later_results = log_s3_bucket_size()
        self.assertIsNotNone(later_results["s3_bucket"]["growth"])

        set_redis_value(LOGGED_S3_SIZE_REDIS_KEY, redis_initial_s3_size, None)
