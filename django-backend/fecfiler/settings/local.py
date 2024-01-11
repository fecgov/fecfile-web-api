from .base import *  # NOSONAR # noqa F401, F403

# These settings are for local development only.

structlog.configure(  # noqa
    processors=get_env_logging_processors(), # noqa
    logger_factory=structlog.stdlib.LoggerFactory(),  # noqa
    cache_logger_on_first_use=True,
)


try:
    from .local import *  # NOSONAR # noqa F401, F403
except ImportError:
    pass
