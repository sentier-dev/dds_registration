"""Regression tests for the production auth-cookie configuration.

Background: commit fbee966 widened the session/CSRF cookies to
``Domain=.d-d-s.ch`` so a single events login also authorises the dashboard
host. That turned the previously host-only ``sessionid``/``csrftoken`` cookies
into *distinct* domain cookies, so any browser that had logged in before the
change carried two cookies of each name. Django reads the last duplicate, and
when a browser (notably Safari) sent the stale host-only one last, login broke.

The fix renames the production cookies so they cannot collide with the legacy
host-only ones. These tests pin that invariant. Each loads ``settings`` in a
clean subprocess (no DB / app registry, no module-reload state leakage), so
they run without pytest-django.
"""

import json
import subprocess
import sys

# Minimal env required by settings.py's `environ.Env(...)` at import time.
_BASE_ENV = {
    "DJANGO_SETTINGS_MODULE": "dds_registration.settings",
    "SECRET_KEY": "test",
    "REGISTRATION_SALT": "test",
    "GOOGLE_TOKEN_FILEPATH": "/tmp/token.json",
    "STRIPE_SECRET_KEY": "x",
    "STRIPE_PUBLISHABLE_KEY": "x",
    "STRIPE_PAYMENT_PRODUCT_NAME": "x",
    "SLACK_PAYMENTS_WEBHOOK": "x",
    "SLACK_REGISTRATIONS_WEBHOOK": "x",
    "SENTRY_DSN": "",
    "DEFAULT_FROM_EMAIL": "x@example.com",
}

# Django's stock cookie names -- the ones legacy host-only cookies still use.
_DJANGO_DEFAULT_SESSION_COOKIE = "sessionid"
_DJANGO_DEFAULT_CSRF_COOKIE = "csrftoken"

_DUMP = (
    "import json, dds_registration.settings as s; "
    "print(json.dumps({"
    "'SESSION_COOKIE_NAME': getattr(s, 'SESSION_COOKIE_NAME', None),"
    "'CSRF_COOKIE_NAME': getattr(s, 'CSRF_COOKIE_NAME', None),"
    "'SESSION_COOKIE_DOMAIN': getattr(s, 'SESSION_COOKIE_DOMAIN', None),"
    "'CSRF_COOKIE_DOMAIN': getattr(s, 'CSRF_COOKIE_DOMAIN', None),"
    "'SESSION_COOKIE_SECURE': getattr(s, 'SESSION_COOKIE_SECURE', None),"
    "'CSRF_COOKIE_SECURE': getattr(s, 'CSRF_COOKIE_SECURE', None),"
    "}))"
)


def _load_settings(*, debug: bool) -> dict:
    """Import settings in a fresh interpreter and return the cookie config."""
    env = dict(_BASE_ENV)
    env["DEBUG"] = "True" if debug else "False"
    env["DEV"] = "True" if debug else "False"
    out = subprocess.run(
        [sys.executable, "-c", _DUMP],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    # settings.py logs a Sentry line to stderr; the JSON is the last stdout line.
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_production_cookie_names_avoid_legacy_collision():
    settings = _load_settings(debug=False)

    # The whole point of the fix: production names must differ from Django's
    # defaults so they cannot collide with pre-existing host-only cookies.
    assert settings["SESSION_COOKIE_NAME"] != _DJANGO_DEFAULT_SESSION_COOKIE
    assert settings["CSRF_COOKIE_NAME"] != _DJANGO_DEFAULT_CSRF_COOKIE
    assert settings["SESSION_COOKIE_NAME"] == "dds_sessionid"
    assert settings["CSRF_COOKIE_NAME"] == "dds_csrftoken"


def test_production_keeps_shared_secure_cookie_domain():
    # The rename must not regress the cross-subdomain SSO sharing.
    settings = _load_settings(debug=False)
    assert settings["SESSION_COOKIE_DOMAIN"] == ".d-d-s.ch"
    assert settings["CSRF_COOKIE_DOMAIN"] == ".d-d-s.ch"
    assert settings["SESSION_COOKIE_SECURE"] is True
    assert settings["CSRF_COOKIE_SECURE"] is True


def test_local_dev_leaves_cookie_domain_unset():
    # In local/dev the production block is skipped, so the widened domain and
    # the rename do not apply (Secure cookies would break http://localhost).
    settings = _load_settings(debug=True)
    assert settings["SESSION_COOKIE_DOMAIN"] in (None, "")
    assert settings["SESSION_COOKIE_NAME"] in (None, _DJANGO_DEFAULT_SESSION_COOKIE)
