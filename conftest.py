"""Pytest bootstrap.

``dds_registration.settings`` reads several values from the environment with no
defaults (``env("SECRET_KEY")`` etc.), and the project keeps real values in a
gitignored ``.env``. Under pytest there is no ``.env``, so we provide safe dummy
values here -- at import time, before pytest-django loads the settings module.

``DEBUG=True`` puts settings in local/dev mode: sqlite database, django-compressor
disabled (templates render without an offline manifest), and no ``Secure`` cookie
flags (which would otherwise be dropped over the test client's plain HTTP).
"""

import os

_TEST_ENV_DEFAULTS = {
    "DEBUG": "True",
    "DEV": "True",
    "SECRET_KEY": "test-secret-key-not-used-in-production",
    "REGISTRATION_SALT": "test-registration-salt",
    "GOOGLE_TOKEN_FILEPATH": "/tmp/dds-test-google-token.json",
    "STRIPE_PUBLISHABLE_KEY": "pk_test_dummy",
    "STRIPE_SECRET_KEY": "sk_test_dummy",
    "STRIPE_PAYMENT_PRODUCT_NAME": "test-product",
    "SLACK_PAYMENTS_WEBHOOK": "",
    "SLACK_REGISTRATIONS_WEBHOOK": "",
    "ERROR_MONITORING_DSN": "",
    "DEFAULT_FROM_EMAIL": "test@example.com",
    "CELERY_TASK_ALWAYS_EAGER": "True",
    "CELERY_BROKER_URL": "memory://",
}

for _key, _value in _TEST_ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)


def pytest_configure(config):
    """Run Celery tasks inline during tests.

    pytest-django imports the settings module before this conftest runs, so the
    env defaults above do not reach import-time settings such as the Celery
    block; configure the app object directly instead.
    """
    from django.conf import settings

    # Celery resolves the namespaced Django name (CELERY_*) before its own conf
    # overrides, so the attributes have to change on the settings object itself.
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.CELERY_BROKER_URL = "memory://"
