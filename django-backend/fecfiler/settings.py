
"""
Django settings for FEC-EFiler project.

Django 1.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import datetime

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

#DEBUG = os.environ.get('DEBUG', False)
DEBUG = True
TEMPLATE_DEBUG = DEBUG
CSRF_TRUSTED_ORIGINS = ['localhost','api']
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SECRET_KEY = '$6(x*g_2g9l_*g8peb-@anl5^*8q!1w)k&e&2!i)t6$s8kia94'


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '!0)(sp6(&$=_70&+_(zogh24=)@5&smwtuwq@t*v88tn-#m=)z'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ROOT_URLCONF = 'fecfiler.urls'
WSGI_APPLICATION = 'fecfiler.wsgi.application'
AUTH_USER_MODEL = 'authentication.Account'


ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'djangocms_admin_style',
    'admin_shortcuts',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_swagger',
    'compressor',
    'corsheaders',
    'fecfiler.authentication',
    'fecfiler.posts',
    'fecfiler.forms',    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates','static/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


CORS_ORIGIN_ALLOW_ALL = True

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {

    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # }

    
     'default': {
         'ENGINE': 'django.db.backends.postgresql_psycopg2',
         'NAME': 'postgres',
         'USER': 'postgres',
         'PASSWORD': 'postgres',
         'HOST': '127.0.0.1',
         'PORT': '5432',
     }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
        os.path.join(BASE_DIR, 'staticfiles'),
    )

STATIC_ROOT = 'static'

COMPRESS_ENABLED = os.environ.get('COMPRESS_ENABLED', not DEBUG)

 
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
}

JWT_AUTH = {
        'JWT_ALLOW_REFRESH': True,
        'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=3600),
    }
                          
ADMIN_SHORTCUTS = [
    {
        'shortcuts': [
            {
                'url': '/',
                'open_new_window': True,
            },
             {
                 'url_name': 'admin:authentication_account_changelist',
                 'title': 'Users',
             },
        ]
    },
]


try:
    from .local_settings import *
except:
    pass
