from .base import *  # NOSONAR # noqa F401, F403

# These settings are used for all public environments:
# dev, stage and production

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = False

LOGGING['loggers'].update(PROD_LOGGERS)

structlog.configure(  # noqa
    processors=get_prod_logger_processors(),  # noqa
    logger_factory=structlog.stdlib.LoggerFactory(),  # noqa
    cache_logger_on_first_use=True,
)

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True

ALLOWED_HOSTS = [".fec.gov", ".app.cloud.gov"]
