from datetime import date, timedelta
from unittest import mock

import pytest
from celery.exceptions import Retry

from dds_registration.models import Membership, MembershipReminder
from dds_registration.tasks.membership_reminders import send_reminder, sweep


@pytest.mark.django_db
@mock.patch("dds_registration.core.membership.reminders.send_email")
def test_sweep_sends_one_email_per_due_member_eagerly(send_email, django_user_model):
    for email in ["a@example.com", "b@example.com"]:
        user = django_user_model.objects.create_user(username=email, email=email, password="x")
        Membership.objects.create(user=user, until=date.today() + timedelta(days=10))
    assert sweep() == 2
    assert send_email.call_count == 2
    assert MembershipReminder.objects.count() == 2
    assert sweep() == 0


@pytest.mark.django_db
@mock.patch("dds_registration.core.membership.reminders.send_email", side_effect=RuntimeError("gmail down"))
def test_send_reminder_failure_leaves_no_log_row(send_email, django_user_model):
    user = django_user_model.objects.create_user(username="f@example.com", email="f@example.com", password="x")
    m = Membership.objects.create(user=user, until=date.today())
    # Eager mode re-runs retries inline and surfaces Celery's Retry (or the original error).
    with pytest.raises((RuntimeError, Retry)):
        send_reminder.apply(args=(m.pk, m.until.isoformat(), "expiry"))
    assert send_email.call_count >= 1
    assert MembershipReminder.objects.count() == 0


def test_beat_schedule_runs_sweep_daily(settings):
    entry = settings.CELERY_BEAT_SCHEDULE["membership-reminders"]
    assert entry["task"] == "dds_registration.tasks.membership_reminders.sweep"


def test_tasks_are_registered_on_the_app():
    from dds_registration.celery import app

    names = {name for name in app.tasks if name.startswith("dds_registration")}
    assert names == {
        "dds_registration.tasks.membership_reminders.sweep",
        "dds_registration.tasks.membership_reminders.send_reminder",
    }
