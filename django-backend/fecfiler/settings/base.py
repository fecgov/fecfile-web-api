"""
Django settings for the FECFile project.
"""

import os
import datetime
import dj_database_url

from .env import env
from corsheaders.defaults import default_headers
from django.utils.crypto import get_random_string


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", True)
TEMPLATE_DEBUG = DEBUG

CSRF_TRUSTED_ORIGINS = ["localhost", os.environ.get("FRONTEND_URL", "api")]
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_RECEIVE_API_URL = os.environ.get("DATA_RECEIVER_URL", "0.0.0.0:8090")
DATA_RECEIVE_API_VERSION = "/v1/"

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

TIME_ZONE = "America/New_York"

CONTACT_MATCH_PERCENTAGE = 92

LOGIN_TIMEOUT_TIME = 15
LOGIN_MAX_RETRY = 3
REGISTER_USER_URL = os.environ.get(
    "REGISTER_USER_URL", "http://localhost/#/register?register_token="
)
OTP_MAX_RETRY = 20
OTP_DIGIT = 6
OTP_TIME_EXPIRY = 300
OTP_TIMEOUT_TIME = 30
OTP_DISABLE = True
OTP_DEFAULT_PASSCODE = "111111"
JWT_PASSWORD_EXPIRY = 1800
API_LOGIN = os.environ.get("API_LOGIN", None)
API_PASSWORD = os.environ.get("API_PASSWORD", None)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.get_credential("DJANGO_SECRET_KEY", get_random_string(50))

FECFILE_FEC_WEBSITE_API_KEY = env.get_credential("FECFILE_FEC_WEBSITE_API_KEY")

ROOT_URLCONF = "fecfiler.urls"
WSGI_APPLICATION = "fecfiler.wsgi.application"
AUTH_USER_MODEL = "authentication.Account"

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "fecfiler.authentication",
    "fecfiler.f3x_summaries",
    "fecfiler.scha_transactions",
    "fecfiler.contacts",
    "fecfiler.soft_delete",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "fecfiler.triage",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = default_headers + ("enctype", "token")

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

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

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

COMPRESS_ENABLED = os.environ.get("COMPRESS_ENABLED", not DEBUG)


# a custom storage file, so we can easily put static and media in one bucket
DEFAULT_FILE_STORAGE = "fecfiler.custom_storages.MediaStorage"


# the sub-directories of media and static files
STATICFILES_LOCATION = "static"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_jwt.authentication.JSONWebTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

JWT_AUTH = {
    "JWT_ALLOW_REFRESH": True,
    "JWT_EXPIRATION_DELTA": datetime.timedelta(seconds=3600),
    "JWT_PAYLOAD_HANDLER": "fecfiler.authentication.token.jwt_payload_handler",
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "default": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/access.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "standard",
        },
        "request_handler": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/access.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {"handlers": ["default"], "level": "DEBUG", "propagate": True},
        "django.request": {
            "handlers": ["request_handler"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# make all loggers use the console.
for logger in LOGGING["loggers"]:
    LOGGING["loggers"][logger]["handlers"] = ["console"]
