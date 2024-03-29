from .base import *  # NOSONAR # noqa: F401, F403
import os

# These settings are for local development only.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {"handlers": ["default"], "level": "DEBUG", "propagate": True},
    },
}

os.environ["DB_DOCKERFILE"] = "Dockerfile-e2e"

try:
    from .local import *  # NOSONAR # noqa: F401, F403
except ImportError:
    pass
