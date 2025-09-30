import os
import ssl
import cfenv
import logging
import structlog
from celery import Celery, current_app
from celery.signals import setup_logging, worker_shutdown, task_prerun, task_postrun
from django_structlog.celery.steps import DjangoStructLogInitStep
from fecfiler import settings

logger = structlog.get_logger(__name__)


# Keep a small in-memory registry of tasks running in this worker process.
# This is reliable for the local worker process and lets us inspect in-flight
# tasks synchronously when the worker_shutdown signal is fired.
running_tasks = {}


@task_prerun.connect
def _task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **_):
    try:
        name = getattr(sender, "name", None) or getattr(task, "name", None) or str(sender)
    except Exception:
        name = str(sender)
    running_tasks[task_id] = {"name": name, "args": args, "kwargs": kwargs}
    logger.debug(
        "DANTEST: Task started", task_id=task_id, task=name, running_tasks=running_tasks
    )


@task_postrun.connect
def _task_postrun(
    sender=None,
    task_id=None,
    task=None,
    args=None,
    kwargs=None,
    retval=None,
    state=None,
    **_,
):
    running_tasks.pop(task_id, None)
    logger.debug(
        "DANTEST: Task finished",
        task_id=task_id,
        task=getattr(sender, "name", str(sender)),
        retval=retval,
        state=state,
        running_tasks=running_tasks,
    )


@worker_shutdown.connect
def on_worker_shutdown(signal, sender, **kwargs):
    """Called when the worker is shutting down.

    Prefer the in-process registry (`running_tasks`) which is updated by
    `task_prerun`/`task_postrun`. As a fallback (for edge cases where the
    registry is empty or not accurate), attempt to query the broker via
    `current_app.control.inspect().active()`.
    """
    logger.info("Worker shutting down, cleaning up in-flight tasks")
    logger.info(f"     Signal: {signal}, Sender: {sender}, KWArgs: {kwargs}")

    if running_tasks:
        logger.warning(
            "Worker shutdown with in-process running tasks", tasks=running_tasks
        )
        # Here you can add any cleanup or task-revocation logic you need.
        return

    # Fallback: try to inspect the worker's active tasks via the broker.
    try:
        inspector = current_app.control.inspect()
        active = inspector.active() or {}
        logger.info("Active tasks from inspector", active=active)
    except Exception as exc:  # pragma: no cover - broker/network failures
        logger.exception("Failed to inspect active tasks during shutdown", exc=exc)


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
    log_format = settings.LOG_FORMAT

    logging.config.dictConfig(settings.get_logging_config(log_format))

    structlog.configure(
        processors=settings.get_logging_processors(),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logger.info("Starting Celery: logging set up")


logger.info("Starting Celery")

if env.get_service(name="fecfile-api-redis"):
    app.conf["broker_use_ssl"] = {"ssl_cert_reqs": ssl.CERT_NONE}
    app.conf["redis_backend_use_ssl"] = {"ssl_cert_reqs": ssl.CERT_NONE}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
