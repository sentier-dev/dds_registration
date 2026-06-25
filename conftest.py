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
    "SENTRY_DSN": "",
    "DEFAULT_FROM_EMAIL": "test@example.com",
}

for _key, _value in _TEST_ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)
