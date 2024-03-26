# -*- coding:utf-8 -*-
from pathlib import Path
import environ
import os
import posixpath
import re
import sys


# Working folder

BASE_DIR = Path(__file__).resolve().parent.parent


# App name

APP_NAME = "dds_registration"


# Define default site id for `sites.models`
SITE_ID = 1

env = environ.Env(
    # @see local `.dev` file and example in `.dev.SAMPLE`
    # @see https://django-environ.readthedocs.io
    DEV=(bool, False),  # Dev server mode
    DEBUG=(bool, False),  # Django debug mode
    LOCAL=(bool, False),  # Local dev server mode
    SECRET_KEY=(str, ""),
    SENDGRID_API_KEY=(str, ""),
    REGISTRATION_SALT=(str, ""),
    DEFAULT_FROM_EMAIL=(str, "events@d-d-s.ch"),
)

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
environ.Env.read_env(os.path.join(BASE_DIR, ".env.local"))

DEV = env("DEV")
DEBUG = env("DEBUG")
LOCAL = env("LOCAL")

SECRET_KEY = env("SECRET_KEY")
REGISTRATION_SALT = env("REGISTRATION_SALT")
SENDGRID_API_KEY = env("SENDGRID_API_KEY")

if not SECRET_KEY or not REGISTRATION_SALT or not SENDGRID_API_KEY:
    error_text = "Error: Environment configuration variables are required (check for your local `.env*` files, refer to `.env.SAMPLE`)."
    raise Exception(error_text)

if not SECRET_KEY or not REGISTRATION_SALT or not SENDGRID_API_KEY:
    error_text = "Error: Environment configuration variables are required (check for your local `.env` file, refer to `.env.SAMPLE`)."
    raise Exception(error_text)

# Preprocess scss source files wwith django filters
USE_DJANGO_PREPROCESSORS = DEV

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_FOLDER = "static/"
STATIC_ROOT = posixpath.join(BASE_DIR, STATIC_FOLDER)
STATIC_URL = posixpath.join("/", STATIC_FOLDER)

MEDIA_FOLDER = "media/"
MEDIA_ROOT = posixpath.join(BASE_DIR, MEDIA_FOLDER)
MEDIA_URL = posixpath.join("/", MEDIA_FOLDER)

# The folder for asset file sources
SRC_FOLDER = "src"
SRC_ROOT = posixpath.join(BASE_DIR, SRC_FOLDER)

ASSETS_FOLDER = "assets/"
ASSETS_ROOT = posixpath.join(SRC_FOLDER, ASSETS_FOLDER)

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like '/home/html/static' or 'C:/www/django/static'.
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

if DEV:
    # Add asset file sources to static folders in dev mode to access scss sources via django filters during dev mode time
    STATICFILES_DIRS += (SRC_ROOT,)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

COMPRESS_PRECOMPILERS = (
    ("text/x-scss", "sass --embed-source-map {infile} {outfile}"),
    # Sass installation:
    # - https://sass-lang.com/install/
    # - https://github.com/sass/dart-sass/releases/latest
    # @see https://django-compressor.readthedocs.io/en/stable/settings.html#django.conf.settings.COMPRESS_PRECOMPILERS
)

# These settings already exist in `default_settings.py` Should we remove those?
ALLOWED_HOSTS = ["events.d-d-s.ch"]
CSRF_TRUSTED_ORIGINS = ["https://events.d-d-s.ch"]

if LOCAL:
    # Allow work with local server in local dev mode
    ALLOWED_HOSTS.append("localhost")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "compressor",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_registration",
    APP_NAME,
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Add livereload app...
# @see https://pypi.org/project/django-livereload/
# Run the reload server with a command: `python manage.py livereload src static`
INSTALLED_APPS.insert(0, "livereload")
# TODO: Do we actually need livereload in production? I remember some issues with it. Can we completely remove it from production?
# There is already present the check in the `dds_registration/templates/base-core.html.django` template:
# ```
#  {% if settings.DEV %}
#  {% load livereload_tags %}
#  {% endif %}
# ```
# -- but probably it doesn't work?

if DEV:
    MIDDLEWARE.append("livereload.middleware.LiveReloadScript")


ROOT_URLCONF = APP_NAME + ".urls"

# Templates folders...
APP_TEMPLATES_PATH = BASE_DIR / APP_NAME / "templates"

TEMPLATE_DIRS = [
    APP_TEMPLATES_PATH,
    SRC_ROOT,  # To access template include blocks
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                APP_NAME + ".context_processors.common_values",
            ],
        },
        "DIRS": TEMPLATE_DIRS,
    },
]

WSGI_APPLICATION = APP_NAME + ".wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

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

LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"

# Random salt for registration keys (to use in django_registration module)
REGISTRATION_SALT = env("REGISTRATION_SALT")

# Registration
# @see https://django-registration.readthedocs.io

AUTH_USER_MODEL = APP_NAME + ".User"
AUTHENTICATION_BACKENDS = [APP_NAME + ".backends.EmailBackend"]

ACCOUNT_ACTIVATION_DAYS = 7  # One-week activation window

# NOTE: It's possible to store some of these parameters (`DEFAULT_FROM_EMAIL`, definitely) in the site preferences or in the `.env*` files
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"  # this is exactly the value 'apikey'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# @see https://docs.sendgrid.com/for-developers/sending-email/django
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = False

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# @see: https://docs.djangoproject.com/en/2.0/ref/templates/builtins/#std:templatefilter-date
DATE_FORMAT = "Y.m.d"
TIME_FORMAT = "H:i"
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
    "version": 1,
    "disable_existing_loggers": False,
    # 'incremental': True,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%Y.%m.%d %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "django": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": posixpath.join(BASE_DIR, "log-django.log"),
            "formatter": "verbose",
        },
        "apps": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": posixpath.join(BASE_DIR, "log-apps.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["django"],
            "propagate": True,
            "level": "INFO",
        },
        APP_NAME: {
            "handlers": ["apps"],
            "level": "DEBUG",
        },
    },
}

# @see: https://docs.djangoproject.com/en/2.0/ref/settings/#timeout
TIMEOUT = 30 if DEBUG else 300  # Short value for debug time

# Site config

# TODO: Use `Site.objects.get_current().name` (via `from django.contrib.sites.models import Site`) as site title.
SITE_NAME = "Départ de Sentier Events and Membership Portal"
SITE_TITLE = SITE_NAME
SITE_DESCRIPTION = SITE_NAME
SITE_KEYWORDS = """
Registration
Events
"""
SITE_KEYWORDS = re.sub(r"\s*[\n\r]+\s*", ", ", SITE_KEYWORDS.strip())
# TODO: Issue #30: Add correct tags, resources for SSO, search engines and social networks (open graph etc)

# Pass settings to context...
PASS_VARIABLES = {
    "DEBUG": DEBUG,  # Pass django debug flag to the code (from environment)
    "DEV": DEV,  # Dev server mode (from the environment)
    "LOCAL": LOCAL,  # Local dev server mode (from the environment)
    "USE_DJANGO_PREPROCESSORS": USE_DJANGO_PREPROCESSORS,
    # NOTE: Site url and name could be taken from site data via `get_current_site`
    "SITE_NAME": SITE_NAME,
    "SITE_TITLE": SITE_TITLE,
    "SITE_DESCRIPTION": SITE_DESCRIPTION,
    "SITE_KEYWORDS": SITE_KEYWORDS,
}
