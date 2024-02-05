from django.test import TestCase
from structlog import get_logger
from structlog.testing import capture_logs


class LoggingTestCase(TestCase):

    def test_logs(self):
        with capture_logs() as log_capture:
            logging = get_logger(__name__)
            logging.debug('debug logged')
            logging.info('info logged')
            logging.warning('warning logged')
            logging.critical('critical logged')

            assert [
                {'event': 'debug logged', 'log_level': 'debug'},
                {'event': 'info logged', 'log_level': 'info'},
                {'event': 'warning logged', 'log_level': 'warning'},
                {'event': 'critical logged', 'log_level': 'critical'}
            ] == log_capture
