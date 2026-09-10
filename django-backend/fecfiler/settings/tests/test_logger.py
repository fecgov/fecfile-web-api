import logging.config
from django.test import TestCase
from django.core.exceptions import ValidationError
import logging
from fecfiler import settings
import structlog
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr


class LoggerTestCase(TestCase):

    # Local

    def test_info_logging_local(self):
        buffer = StringIO()
        with redirect_stdout(buffer):
            logging.config.dictConfig(settings.get_logging_config("LINE"))
            logger = structlog.get_logger()
            logger.info("Test info log message")
            output = buffer.getvalue()
            self.assertIn("Test info log message", output)

    def test_exception_logging_local(self):
        buffer = StringIO()
        with redirect_stderr(buffer):
            logging.config.dictConfig(settings.get_logging_config("LINE"))
            logger = structlog.get_logger()
            try:
                raise ValidationError("Test exception")
            except ValidationError as e:
                logger.exception(e)
                output = buffer.getvalue()
            self.assertIn("Test exception", output)

    # Cloud

    def test_info_logging_cloud(self):
        buffer = StringIO()
        with redirect_stdout(buffer):
            logging.config.dictConfig(settings.get_logging_config("NOT_LINE"))
            logger = structlog.get_logger()
            logger.info("Test info log message")
            output = buffer.getvalue()
            self.assertIn("Test info log message", output)

    def test_exception_logging_cloud(self):
        buffer = StringIO()
        with redirect_stderr(buffer):
            logging.config.dictConfig(settings.get_logging_config("NOT_LINE"))
            logger = structlog.get_logger()
            try:
                raise ValidationError("Test exception1")
            except ValidationError as e:
                try:
                    raise ValidationError("Test exception2") from e
                except ValidationError as e2:
                    logger.exception(e2)
            output = buffer.getvalue()
            self.assertIn("Test exception1", output)
            self.assertIn("Test exception2", output)
