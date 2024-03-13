"""
Django settings for ddsr project.

Generated by 'django-admin startproject' using Django 5.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import posixpath
import re
import sys
import environ


# App name

APP_NAME = 'dds_registration'  # Root app name


# Define default site id for `sites.models`
SITE_ID = 1

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Determine dev mode...

RUNNING_DEVSERVER = len(sys.argv) > 1 and sys.argv[1] == 'runserver'
RUNNING_MANAGE_PY = len(sys.argv) > 0 and sys.argv[0] == 'manage.py'
RUNNING_MOD_WSGI = len(sys.argv) > 0 and sys.argv[0] == 'mod_wsgi'
# TODO: Correctly determine is it runnning on production server or locally?
LOCAL_RUN = RUNNING_MANAGE_PY and not RUNNING_MOD_WSGI
LOCAL = LOCAL_RUN and RUNNING_DEVSERVER
DEV = LOCAL

# Env variables...

env = environ.Env(
    # @see https://django-environ.readthedocs.io
    DEBUG=(bool, True),  # LOCAL  # and DEV
    SECRET_KEY=(str, 'django-insecure-1d*alw^8-nya9h#xhfjqe*5%w8!o7vy8!211ez++h!p_*nm%21'),
    SENDGRID_API_KEY=(str, ''),
)
environ.Env.read_env(posixpath.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
# NOTE: Set your `SECRET_KEY` in `.env` (see `.env.SAMPLE` for example)
SECRET_KEY = env('SECRET_KEY')

# NOTE: Set your `DEBUG` in `.env` (see `.env.SAMPLE` for example)
DEBUG = env('DEBUG')

# Use filters to preprocess assets' sources (like sass, see `COMPRESS_PRECOMPILERS` section below)
USE_DJANGO_PREPROCESSORS = LOCAL and True

# Core folders...

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_FOLDER = 'static/'
STATIC_ROOT = posixpath.join(BASE_DIR, STATIC_FOLDER)
STATIC_URL = posixpath.join('/', STATIC_FOLDER)

MEDIA_FOLDER = 'media/'
MEDIA_ROOT = posixpath.join(BASE_DIR, MEDIA_FOLDER)
MEDIA_URL = posixpath.join('/', MEDIA_FOLDER)

ASSETS_FOLDER = 'assets/'
ASSETS_ROOT = posixpath.join(STATIC_ROOT, ASSETS_FOLDER)

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like '/home/html/static' or 'C:/www/django/static'.
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #  STATIC_ROOT,
    #  ASSETS_ROOT,  ## Debug only
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'sass --embed-source-map {infile} {outfile}'),
    # Sass installation:
    # - https://sass-lang.com/install/
    # - https://github.com/sass/dart-sass/releases/latest
    # @see https://django-compressor.readthedocs.io/en/stable/settings.html#django.conf.settings.COMPRESS_PRECOMPILERS
    #  ('text/x-scss', 'django_libsass.SassCompiler'),  # NOTE: DEPRECATED!
    #  ('text/coffeescript', 'coffee --compile --stdio'),
    #  ('text/less', 'lessc {infile} {outfile}'),
    #  ('text/x-sass', 'sass {infile} {outfile}'),
    #  ('text/stylus', 'stylus < {infile} > {outfile}'),
    #  ('text/foobar', 'path.to.MyPrecompilerFilter'),
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    #  # @see: https://github.com/praekelt/django-preferences
    #  'preferences',
    'compressor',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_registration',
    #  'django_extensions',
    #  'debug_toolbar',
    #  'accounts', # Custom accounts extensions (unused in favour of django_registration)
    APP_NAME,
]

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'

CRISPY_TEMPLATE_PACK = 'bootstrap5'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add livereload app...
# @see https://pypi.org/project/django-livereload/
# Run the reload server with a command: `python manage.py livereload static`
INSTALLED_APPS.insert(0, 'livereload')
if False or DEV:
    MIDDLEWARE.append('livereload.middleware.LiveReloadScript')


ROOT_URLCONF = APP_NAME + '.urls'

# Templates folders...
#  TEMPLATES_PATH = posixpath.join(BASE_DIR, APP_NAME, 'templates')
TEMPLATES_PATH = BASE_DIR / APP_NAME / 'templates'

TEMPLATE_DIRS = [
    TEMPLATES_PATH,
    STATIC_ROOT,
]
#  if DEV:
#      # Extra templates folders...
#      TEMPLATE_DIRS.append(ASSETS_ROOT)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                #  # @see: https://github.com/praekelt/django-preferences
                #  'preferences.context_processors.preferences_cp',
                # Pass local context to the templates. @see `main/context_processors.py`
                APP_NAME + '.context_processors.common_values',
            ],
        },
        'DIRS': TEMPLATE_DIRS,
    },
]

WSGI_APPLICATION = APP_NAME + '.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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

#  AUTH_PROFILE_MODULE = APP_NAME + '.User'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'index'

# Registration
# @see https://django-registration.readthedocs.io

ACCOUNT_ACTIVATION_DAYS = 7   # One-week activation window

# Sending emails with sendgrid

# @see https://docs.sendgrid.com/for-developers/sending-email/django
DEFAULT_FROM_EMAIL = 'noreply@d-d-s.ch'
# TODO: Store parameters in `django-preferences` (see)?
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'   # this is exactly the value 'apikey'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# NOTE: Set your `SENDGRID_API_KEY` in `.env` (see `.env.SAMPLE` for example)
EMAIL_HOST_PASSWORD = env('SENDGRID_API_KEY')
# NOTE: Check if `SENDGRID_API_KEY` hasn't set (write to log and stop server)...
if not EMAIL_HOST_PASSWORD:
    error_text = 'Error: A required sendgrid api key SENDGRID_API_KEY is not provided! It expected to be set in .env file (see .env.SAMPLE).'
    raise Exception(error_text)

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = False

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# @see: https://docs.djangoproject.com/en/2.0/ref/templates/builtins/#std:templatefilter-date
DATE_FORMAT = 'Y.m.d'
TIME_FORMAT = 'H:i'
DATETIME_FORMAT = DATE_FORMAT + TIME_FORMAT

# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
#
# Logging levels:
#
# - DEBUG: Low level system information for debugging purposes
# - INFO: General system information
# - WARNING: Information describing a minor problem that has occurred.
# - ERROR: Information describing a major problem that has occurred.
# - CRITICAL: Information describing a critical problem that has occurred.
#
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    # 'incremental': True,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%Y.%m.%d %H:%M:%S',
        },
        'simple': {'format': '%(levelname)s %(message)s'},
    },
    'filters': {
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'},
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'django': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': posixpath.join(BASE_DIR, 'log-django.log'),
            'formatter': 'verbose',
        },
        'apps': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': posixpath.join(BASE_DIR, 'log-apps.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['django'],
            'propagate': True,
            'level': 'INFO',
        },
        APP_NAME: {
            'handlers': ['apps'],
            'level': 'DEBUG',
        },
    },
}

# @see: https://docs.djangoproject.com/en/2.0/ref/settings/#timeout
TIMEOUT = 30 if DEBUG else 300  # Short value for debug time

# Site config

# TODO: Use `Site.objects.get_current().name` (via `from django.contrib.sites.models import Site`) as site title.
SITE_NAME = 'DdS Registration'
SITE_TITLE = SITE_NAME
SITE_DESCRIPTION = SITE_NAME
SITE_KEYWORDS = """
DdS
Registration
application
"""
SITE_KEYWORDS = re.sub(r'\s*[\n\r]+\s*', ', ', SITE_KEYWORDS.strip())

if DEV:
    SITE_TITLE += ' (DEV)'

# Pass settings to context...
PASS_VARIABLES = {
    'DEBUG': DEBUG,
    'DEV': DEV,
    #  'LOCAL_RUN': LOCAL_RUN,
    'LOCAL': LOCAL,
    'USE_DJANGO_PREPROCESSORS': USE_DJANGO_PREPROCESSORS,
    'SITE_NAME': SITE_NAME,
    'SITE_TITLE': SITE_TITLE,
    # 'ASSETS_FOLDER': ASSETS_FOLDER,
    # 'STATIC_ROOT': STATIC_ROOT,
    # 'ASSETS_ROOT': ASSETS_ROOT,
    # 'STATIC_URL': STATIC_URL,
    'SITE_DESCRIPTION': SITE_DESCRIPTION,
    'SITE_KEYWORDS': SITE_KEYWORDS,
}
