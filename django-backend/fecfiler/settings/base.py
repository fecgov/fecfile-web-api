"""
Django settings for the FECFile project.
"""

import os
import dj_database_url
import requests

from .env import env
from corsheaders.defaults import default_headers
from django.utils.crypto import get_random_string
from fecfiler.celery import CeleryStorageType


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", True)
TEMPLATE_DEBUG = DEBUG

CSRF_COOKIE_DOMAIN = env.get_credential("FFAPI_COOKIE_DOMAIN")

CSRF_TRUSTED_ORIGINS = [
    env.get_credential("CSRF_TRUSTED_ORIGINS", "http://localhost:4200")
]

# E2E Testing Login API
# Defaults to False, overriden by local.py & e2e.py
# Set to True until we're ready to deprecate the old login
E2E_TESTING_LOGIN = True


LOGIN_TIMEOUT_TIME = 15
LOGIN_MAX_RETRY = 3
JWT_PASSWORD_EXPIRY = 1800

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.get_credential("DJANGO_SECRET_KEY", get_random_string(50))


ROOT_URLCONF = "fecfiler.urls"
WSGI_APPLICATION = "fecfiler.wsgi.application"
AUTH_USER_MODEL = "authentication.Account"

ALLOWED_HOSTS = ["*"]

# Application definition

SESSION_COOKIE_AGE = 15 * 60  # Inactivity timeout
SESSION_SAVE_EVERY_REQUEST = True

INSTALLED_APPS = [
    "django.contrib.admin",
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
    "fecfiler.authentication",
    "fecfiler.committee_accounts",
    "fecfiler.f3x_summaries",
    "fecfiler.scha_transactions",
    "fecfiler.memo_text",
    "fecfiler.contacts",
    "fecfiler.soft_delete",
    "fecfiler.validation",
    "fecfiler.web_services",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "fecfiler.triage",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "fecfiler.authentication.middleware.AuthMiddleware"
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

CORS_ALLOWED_ORIGINS = [
    env.get_credential("CORS_ALLOWED_ORIGINS", "http://localhost:4200")
]
CORS_ALLOW_HEADERS = default_headers + ("enctype", "token")

CORS_ALLOW_CREDENTIALS = True

# Database
DATABASES = {
    # Be sure to set the DATABASE_URL environment variable on your local
    # development machine so that the local database can be connected to.
    "default": dj_database_url.config()
}

# Override default test name
DATABASES["default"]["TEST"] = {
    "NAME": os.environ.get("FECFILE_TEST_DB_NAME", "postgres")
}

# Connection string for connecting directly
DATABASE_URL = os.environ.get("DATABASE_URL")

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# OpenID Connect settings start
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "mozilla_django_oidc.auth.OIDCAuthenticationBackend",
)

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

# TODO: Env vars?
FFAPI_COMMITTEE_ID_COOKIE_NAME = "ffapi_committee_id"
FFAPI_EMAIL_COOKIE_NAME = "ffapi_email"
FFAPI_COOKIE_DOMAIN = env.get_credential("FFAPI_COOKIE_DOMAIN")

LOGIN_REDIRECT_URL = env.get_credential("LOGIN_REDIRECT_SERVER_URL")
LOGIN_REDIRECT_CLIENT_URL = env.get_credential("LOGIN_REDIRECT_CLIENT_URL")
LOGOUT_REDIRECT_URL = env.get_credential("LOGOUT_REDIRECT_URL")

OIDC_AUTH_REQUEST_EXTRA_PARAMS = {
    "acr_values": "http://idmanagement.gov/ns/assurance/ial/1"
}

OIDC_OP_LOGOUT_URL_METHOD = "fecfiler.authentication.token.login_dot_gov_logout"

OIDC_USERNAME_ALGO = "fecfiler.authentication.token.generate_username"
# OpenID Connect settings end

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
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

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
        "": {"handlers": ["default"], "level": "INFO", "propagate": True},
    },
}

"""Celery configurations
"""
CELERY_BROKER_URL = env.get_credential("REDIS_URL")
CELERY_RESULT_BACKEND = env.get_credential("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"


CELERY_LOCAL_STORAGE_DIRECTORY = os.path.join(BASE_DIR, "web_services/dot_fec/output")
CELERY_WORKER_STORAGE = env.get_credential(
    "CELERY_WORKER_STORAGE", CeleryStorageType.AWS
)

"""FEC Webload settings
"""
FEC_FILING_API = env.get_credential("FEC_FILING_API")
FEC_FILING_API_KEY = env.get_credential("FEC_FILING_API_KEY")
FEC_AGENCY_ID = env.get_credential("FEC_AGENCY_ID")
FILE_AS_TEST_COMMITTEE = env.get_credential("FILE_AS_TEST_COMMITTEE")
TEST_COMMITTEE_PASSWORD = env.get_credential("TEST_COMMITTEE_PASSWORD")
WEBPRINT_EMAIL = env.get_credential("WEBPRINT_EMAIL")

AWS_ACCESS_KEY_ID = env.get_credential("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.get_credential("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env.get_credential("AWS_STORAGE_BUCKET_NAME")
AWS_REGION = env.get_credential("AWS_REGION")

"""FEC API settings
"""
FEC_API = env.get_credential("FEC_API")
FEC_API_KEY = env.get_credential("FEC_API_KEY")
FEC_API_COMMITTEE_LOOKUP_ENDPOINT = str(FEC_API) + "names/committees/"
