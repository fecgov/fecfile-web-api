from .base import *  # NOSONAR # noqa: F401, F403
from corsheaders.defaults import default_headers

# These settings are for local development only.

INSTALLED_APPS.append("corsheaders")  # NOSONAR # noqa: F405
MIDDLEWARE.append("corsheaders.middleware.CorsMiddleware")  # NOSONAR # noqa: F405

CORS_ALLOWED_ORIGIN_REGEXES = ["http://localhost:4200"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:4200"]

CORS_ALLOW_HEADERS = (
    *default_headers,
    "enctype",
    "token",
    "cache-control",
)

CORS_ALLOW_CREDENTIALS = True

try:
    from .local import *  # NOSONAR # noqa: F401, F403
except ImportError:
    pass
