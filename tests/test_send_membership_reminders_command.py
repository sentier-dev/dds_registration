from datetime import date
from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command

from dds_registration.models import Membership, MembershipReminder


@pytest.fixture
def due_member(django_user_model):
    user = django_user_model.objects.create_user(username="d@example.com", email="d@example.com", password="x")
    return Membership.objects.create(user=user, until=date(2026, 12, 31))


@pytest.mark.django_db
@mock.patch("dds_registration.core.membership.reminders.send_email")
def test_dry_run_lists_without_sending(send_email, due_member):
    out = StringIO()
    call_command("send_membership_reminders", "--today", "2026-11-01", "--dry-run", stdout=out)
    assert "d@example.com" in out.getvalue() and "before_60" in out.getvalue()
    send_email.assert_not_called()
    assert MembershipReminder.objects.count() == 0


@pytest.mark.django_db
@mock.patch("dds_registration.core.membership.reminders.send_email")
def test_real_run_sends_synchronously(send_email, due_member):
    out = StringIO()
    call_command("send_membership_reminders", "--today", "2026-12-01", stdout=out)
    send_email.assert_called_once()
    assert MembershipReminder.objects.get().stage == "before_30"
    assert "Sent 1" in out.getvalue()
