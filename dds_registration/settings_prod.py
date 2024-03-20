import posixpath
import re
from pathlib import Path

import environ

APP_NAME = "dds_registration"
SITE_ID = 1
LOCAL=False

env = environ.Env(
    # @see https://django-environ.readthedocs.io
    DEBUG=(bool, False),
    SECRET_KEY=(str, ""),
    SENDGRID_API_KEY=(str, ""),
    REGISTRATION_SALT=(str, ""),
)

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
REGISTRATION_SALT = env("REGISTRATION_SALT")

USE_DJANGO_PREPROCESSORS = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_FOLDER = "static/"
STATIC_ROOT = posixpath.join(BASE_DIR, STATIC_FOLDER)
STATIC_URL = posixpath.join("/", STATIC_FOLDER)

MEDIA_FOLDER = "media/"
MEDIA_ROOT = posixpath.join(BASE_DIR, MEDIA_FOLDER)
MEDIA_URL = posixpath.join("/", MEDIA_FOLDER)

ASSETS_FOLDER = "assets/"
ASSETS_ROOT = posixpath.join(STATIC_ROOT, ASSETS_FOLDER)

STATICFILES_DIRS = ()
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
    #  ('text/x-scss', 'django_libsass.SassCompiler'),  # NOTE: DEPRECATED!
    #  ('text/coffeescript', 'coffee --compile --stdio'),
    #  ('text/less', 'lessc {infile} {outfile}'),
    #  ('text/x-sass', 'sass {infile} {outfile}'),
    #  ('text/stylus', 'stylus < {infile} > {outfile}'),
    #  ('text/foobar', 'path.to.MyPrecompilerFilter'),
)

ALLOWED_HOSTS = ["events.d-d-s.ch"]
CSRF_TRUSTED_ORIGINS = ["https://events.d-d-s.ch"]

# Application definition

INSTALLED_APPS = [
    "livereload",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "compressor",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_registration",
    "dds_registration",
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

ROOT_URLCONF = "dds_registration.urls"

TEMPLATES_PATH = BASE_DIR / APP_NAME / "templates"
TEMPLATE_DIRS = [
    TEMPLATES_PATH,
    STATIC_ROOT,
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
                "dds_registration.context_processors.common_values",
            ],
        },
        "DIRS": TEMPLATE_DIRS,
    },
]

WSGI_APPLICATION = "dds_registration.wsgi.application"

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

# Registration
# @see https://django-registration.readthedocs.io

ACCOUNT_ACTIVATION_DAYS = 7  # One-week activation window

# @see https://docs.sendgrid.com/for-developers/sending-email/django
DEFAULT_FROM_EMAIL = "noreply@d-d-s.ch"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"  # this is exactly the value 'apikey'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_PASSWORD = env("SENDGRID_API_KEY")
if not EMAIL_HOST_PASSWORD:
    error_text = "Error: Environment variable SENDGRID_API_KEY required."
    raise Exception(error_text)

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
SITE_NAME = "DdS events registration"
SITE_TITLE = SITE_NAME
SITE_DESCRIPTION = SITE_NAME
SITE_KEYWORDS = """
Registration
Events
"""
SITE_KEYWORDS = re.sub(r"\s*[\n\r]+\s*", ", ", SITE_KEYWORDS.strip())

# Pass settings to context...
PASS_VARIABLES = {
    "DEBUG": DEBUG,
    "DEV": False,
    "LOCAL": False,
    "USE_DJANGO_PREPROCESSORS": USE_DJANGO_PREPROCESSORS,
    "SITE_NAME": SITE_NAME,
    "SITE_TITLE": SITE_TITLE,
    "SITE_DESCRIPTION": SITE_DESCRIPTION,
    "SITE_KEYWORDS": SITE_KEYWORDS,
}
