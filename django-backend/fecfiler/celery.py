from enum import Enum
import os
import ssl
import cfenv
import logging
import structlog
from django.conf import settings
from celery import Celery
from celery.signals import setup_logging
from django_structlog.celery.steps import DjangoStructLogInitStep

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fecfiler.settings")

app = Celery("fecfiler")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# A step to initialize django-structlog
app.steps['worker'].add(DjangoStructLogInitStep)

env = cfenv.AppEnv()


@setup_logging.connect
def receiver_setup_logging(loglevel, logfile, format, colorize, **kwargs):
    """
    Celery and environment-specific logging
    See https://django-structlog.readthedocs.io/en/latest/celery.html
    """
    if env.space is not None:  # Running in prod
        loggers = settings.PROD_LOGGERS
        logger_processors = settings.get_prod_logger_processors
    else:
        loggers = settings.LOCAL_LOGGERS
        logger_processors = settings.get_local_logger_processors

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json_formatter": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(),
                },
                "plain_console": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(),
                },
                "key_value": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.KeyValueRenderer(
                        key_order=['timestamp', 'level', 'event', 'logger']
                    ),
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "plain_console",
                },
                "json_file": {
                    "class": "logging.handlers.WatchedFileHandler",
                    "filename": "logs/json.log",
                    "formatter": "json_formatter",
                },
                "flat_line_file": {
                    "class": "logging.handlers.WatchedFileHandler",
                    "filename": "logs/flat_line.log",
                    "formatter": "key_value",
                },
            },
            "loggers": loggers
        }
    )

    structlog.configure(  # noqa
        processors=logger_processors(),
        logger_factory=structlog.stdlib.LoggerFactory(),  # noqa
        cache_logger_on_first_use=True,
    )


if env.get_service(name="fecfile-api-redis"):
    app.conf["broker_use_ssl"] = {"ssl_cert_reqs": ssl.CERT_NONE}
    app.conf["redis_backend_use_ssl"] = {"ssl_cert_reqs": ssl.CERT_NONE}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


class CeleryStorageType(Enum):
    AWS = "aws"
    LOCAL = "local"


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
