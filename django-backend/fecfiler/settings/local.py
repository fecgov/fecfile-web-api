from .base import *  # NOSONAR # noqa F401, F403

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

# E2E Testing Login API
E2E_TESTING_LOGIN = True

MIDDLEWARE.append(
    "django_cprofile_middleware.middleware.ProfilerMiddleware"
)
DJANGO_CPROFILE_MIDDLEWARE_REQUIRE_STAFF = False

try:
    from .local import *  # NOSONAR # noqa F401, F403
except ImportError:
    pass
