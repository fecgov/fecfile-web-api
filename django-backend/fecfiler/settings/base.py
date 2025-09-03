"""
Django settings for the FECFile project.
"""

import os
import dj_database_url
import structlog
import logging
import sys

from enum import Enum
from .env import env
from corsheaders.defaults import default_headers
from fecfiler.shared.utilities import get_float_from_string, get_boolean_from_string
from fecfiler.transactions.profilers import TRANSACTION_MANAGER_PROFILING
from math import floor


class CeleryStorageType(Enum):
    AWS = "aws"
    LOCAL = "local"


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", True)
TEMPLATE_DEBUG = DEBUG

LINE = "LINE"
KEY_VALUE = "KEY_VALUE"

APPEND_SLASH = False

LOG_FORMAT = env.get_credential("LOG_FORMAT", LINE)
# SECURITY WARNING: for local logging only - do not enable in any cloud.gov environments!
# Django DEBUG base.py setting must also be set to True to see SQL output
ENABLE_PL_SQL_LOGGING = get_boolean_from_string(
    env.get_credential("ENABLE_PL_SQL_LOGGING", "False")
)

CSRF_COOKIE_DOMAIN = env.get_credential("FFAPI_COOKIE_DOMAIN")
CSRF_TRUSTED_ORIGINS = ["https://*.app.cloud.gov"]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.get_credential("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise Exception("DJANGO_SECRET_KEY is not set!")
SECRET_KEY_FALLBACKS = env.get_credential("DJANGO_SECRET_KEY_FALLBACKS", [])


ROOT_URLCONF = "fecfiler.urls"
WSGI_APPLICATION = "fecfiler.wsgi.application"
AUTH_USER_MODEL = "user.User"

ALLOWED_HOSTS = ["*"]


# Application definition

SESSION_COOKIE_AGE = int(
    env.get_credential("SESSION_COOKIE_AGE", str(30 * 60))  # Inactivity timeout
)
SESSION_SAVE_EVERY_REQUEST = True


INCLUDE_SILK = get_boolean_from_string(env.get_credential("INCLUDE_SILK", "False"))
INSTALLED_APPS = [
    # "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "django_structlog",
    "django_migration_linter",
    "fecfiler.committee_accounts",
    "fecfiler.reports",
    "fecfiler.transactions",
    "fecfiler.memo_text",
    "fecfiler.contacts",
    "fecfiler.soft_delete",
    "fecfiler.validation",
    "fecfiler.web_services",
    "fecfiler.user",
    "fecfiler.oidc",
    "fecfiler.devops",
    "fecfiler.mock_oidc_provider",
    "fecfiler.cash_on_hand",
    "fecfiler.openapi",
]

MIDDLEWARE = []


if INCLUDE_SILK:
    STATIC_URL = "/static/"
    STATICFILES_DIRS = (os.path.join(BASE_DIR, "staticfiles"),)
    STATIC_ROOT = "static"

    INSTALLED_APPS += [
        "silk",
        "django.contrib.staticfiles",
    ]
    MIDDLEWARE = ["silk.middleware.SilkyMiddleware"]
    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/1.11/howto/static-files/

    SILKY_PYTHON_PROFILER = True
    SILKY_PYTHON_PROFILER_BINARY = True

    # the sub-directories of media and static files
    STATICFILES_LOCATION = "static"
    SILKY_DYNAMIC_PROFILING = TRANSACTION_MANAGER_PROFILING


MIDDLEWARE += [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "fecfiler.middleware.HeaderMiddleware",
    "fecfiler.oidc.middleware.TimeoutMiddleware.TimeoutMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "fecfiler.middleware.StructlogContextMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["fecfiler/openapi/templates", "static/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

CORS_ALLOWED_ORIGIN_REGEXES = [r"https://(.*?)fecfile\.fec\.gov$"]

CORS_ALLOW_HEADERS = (
    *default_headers,
    "enctype",
    "token",
    "cache-control",
)

CORS_ALLOW_CREDENTIALS = True


# Database
DATABASES = {
    # Be sure to set the DATABASE_URL environment variable on your local
    # development machine so that the local database can be connected to.
    "default": dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Connection string for connecting directly
DATABASE_URL = os.environ.get("DATABASE_URL")

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
MIGRATION_LINTER_OVERRIDE_MAKEMIGRATIONS = True

FECFILE_GITHUB_TOKEN = env.get_credential("FECFILE_GITHUB_TOKEN")

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "fecfiler.oidc.backends.OIDCAuthenticationBackend",
]

# Maximum number of concurrent sessions
OIDC_MAX_STATES = 3

OIDC_RP_SIGN_ALGO = "RS256"
OIDC_RP_CLIENT_ID = env.get_credential("OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET_STAGING = env.get_credential("OIDC_RP_CLIENT_SECRET_STAGING")
OIDC_RP_CLIENT_SECRET = env.get_credential("OIDC_RP_CLIENT_SECRET")
OIDC_RP_CLIENT_SECRET_BACKUP = env.get_credential("OIDC_RP_CLIENT_SECRET_BACKUP")

# The Django field used to identify users - default is email
OIDC_RP_UNIQUE_IDENTIFIER = "username"

# Sometimes the OP (IDP - login.gov)has a different label for the unique ID
OIDC_OP_UNIQUE_IDENTIFIER = "sub"

OIDC_OP_AUTODISCOVER_ENDPOINT = env.get_credential(
    "OIDC_OP_AUTODISCOVER_ENDPOINT",
)
if not OIDC_OP_AUTODISCOVER_ENDPOINT:
    raise Exception("OIDC_OP_AUTODISCOVER_ENDPOINT is not set!")

MOCK_OIDC_PROVIDER = get_boolean_from_string(
    env.get_credential("MOCK_OIDC_PROVIDER", "False")
)
MOCK_OIDC_PROVIDER_CACHE = env.get_credential("REDIS_URL")

OIDC_ACR_VALUES = "http://idmanagement.gov/ns/assurance/ial/1"

FFAPI_COOKIE_DOMAIN = env.get_credential("FFAPI_COOKIE_DOMAIN")
FFAPI_LOGIN_DOT_GOV_COOKIE_NAME = "ffapi_login_dot_gov"
FFAPI_TIMEOUT_COOKIE_NAME = env.get_credential("FFAPI_TIMEOUT_COOKIE_NAME", "False")
if not FFAPI_TIMEOUT_COOKIE_NAME:
    raise Exception("FFAPI_TIMEOUT_COOKIE_NAME is not set!")


LOGIN_REDIRECT_URL = env.get_credential("LOGIN_REDIRECT_SERVER_URL")
LOGIN_REDIRECT_CLIENT_URL = env.get_credential("LOGIN_REDIRECT_CLIENT_URL")
LOGOUT_REDIRECT_URL = env.get_credential("LOGOUT_REDIRECT_URL")

# keygen settings
LOGIN_DOT_GOV_RSA_PK_SIZE = int(env.get_credential("LOGIN_DOT_GOV_RSA_PK_SIZE", "2048"))
LOGIN_DOT_GOV_X509_DAYS_VALID = float(
    env.get_credential("LOGIN_DOT_GOV_X509_DAYS_VALID", "365")
)
LOGIN_DOT_GOV_X509_COUNTRY = env.get_credential("LOGIN_DOT_GOV_X509_COUNTRY")
LOGIN_DOT_GOV_X509_STATE = env.get_credential("LOGIN_DOT_GOV_X509_STATE")
LOGIN_DOT_GOV_X509_LOCALITY = env.get_credential("LOGIN_DOT_GOV_X509_LOCALITY")
LOGIN_DOT_GOV_X509_ORG = env.get_credential("LOGIN_DOT_GOV_X509_ORG")
LOGIN_DOT_GOV_X509_ORG_UNIT = env.get_credential("LOGIN_DOT_GOV_X509_ORG_UNIT")
LOGIN_DOT_GOV_X509_COMMON_NAME = env.get_credential("LOGIN_DOT_GOV_X509_COMMON_NAME")
LOGIN_DOT_GOV_X509_EMAIL_ADDRESS = env.get_credential("LOGIN_DOT_GOV_X509_EMAIL_ADDRESS")

USE_X_FORWARDED_HOST = True

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"

USE_I18N = True
USE_L10N = True
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "EXCEPTION_HANDLER": "fecfiler.utils.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "SERVE_INCLUDE_SCHEMA": False,
}


class NotErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < logging.ERROR


def get_logging_config(log_format=LINE):
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.dict_tracebacks,
                    structlog.processors.JSONRenderer(),
                ],
            },
            "plain_console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.dict_tracebacks,
                    structlog.dev.ConsoleRenderer(
                        colors=True, exception_formatter=structlog.dev.rich_traceback
                    ),
                ],
                "foreign_pre_chain": [
                    structlog.contextvars.merge_contextvars,
                ],
            },
            "key_value": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.dict_tracebacks,
                    structlog.processors.ExceptionRenderer(),
                    structlog.processors.KeyValueRenderer(
                        key_order=["level", "event", "logger"]
                    ),
                ],
                "foreign_pre_chain": [
                    structlog.contextvars.merge_contextvars,
                ],
            },
        },
        "filters": {
            "not_error": {
                "()": NotErrorFilter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "plain_console",
                "stream": sys.stdout,
                "filters": ["not_error"],
            },
            "console_error": {
                "level": "ERROR",
                "class": "logging.StreamHandler",
                "formatter": "plain_console",
                "stream": sys.stderr,
            },
            "cloud": {
                "class": "logging.StreamHandler",
                "formatter": "key_value",
                "stream": sys.stdout,
                "filters": ["not_error"],
            },
            "cloud_error": {
                "level": "ERROR",
                "class": "logging.StreamHandler",
                "formatter": "key_value",
                "stream": sys.stderr,
            },
        },
    }

    if log_format == LINE:
        logging_config["loggers"] = {
            "django_structlog": {
                "handlers": ["console", "console_error"],
                "level": "DEBUG",
            },
            "fecfiler": {
                "handlers": ["console", "console_error"],
                "level": "DEBUG",
            },
        }
        if ENABLE_PL_SQL_LOGGING is True:
            logging_config["loggers"]["django.db.backends"] = {
                "handlers": ["console"],
                "level": "DEBUG",
            }
    else:
        logging_config["loggers"] = {
            "django_structlog": {
                "handlers": ["cloud", "cloud_error"],
                "level": "INFO",
            },
            "fecfiler": {
                "handlers": ["cloud", "cloud_error"],
                "level": "INFO",
            },
        }

    return logging_config


def get_logging_processors():
    """
    get structlog processors
    We will need to set these explicitly for Celery too
    """
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]


LOGGING = get_logging_config(LOG_FORMAT)

structlog.configure(
    processors=get_logging_processors(),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

"""System status settings
"""
SYSTEM_STATUS_CACHE_BACKEND = env.get_credential("REDIS_URL")
SYSTEM_STATUS_CACHE_AGE = env.get_credential("SYSTEM_STATUS_CACHE_AGE", 60)


"""Celery configurations
"""
CELERY_BROKER_URL = env.get_credential("REDIS_URL")
CELERY_RESULT_BACKEND = env.get_credential("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
DJANGO_STRUCTLOG_CELERY_ENABLED = True


CELERY_LOCAL_STORAGE_DIRECTORY = os.path.join(BASE_DIR, "web_services/dot_fec/output")
CELERY_WORKER_STORAGE = env.get_credential("CELERY_WORKER_STORAGE", CeleryStorageType.AWS)

CELERY_BEAT_SCHEDULE = {
    "essential-services-status-check": {
        "task": "fecfiler.devops.tasks.get_devops_status_report",
        "schedule": 30.0,
        "args": (),
        "options": {
            "expires": 15.0,
            "priority": 1,  # 0-9; 0 is the highest priority; 5 is the default
        },
    },
}
if CELERY_WORKER_STORAGE != "local":
    CELERY_BEAT_SCHEDULE["delete_expired_s3_objects"] = {
        "task": "fecfiler.devops.tasks.delete_expired_s3_objects",
        "schedule": 86400.0,  # Once per day
        "args": (),
        "options": {
            "expires": 15.0,
        },
    }


"""FEC Webload settings
"""
MOCK_EFO_FILING = get_boolean_from_string(env.get_credential("MOCK_EFO_FILING", "False"))
EFO_FILING_API = env.get_credential("EFO_FILING_API")
EFO_FILING_API_KEY = env.get_credential("EFO_FILING_API_KEY")
if not MOCK_EFO_FILING:
    if EFO_FILING_API is None:
        raise Exception("EFO_FILING_API must be set if MOCK_EFO_FILING is False")
    if EFO_FILING_API_KEY is None:
        raise Exception("EFO_FILING_API_KEY must be set if MOCK_EFO_FILING is False")
FEC_AGENCY_ID = env.get_credential("FEC_AGENCY_ID")
FEC_FORMAT_VERSION = env.get_credential("FEC_FORMAT_VERSION")

"""EFO POLLING SETTINGS
"""

INITIAL_POLLING_INTERVAL = get_float_from_string(
    env.get_credential("INITIAL_POLLING_INTERVAL", 30)
)
INITIAL_POLLING_DURATION = get_float_from_string(
    env.get_credential("INITIAL_POLLING_DURATION", 300)
)

INITIAL_POLLING_MAX_ATTEMPTS = floor(INITIAL_POLLING_DURATION / INITIAL_POLLING_INTERVAL)

SECONDARY_POLLING_INTERVAL = get_float_from_string(
    env.get_credential("SECONDARY_POLLING_INTERVAL", 30)
)
SECONDARY_POLLING_DURATION = get_float_from_string(
    env.get_credential("SECONDARY_POLLING_DURATION", 300)
)

SECONDARY_POLLING_MAX_ATTEMPTS = floor(
    SECONDARY_POLLING_DURATION / SECONDARY_POLLING_INTERVAL
)

"""OUTPUT_TEST_INFO_IN_DOT_FEC will configure the .fec writer to output extra
info for testing purposes
WARNING: This will BREAK submitting to fec because it will no longer conform to spec
"""
OUTPUT_TEST_INFO_IN_DOT_FEC = env.get_credential("OUTPUT_TEST_INFO_IN_DOT_FEC")

AWS_ACCESS_KEY_ID = env.get_credential("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.get_credential("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env.get_credential("AWS_STORAGE_BUCKET_NAME")
AWS_REGION = env.get_credential("AWS_REGION")
S3_OBJECTS_MAX_AGE_DAYS = get_float_from_string(
    env.get_credential("S3_OBJECTS_MAX_AGE_DAYS", 365)
)

"""FEATURE FLAGS
"""

# FLAG__COMMITTEE_DATA_SOURCE:
# Determines whether committee data is pulled from EFO, TestEFO, or REDIS
FLAG__COMMITTEE_DATA_SOURCE = env.get_credential("FLAG__COMMITTEE_DATA_SOURCE")
valid_sources = ["PRODUCTION", "TEST", "MOCKED"]
if FLAG__COMMITTEE_DATA_SOURCE not in valid_sources:
    raise Exception(
        f'FLAG__COMMITTEE_DATA_SOURCE "{FLAG__COMMITTEE_DATA_SOURCE}"'
        + f" must be valid source ({valid_sources})"
    )


PRODUCTION_OPEN_FEC_API = env.get_credential("PRODUCTION_OPEN_FEC_API")
PRODUCTION_OPEN_FEC_API_KEY = env.get_credential("PRODUCTION_OPEN_FEC_API_KEY")

STAGE_OPEN_FEC_API = env.get_credential("STAGE_OPEN_FEC_API")
STAGE_OPEN_FEC_API_KEY = env.get_credential("STAGE_OPEN_FEC_API_KEY")

"""MOCK OPENFEC settings"""
MOCK_OPENFEC_REDIS_URL = env.get_credential("REDIS_URL")

TEST_RUNNER = "fecfiler.test_runner.CustomTestRunner"

ENABLE_RESTRICTED_COMMANDS = get_boolean_from_string(
    env.get_credential("ENABLE_RESTRICTED_COMMANDS", "False")
)

E2E_TEST = get_boolean_from_string(env.get_credential("E2E_TEST", "False"))
