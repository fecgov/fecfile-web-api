from enum import Enum
import os
import ssl

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fecfiler.settings")

app = Celery("fecfiler")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")
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
