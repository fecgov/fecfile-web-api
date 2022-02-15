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
    "rest_framework_swagger",
    "compressor",
    "corsheaders",
    "fecfiler.authentication",
    'fecfiler.forms',
    'db_file_storage',
    'fecfiler.f3x_summaries',
    'fecfiler.scha_transactions',
    'fecfiler.core',
    'fecfiler.sched_A',
    'fecfiler.sched_B',
    'fecfiler.sched_E',
    'fecfiler.sched_F',
    'fecfiler.sched_H',
    'fecfiler.sched_L',
    'storages',
    'fecfiler.form_1M',
    'fecfiler.contacts',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'fecfiler.password_management'
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

# add the credentials from IAM and bucket name
AWS_STORAGE_BUCKET_NAME = "fecfile-filing"  # or None if using service role
AWS_STORAGE_UPLOAD_BUCKET_NAME = (
    "fecfile-filing-uploads"  # or None if using service role
)
AWS_STORAGE_IMPORT_CONTACT_BUCKET_NAME = "fecfile-filing-frontend"

# if False it will create unique file names for every uploaded file
AWS_S3_FILE_OVERWRITE = False
# the url, that your media and static files will be available at
S3_URL = "%s.s3.amazonaws.com"
AWS_S3_CUSTOM_DOMAIN = S3_URL % AWS_STORAGE_BUCKET_NAME
AWS_S3_CUSTOM_UPLOAD_DOMAIN = S3_URL % AWS_STORAGE_UPLOAD_BUCKET_NAME

# a custom storage file, so we can easily put static and media in one bucket
DEFAULT_FILE_STORAGE = "fecfiler.custom_storages.MediaStorage"

AWS_ACCESS_KEY_ID = os.environ.get("ACCESS_KEY", None)
AWS_SECRET_ACCESS_KEY = os.environ.get("SECRET_KEY", None)
AWS_HOST_NAME = "us-east-1"
AWS_REGION = "us-east-1"
AWS_DEFAULT_ACL = None
AWS_SES_AUTO_THROTTLE = 0.5  # (default; safety factor applied to rate limit, turn off automatic throttling, set this to None)

USPS_USERNAME = os.environ.get("USPS_USERNAME", None)
USPS_API_URL = os.environ.get("USPS_API_URL", None)

# the sub-directories of media and static files
STATICFILES_LOCATION = "static"
MEDIAFILES_LOCATION = "media"

NXG_FEC_API_URL = os.environ.get("NXG_API_URL", "127.0.0.1:8080")
NXG_FEC_API_VERSION = os.environ.get("NXG_API_VERSION", "/api/v1/")

NXG_FEC_PRINT_API_URL = os.environ.get(
    "PRINTPDF_URL", "https://dev-efile-api.efdev.fec.gov/printpdf"
)
NXG_FEC_PRINT_API_VERSION = "/v1/print"

# SUBMISSION REPORT SETTINGS
NXG_COMMITTEE_DEFAULT_PASSWORD = os.environ.get(
    "NXG_COMMITTEE_DEFAULT_PASSWORD", "test"
)
SUBMIT_REPORT_WAIT_FLAG = "False"

# Service Endpoint for filing confirmation email
NXG_FEC_FILING_CONFIRMATION_URL = os.environ.get(
    "FILING_CONFIRMATION_URL",
    "https://dev-efile-api.efdev.fec.gov/receiver/v1/acknowledgement_email",
)

# dcf_converter end point details
NXG_FEC_DCF_CONVERTER_API_URL = os.environ.get(
    "DCF_CONVERTER_URL", "https://dev-efile-api.efdev.fec.gov/dcf_converter"
)
NXG_FEC_DCF_CONVERTER_API_VERSION = "/v1/import"

# the regular Django file settings but with the custom S3 URLs
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_UPLOAD_DOMAIN, MEDIAFILES_LOCATION)

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_jwt.authentication.JSONWebTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
}

JWT_AUTH = {
    "JWT_ALLOW_REFRESH": True,
    "JWT_EXPIRATION_DELTA": datetime.timedelta(seconds=3600),
    "JWT_RESPONSE_PAYLOAD_HANDLER": "fecfiler.authentication.views.jwt_response_payload_handler",
    "JWT_PAYLOAD_HANDLER": "fecfiler.authentication.token.jwt_payload_handler",
}


ADMIN_SHORTCUTS = [
    {
        "shortcuts": [
            {
                "url": "/",
                "open_new_window": True,
            },
            {
                "url_name": "admin:authentication_account_changelist",
                "title": "Users",
            },
        ]
    },
]

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
