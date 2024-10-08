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

logger = structlog.get_logger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fecfiler.settings")

app = Celery("fecfiler")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# A step to initialize django-structlog
app.steps["worker"].add(DjangoStructLogInitStep)

env = cfenv.AppEnv()


@setup_logging.connect
def receiver_setup_logging(loglevel, logfile, format, colorize, **kwargs):
    """
    Celery and environment-specific logging
    See https://django-structlog.readthedocs.io/en/latest/celery.html
    """
    log_format = env.get_credential("LOG_FORMAT")

    logging.config.dictConfig(settings.get_logging_config(log_format))

    structlog.configure(
        processors=settings.get_logging_processors(),
        logger_factory=structlog.stdlib.LoggerFactory(),
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
    logger.debug(f"Request: {self.request!r}")
    return True
