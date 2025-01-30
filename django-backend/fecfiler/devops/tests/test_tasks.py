from unittest.mock import MagicMock, patch
from ..tasks import (
    get_database_connections,
    get_database_size,
    log_database_size,
    get_database_status_report,
    INITIAL_DB_SIZE
)
from ..utils.redis_utils import get_redis_value, set_redis_value
from django.test import TestCase


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
        self.assertGreater(get_database_size(), 0)

    def test_log_db_size(self):
        redis_initial_db_size = get_redis_value(INITIAL_DB_SIZE)
        set_redis_value(INITIAL_DB_SIZE, None, None)
        db_size = 10 * 1024**3
        log_database_size(db_size)
        stored_db_size = get_redis_value(INITIAL_DB_SIZE)[0]
        self.assertEqual(stored_db_size, db_size)
        set_redis_value(INITIAL_DB_SIZE, redis_initial_db_size, None)

    def test_get_db_status_report(self):
        redis_initial_db_size = get_redis_value(INITIAL_DB_SIZE)
        set_redis_value(INITIAL_DB_SIZE, None, None)
        get_database_status_report()
        self.assertIsNotNone(get_redis_value(INITIAL_DB_SIZE))
        set_redis_value(INITIAL_DB_SIZE, redis_initial_db_size, None)
