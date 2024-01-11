from .base import *  # NOSONAR # noqa F401, F403

# These settings are for local development only.

LOGGER_PROCESSORS = get_local_logger_processors()  # noqa

# To test json locally,
# Set LOGGER_PROCESSORS to get_prod_logger_processors() above

structlog.configure(  # noqa
    processors=LOGGER_PROCESSORS,
    logger_factory=structlog.stdlib.LoggerFactory(),  # noqa
    cache_logger_on_first_use=True,
)

# E2E Testing Login API
E2E_TESTING_LOGIN = True

try:
    from .local import *  # NOSONAR # noqa F401, F403
except ImportError:
    pass
