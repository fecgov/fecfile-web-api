"""
Django settings for the FECFile project.
"""

import os
import dj_database_url
import requests
import structlog
import sys

from .env import env
from corsheaders.defaults import default_headers
from django.utils.crypto import get_random_string
from fecfiler.celery import CeleryStorageType


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", True)
TEMPLATE_DEBUG = DEBUG

LINE = "LINE"
KEY_VALUE = "KEY_VALUE"

LOG_FORMAT = env.get_credential("LOG_FORMAT", LINE)

CSRF_COOKIE_DOMAIN = env.get_credential("FFAPI_COOKIE_DOMAIN")
CSRF_TRUSTED_ORIGINS = [
    env.get_credential("CSRF_TRUSTED_ORIGINS", "http://localhost:4200")
]

"""
Enables alternative log in method.
See :py:const:`fecfiler.authentication.views.USERNAME_PASSWORD`
and :py:meth:`fecfiler.authentication.views.authenticate_login`
"""
ALTERNATIVE_LOGIN = env.get_credential("ALTERNATIVE_LOGIN")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.get_credential("DJANGO_SECRET_KEY", get_random_string(50))


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
    "mozilla_django_oidc",  # Load after auth
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "storages",
    "django_structlog",
    "fecfiler.authentication",
    "fecfiler.committee_accounts",
    "fecfiler.reports",
    "fecfiler.transactions",
    "fecfiler.memo_text",
    "fecfiler.contacts",
    "fecfiler.soft_delete",
    "fecfiler.validation",
    "fecfiler.web_services",
    "fecfiler.openfec",
    "fecfiler.user",
    "fecfiler.mock_openfec",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "fecfiler.authentication.middleware.TimeoutMiddleware.TimeoutMiddleware",
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

# CORS_ALLOWED_ORIGINS = [
#     env.get_credential("CORS_ALLOWED_ORIGINS", "http://localhost:4200")
# ]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://(.*?).fec\.gov$",
    r"^https://(.*?).cloud\.gov$",
]
CORS_ALLOW_HEADERS = default_headers + ("enctype", "token")

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = ["https://*.fec.gov", "https://*.cloud.gov"]

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

# OpenID Connect settings start
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "mozilla_django_oidc.auth.OIDCAuthenticationBackend",
]

OIDC_CREATE_USER = True
OIDC_STORE_ID_TOKEN = True
# Maximum number of concurrent sessions
OIDC_MAX_STATES = 3

OIDC_RP_SIGN_ALGO = "RS256"
OIDC_RP_CLIENT_ID = env.get_credential("OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = env.get_credential("OIDC_RP_CLIENT_SECRET")

# The Django field used to identify users - default is email
OIDC_RP_UNIQUE_IDENTIFIER = "username"

# Sometimes the OP (IDP - login.gov)has a different label for the unique ID
OIDC_OP_UNIQUE_IDENTIFIER = "sub"

# Default implicit_flow is considered vulnerable
OIDC_OP_CLIENT_AUTH_METHOD = "private_key_jwt"

OIDC_OP_AUTODISCOVER_ENDPOINT = (
    "https://idp.int.identitysandbox.gov/.well-known/openid-configuration"
)
OIDC_OP_CONFIG = requests.get(OIDC_OP_AUTODISCOVER_ENDPOINT).json()

OIDC_OP_JWKS_ENDPOINT = OIDC_OP_CONFIG.get("jwks_uri")
OIDC_OP_AUTHORIZATION_ENDPOINT = OIDC_OP_CONFIG.get("authorization_endpoint")
OIDC_OP_TOKEN_ENDPOINT = OIDC_OP_CONFIG.get("token_endpoint")
OIDC_OP_USER_ENDPOINT = OIDC_OP_CONFIG.get("userinfo_endpoint")
OIDC_OP_LOGOUT_ENDPOINT = OIDC_OP_CONFIG.get("end_session_endpoint")
ALLOW_LOGOUT_GET_METHOD = True

FFAPI_COOKIE_DOMAIN = env.get_credential("FFAPI_COOKIE_DOMAIN")
FFAPI_LOGIN_DOT_GOV_COOKIE_NAME = "ffapi_login_dot_gov"
FFAPI_TIMEOUT_COOKIE_NAME = "ffapi_timeout"

LOGIN_REDIRECT_URL = env.get_credential("LOGIN_REDIRECT_SERVER_URL")
LOGIN_REDIRECT_CLIENT_URL = env.get_credential("LOGIN_REDIRECT_CLIENT_URL")
LOGOUT_REDIRECT_URL = env.get_credential("LOGOUT_REDIRECT_URL")

OIDC_AUTH_REQUEST_EXTRA_PARAMS = {
    "acr_values": "http://idmanagement.gov/ns/assurance/ial/1"
}

OIDC_OP_LOGOUT_URL_METHOD = "fecfiler.authentication.views.login_dot_gov_logout"

OIDC_USERNAME_ALGO = "fecfiler.authentication.views.generate_username"
# OpenID Connect settings end

USE_X_FORWARDED_HOST = True

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_DIRS = (os.path.join(BASE_DIR, "staticfiles"),)

STATIC_ROOT = "static"

# the sub-directories of media and static files
STATICFILES_LOCATION = "static"

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

DJANGO_STRUCTLOG_CELERY_ENABLED = True

"""Celery configurations
"""
CELERY_BROKER_URL = env.get_credential("REDIS_URL")
CELERY_RESULT_BACKEND = env.get_credential("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"


CELERY_LOCAL_STORAGE_DIRECTORY = os.path.join(BASE_DIR, "web_services/dot_fec/output")
CELERY_WORKER_STORAGE = env.get_credential("CELERY_WORKER_STORAGE", CeleryStorageType.AWS)

"""FEC Webload settings
"""
FEC_FILING_API = env.get_credential("FEC_FILING_API")
FEC_FILING_API_KEY = env.get_credential("FEC_FILING_API_KEY")
FEC_AGENCY_ID = env.get_credential("FEC_AGENCY_ID")
FILE_AS_TEST_COMMITTEE = env.get_credential("FILE_AS_TEST_COMMITTEE")
TEST_COMMITTEE_PASSWORD = env.get_credential("TEST_COMMITTEE_PASSWORD")
WEBPRINT_EMAIL = env.get_credential("WEBPRINT_EMAIL")
"""OUTPUT_TEST_INFO_IN_DOT_FEC will configure the .fec writer to output extra
info for testing purposes
WARNING: This will BREAK submitting to fec because it will no longer conform to spec
"""
OUTPUT_TEST_INFO_IN_DOT_FEC = env.get_credential("OUTPUT_TEST_INFO_IN_DOT_FEC")

AWS_ACCESS_KEY_ID = env.get_credential("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.get_credential("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env.get_credential("AWS_STORAGE_BUCKET_NAME")
AWS_REGION = env.get_credential("AWS_REGION")

"""FEC API settings
"""
FEC_API = env.get_credential("FEC_API")
FEC_API_KEY = env.get_credential("FEC_API_KEY")
FEC_API_COMMITTEE_LOOKUP_ENDPOINT = str(FEC_API) + "names/committees/"
FEC_API_CANDIDATE_LOOKUP_ENDPOINT = str(FEC_API) + "candidates/"
FEC_API_CANDIDATE_ENDPOINT = str(FEC_API) + "candidate/{}/history/"


"""MOCK OPENFEC settings"""
MOCK_OPENFEC = env.get_credential("MOCK_OPENFEC")
if MOCK_OPENFEC == "REDIS":
    MOCK_OPENFEC_REDIS_URL = env.get_credential("REDIS_URL")
else:
    MOCK_OPENFEC_REDIS_URL = None
