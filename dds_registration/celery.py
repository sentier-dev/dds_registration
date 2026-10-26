"""Celery application; the worker and beat run ``celery -A dds_registration``."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dds_registration.settings")

app = Celery("dds_registration")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
