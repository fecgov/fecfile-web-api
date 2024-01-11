from .base import *  # NOSONAR # noqa F401, F403

# These settings are for local development only.

DEBUG = True

structlog.configure(  # noqa
    processors=get_local_logger_processors(), # noqa
    logger_factory=structlog.stdlib.LoggerFactory(),  # noqa
    cache_logger_on_first_use=True,
)

# Uncomment to test json logs locally
# structlog.configure(  # noqa
#     processors=get_prod_logger_processors(),
#     logger_factory=structlog.stdlib.LoggerFactory(),  # noqa
#     cache_logger_on_first_use=True,
# )

# E2E Testing Login API
E2E_TESTING_LOGIN = True

try:
    from .local import *  # NOSONAR # noqa F401, F403
except ImportError:
    pass
