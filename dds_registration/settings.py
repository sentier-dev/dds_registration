# -*- coding:utf-8 -*-
import os
import posixpath
import random
import re
import string
from pathlib import Path

import environ
import sentry_sdk
from loguru import logger

# Working folder

BASE_DIR = Path(__file__).resolve().parent.parent


# App name

APP_NAME = "dds_registration"


# Define default site id for `sites.models`
SITE_ID = 1


def random_string(length: int = 32) -> str:
    possibles = string.ascii_letters + string.digits
    return "".join(random.sample(possibles, length))


env = environ.Env(
    # @see local `.dev` file and example in `.dev.SAMPLE`
    # @see https://django-environ.readthedocs.io
    DEBUG=(bool, False),  # Django debug mode
    SECRET_KEY=(str, random_string()),
    SENDGRID_API_KEY=(str, ""),
    REGISTRATION_SALT=(str, random_string()),
    DEFAULT_FROM_EMAIL=(str, "events@d-d-s.ch"),
    STRIPE_PUBLISHABLE_KEY=(str, ""),
    STRIPE_SECRET_KEY=(str, ""),
    SLACK_WEBHOOK=(str, ""),
    SENTRY_DSN=(str, ""),
)

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
environ.Env.read_env(os.path.join(BASE_DIR, ".env.local"))

# Dev-time flags
DEBUG = env("DEBUG")
DEV = DEBUG
LOCAL = DEV

# Preprocess scss source files with django filters
USE_DJANGO_PREPROCESSORS = False  # LOCAL

# Secrets
SECRET_KEY = env("SECRET_KEY")
REGISTRATION_SALT = env("REGISTRATION_SALT")
SENDGRID_API_KEY = env("SENDGRID_API_KEY")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY") or ''
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
SLACK_WEBHOOK = env("SLACK_WEBHOOK")
SENTRY_DSN = env("SENTRY_DSN")

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
DEFAULT_HOST = "events.d-d-s.ch"
ALLOWED_HOSTS = [
    DEFAULT_HOST,
]
CSRF_TRUSTED_ORIGINS = [
    "https://" + DEFAULT_HOST,
]

if LOCAL or DEBUG:
    # Allow work with local server in local dev mode
    ALLOWED_HOSTS.extend(["localhost", "127.0.0.1"])

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
    "djf_surveys",
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
    APP_NAME + ".middleware.BeautifulMiddleware.BeautifulMiddleware",  # Html content prettifier
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
                "djf_surveys.context_processors.surveys_context",
                APP_NAME + ".core.app.context_processors.common_values",
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
AUTHENTICATION_BACKENDS = [APP_NAME + ".core.app.backends.EmailBackend"]

ACCOUNT_ACTIVATION_DAYS = 7  # One-week activation window

# NOTE: It's possible to store some of these parameters (`DEFAULT_FROM_EMAIL`, definitely) in the site preferences or in the `.env*` files
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
DEFAULT_CONTACT_EMAIL = DEFAULT_FROM_EMAIL
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

(BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)
logger.add(
    BASE_DIR / "logs" / "registration.log",
    rotation="1 week",
    format="[{time}] {level} [{name}:{function}:{line}] {message}",
    filter="dds_registration",
    level="INFO",
)
logger.add(
    BASE_DIR / "logs" / "django.log",
    rotation="1 week",
    format="[{time}] {level} [{name}:{function}:{line}] {message}",
    filter="django",
    level="WARNING",
)

# @see: https://docs.djangoproject.com/en/2.0/ref/settings/#timeout
TIMEOUT = 30 if DEBUG else 300  # Short value for debug time

# Site config

# TODO: Use `Site.objects.get_current().name` (via `from django.contrib.sites.models import Site`) as site title.
SITE_NAME = "Départ de Sentier Events and Membership Portal"
SITE_TITLE = SITE_NAME
# TODO: Issue #40: Add proper site description and keywords...
SITE_DESCRIPTION = "The membership and events registration portal for the DdS. Départ de Sentier (abbreviated DdS) is a non-profit association which supports open sustainability assessment and public engagement. DdS organizes conferences and code, supports teaching, and rewards open software development."
SITE_KEYWORDS = """
Départ de Sentier
DdS
d-d-s.ch
events and membership portal
non-profit association
open sustainability conferences
teaching
open software development
registration
events
membership
"""
SITE_KEYWORDS = re.sub(r"\s*[\n\r]+\s*", ", ", SITE_KEYWORDS.strip())
# TODO: Issue #30: Add correct tags, resources for SSO, search engines and social networks (open graph etc)

# Pass settings to context...
PASS_VARIABLES = {
    "DEBUG": DEBUG,  # Pass django debug flag to the code (from environment)
    "DEV": DEV,  # Dev server mode (from the environment)
    "LOCAL": LOCAL,  # Local dev server mode (from the environment)
    "DEFAULT_HOST": DEFAULT_HOST,
    "USE_DJANGO_PREPROCESSORS": USE_DJANGO_PREPROCESSORS,
    "STRIPE_PUBLISHABLE_KEY": STRIPE_PUBLISHABLE_KEY,
    "DEFAULT_FROM_EMAIL": DEFAULT_FROM_EMAIL,
    "DEFAULT_CONTACT_EMAIL": DEFAULT_CONTACT_EMAIL,
    # NOTE: Site url and name could be taken from site data via `get_current_site`
    "SITE_NAME": SITE_NAME,
    "SITE_TITLE": SITE_TITLE,
    "SITE_DESCRIPTION": SITE_DESCRIPTION,
    "SITE_KEYWORDS": SITE_KEYWORDS,
}

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )
else:
    logger.info("No key for Sentry found")
