from .base import *  # NOSONAR # noqa: F401, F403

# These settings are for local development only.

CSRF_TRUSTED_ORIGINS.append("http://localhost:4200")  # NOSONAR # noqa: F405

try:
    from .local import *  # NOSONAR # noqa: F401, F403
except ImportError:
    pass
