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
    logger.info("DANTEST: Worker shutting down, cleaning up in-flight tasks")
    logger.info(f"     Signal: {signal}, Sender: {sender}, KWArgs: {kwargs}")

    if running_tasks:
        logger.warning(
            "DANTEST: Worker shutdown with in-process running tasks", tasks=running_tasks
        )
        for task_id, task in running_tasks.items():
            fail_running_task(task)
        return

    # Fallback: try to inspect the worker's active tasks via the broker.
    try:
        inspector = current_app.control.inspect()
        active_tasks = inspector.active() or {}
        logger.info("DANTEST: Active tasks from inspector", active_tasks=active_tasks)
        for task_list in active_tasks.values():
            for task in task_list:
                fail_running_task(task)

    except Exception as exc:  # pragma: no cover - broker/network failures
        logger.exception(
            "DANTEST: Failed to inspect active tasks during shutdown", exc=exc
        )


def fail_running_task(task: dict):
    """Handles a task that was running when the worker was shut down"""
    #    from fecfiler.web_services.models import UploadSubmission, WebPrintSubmission
    #    from fecfiler.web_services.tasks import (
    #        SUBMISSION_CLASSES,
    #        Task,
    #        create_dot_fec,
    #        submit_to_fec,
    #        submit_to_webprint,
    #        poll_for_fec_response,
    #    )

    try:
        task_name = task.get("name")
        logger.info(f"DANTEST: Handling running task: {task_name}")
    #        if task_name == create_dot_fec.name:
    #            fail_create_dot_fec(task)
    #        elif task_name == submit_to_fec.name:
    #            fail_submit_to_fec(task)
    #        elif task_name == submit_to_webprint.name:
    #            fail_submit_to_webprint(task)
    #        elif task_name == poll_for_fec_response.name:
    #            fail_poll_for_fec_response(task)
    except Exception:
        id = task.get("id")
        logger.exception(f"Failed to handle running task: {id}")


# def fail_create_dot_fec(task: dict):
#    """Handles create_dot_fec task"""
#    upload_submission_id = task.get("kwargs", {}).get("upload_submission_id")
#    if upload_submission_id:
#        fail_submission(upload_submission_id, UploadSubmission)

#    webprint_submission_id = task.get("kwargs", {}).get("webprint_submission_id")
#    if webprint_submission_id:
#        fail_submission(webprint_submission_id, WebPrintSubmission)


# def fail_submit_to_fec(task: dict):
#    """Handles submit_to_fec task"""
#    submission_id = task.get("args")[1]
#    fail_submission(submission_id, UploadSubmission)


# def fail_submit_to_webprint(task: dict):
#    """Handles submit_to_webprint task"""
#    submission_id = task.get("args")[1]
#    fail_submission(submission_id, WebPrintSubmission)


# def fail_poll_for_fec_response(task: dict):
#    """Handles poll_for_fec_response task"""
#    submission_id = task.get("args")[0]
#    submission_type_key = task.get("args")[1]
#    SubmissionClass = SUBMISSION_CLASSES[submission_type_key]
#    fail_submission(submission_id, SubmissionClass)


# def fail_submission(submission_id: str, SubmissionClass: Task):
#    """Marks a submission as failed"""
#    submission = SubmissionClass.objects.get(id=submission_id)
#    submission.save_error("Celery worker shutting down")
#    logger.info(f"Report {submission_id} marked as failed")


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
