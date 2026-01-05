from .base import *  # NOSONAR # noqa: F401, F403

# These settings are for local development only.

CORS_ALLOWED_ORIGIN_REGEXES.append("http://localhost:4200")  # NOSONAR # noqa: F405
CSRF_TRUSTED_ORIGINS.append("http://localhost:4200")  # NOSONAR # noqa: F405
CORS_ALLOW_HEADERS = (
    *CORS_ALLOW_HEADERS,  # NOSONAR # noqa: F405
    "x-test-source",
    "x-test-run-id",
    "x-test-title",
    "x-test-spec",
)

try:
    from .local import *  # NOSONAR # noqa: F401, F403
except ImportError:
    pass
