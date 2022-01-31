from .base import *  # noqa F401, F403

# TODO: Do we want to removee fallback to random string in prod?
# SECRET_KEY = env.get_credential('DJANGO_SECRET_KEY')

# These settings are used for all public environments:
# dev, stage and production

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = False

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

ALLOWED_HOSTS = [
    # '.fec.gov',
    '.app.cloud.gov'
]
