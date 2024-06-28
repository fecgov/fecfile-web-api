from .base import *  # NOSONAR # noqa: F401, F403

# These settings are for local development only.

CORS_ALLOWED_ORIGIN_REGEXES.append("http://localhost:4200")  # NOSONAR # noqa: F405

try:
    from .local import *  # NOSONAR # noqa: F401, F403
except ImportError:
    pass
