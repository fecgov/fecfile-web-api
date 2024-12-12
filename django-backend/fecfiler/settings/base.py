"""
Django settings for the FECFile project.
"""

import os
import dj_database_url
import structlog
import sys

from .env import env
from corsheaders.defaults import default_headers
from django.utils.crypto import get_random_string
from fecfiler.celery import CeleryStorageType
from fecfiler.shared.utilities import get_float_from_string
from math import floor


def get_boolean(value):
    return value.lower() == "true"


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", True)
TEMPLATE_DEBUG = DEBUG

LINE = "LINE"
KEY_VALUE = "KEY_VALUE"

LOG_FORMAT = env.get_credential("LOG_FORMAT", LINE)

CSRF_COOKIE_DOMAIN = env.get_credential("FFAPI_COOKIE_DOMAIN")
CSRF_TRUSTED_ORIGINS = ["https://*.fecfile.fec.gov"]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.get_credential("DJANGO_SECRET_KEY", get_random_string(50))
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
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "fecfiler.middleware.HeaderMiddleware",
    "fecfiler.oidc.middleware.TimeoutMiddleware.TimeoutMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": ["templates", "static/templates"],
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
    "https://idp.int.identitysandbox.gov/.well-known/openid-configuration",
)

MOCK_OIDC_PROVIDER = get_boolean(env.get_credential("MOCK_OIDC_PROVIDER", "False"))
MOCK_OIDC_PROVIDER_CACHE = env.get_credential("REDIS_URL")

OIDC_ACR_VALUES = "http://idmanagement.gov/ns/assurance/ial/1"

FFAPI_COOKIE_DOMAIN = env.get_credential("FFAPI_COOKIE_DOMAIN")
FFAPI_LOGIN_DOT_GOV_COOKIE_NAME = "ffapi_login_dot_gov"
FFAPI_TIMEOUT_COOKIE_NAME = "ffapi_timeout"

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


def get_logging_config(log_format=LINE):
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
            "plain_console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.dev.ConsoleRenderer(
                        colors=True, exception_formatter=structlog.dev.rich_traceback
                    )
                ],
            },
            "key_value": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.processors.ExceptionRenderer(),
                    structlog.processors.KeyValueRenderer(
                        key_order=["level", "event", "logger"]
                    ),
                ],
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "plain_console",
                "stream": sys.stdout,
            },
            "cloud": {
                "class": "logging.StreamHandler",
                "formatter": "key_value",
                "stream": sys.stdout,
            },
        },
    }

    if log_format == LINE:
        logging_config["loggers"] = {
            "django_structlog": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
            "fecfiler": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
        }
    else:
        logging_config["loggers"] = {
            "django_structlog": {
                "handlers": ["cloud"],
                "level": "INFO",
            },
            "fecfiler": {
                "handlers": ["cloud"],
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
        structlog.stdlib.add_logger_name,
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

"""FEC Webload settings
"""
MOCK_EFO = get_boolean(env.get_credential("MOCK_EFO", "False"))
FEC_FILING_API = env.get_credential("FEC_FILING_API")
if not MOCK_EFO and FEC_FILING_API is None:
    raise Exception("FEC_FILING_API must be set if MOCK_EFO is False")
FEC_FILING_API_KEY = env.get_credential("FEC_FILING_API_KEY")
FEC_AGENCY_ID = env.get_credential("FEC_AGENCY_ID")

"""EFO POLLING SETTINGS
"""
EFO_POLLING_MAX_DURATION = get_float_from_string(
    env.get_credential("EFO_POLLING_MAX_DURATION", 300)
)
EFO_POLLING_INTERVAL = get_float_from_string(
    env.get_credential("EFO_POLLING_INTERVAL", 30)
)
EFO_POLLING_MAX_ATTEMPTS = floor(EFO_POLLING_MAX_DURATION / EFO_POLLING_INTERVAL)

"""OUTPUT_TEST_INFO_IN_DOT_FEC will configure the .fec writer to output extra
info for testing purposes
WARNING: This will BREAK submitting to fec because it will no longer conform to spec
"""
OUTPUT_TEST_INFO_IN_DOT_FEC = env.get_credential("OUTPUT_TEST_INFO_IN_DOT_FEC")

AWS_ACCESS_KEY_ID = env.get_credential("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.get_credential("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env.get_credential("AWS_STORAGE_BUCKET_NAME")
AWS_REGION = env.get_credential("AWS_REGION")


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

CREATE_COMMITTEE_ACCOUNT_ALLOWED_EMAIL_LIST = env.get_credential(
    "CREATE_COMMITTEE_ACCOUNT_ALLOWED_EMAIL_LIST", []
)

TEST_RUNNER = "fecfiler.test_runner.CustomTestRunner"

ENABLE_DEVELOPER_COMMANDS = get_boolean(
    env.get_credential("ENABLE_DEVELOPER_COMMANDS", "False")
)
