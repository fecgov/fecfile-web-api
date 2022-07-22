from .base import *  # NOSONAR # noqa F401, F403

# These settings are for local development only.

CELERY_WORKER_STORAGE = CELERY_STORAGE_TYPE.LOCAL

try:
    from .local import *  # NOSONAR # noqa F401, F403
except ImportError:
    pass
