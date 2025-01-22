from unittest.mock import MagicMock, patch
from .tasks import get_database_connections
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
        get_database_connections()

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
        mock_logger.info.assert_called_once_with(expected_results_dict)
