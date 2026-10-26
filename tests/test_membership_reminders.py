from datetime import date, timedelta
from unittest import mock

import pytest

from dds_registration.core.membership.reminders import due_reminders, send_reminder, stage_due
from dds_registration.models import Membership, MembershipReminder, Payment

TODAY = date(2026, 11, 1)
UNTIL = date(2026, 12, 31)


@pytest.mark.parametrize(
    "today,expected",
    [
        (date(2026, 10, 31), None),
        (date(2026, 11, 1), "before_60"),
        (date(2026, 11, 30), "before_60"),
        (date(2026, 12, 1), "before_30"),
        (date(2026, 12, 31), "expiry"),
        (date(2027, 1, 30), "after_30"),
        (date(2027, 3, 1), "after_60"),
        (date(2027, 3, 2), "after_60"),
    ],
)
def test_stage_due(today, expected):
    assert stage_due(UNTIL, today) == expected


def make_member(django_user_model, email, **kwargs):
    user = django_user_model.objects.create_user(username=email, email=email, password="x", first_name="M")
    kwargs.setdefault("until", UNTIL)
    return Membership.objects.create(user=user, **kwargs)


@pytest.mark.django_db
def test_due_reminders_picks_members_in_window(django_user_model):
    in_window = make_member(django_user_model, "in@example.com")
    make_member(django_user_model, "later@example.com", until=TODAY + timedelta(days=61))
    make_member(django_user_model, "long_gone@example.com", until=TODAY - timedelta(days=61))
    assert [(m.pk, s) for m, s in due_reminders(TODAY)] == [(in_window.pk, "before_60")]


@pytest.mark.django_db
def test_due_reminders_skips_honorary(django_user_model):
    make_member(django_user_model, "h@example.com", membership_type="HONORARY")
    assert list(due_reminders(TODAY)) == []


@pytest.mark.django_db
def test_due_reminders_skips_pending_renewal_invoice(django_user_model):
    member = make_member(django_user_model, "p@example.com")
    payment = Payment.objects.create(status="ISSUED", data={"kind": "membership", "user": {"id": member.user_id}})
    Payment.objects.filter(pk=payment.pk).update(created=TODAY)  # issued inside this end date's window
    member.payment = payment
    member.save()
    assert list(due_reminders(TODAY)) == []


@pytest.mark.django_db
def test_due_reminders_ignores_old_unpaid_invoice(django_user_model):
    member = make_member(django_user_model, "o@example.com")
    payment = Payment.objects.create(status="ISSUED", data={"kind": "membership", "user": {"id": member.user_id}})
    Payment.objects.filter(pk=payment.pk).update(created=UNTIL - timedelta(days=400))
    member.payment = payment
    member.save()
    assert [s for _, s in due_reminders(TODAY)] == ["before_60"]


@pytest.mark.django_db
def test_due_reminders_skips_already_sent_stage(django_user_model):
    member = make_member(django_user_model, "s@example.com")
    MembershipReminder.objects.create(membership=member, until=UNTIL, stage="before_60")
    assert list(due_reminders(TODAY)) == []
    assert [s for _, s in due_reminders(date(2026, 12, 1))] == ["before_30"]


@pytest.mark.django_db
def test_backlog_sends_only_latest_stage(django_user_model):
    make_member(django_user_model, "b@example.com")
    assert [s for _, s in due_reminders(date(2027, 1, 15))] == ["expiry"]


@pytest.mark.django_db
@mock.patch("dds_registration.core.membership.reminders.send_email")
def test_send_reminder_emails_and_logs(send_email, django_user_model):
    member = make_member(django_user_model, "e@example.com")
    assert send_reminder(member.pk, UNTIL, "before_30", today=date(2026, 12, 1)) is True
    send_email.assert_called_once()
    kwargs = send_email.call_args.kwargs
    assert kwargs["recipient_address"] == "e@example.com"
    assert kwargs["subject"] == "Your DdS membership expires on 31 December 2026"
    assert "https://events.d-d-s.ch/membership/apply" in kwargs["message"]
    assert "30 days" in kwargs["message"]
    assert MembershipReminder.objects.filter(membership=member, until=UNTIL, stage="before_30").count() == 1


@pytest.mark.django_db
@mock.patch("dds_registration.core.membership.reminders.send_email")
def test_send_reminder_is_idempotent(send_email, django_user_model):
    member = make_member(django_user_model, "i@example.com")
    send_reminder(member.pk, UNTIL, "expiry", today=UNTIL)
    assert send_reminder(member.pk, UNTIL, "expiry", today=UNTIL) is False
    assert send_email.call_count == 1


@pytest.mark.django_db
@mock.patch("dds_registration.core.membership.reminders.send_email")
def test_send_reminder_after_expiry_wording(send_email, django_user_model):
    member = make_member(django_user_model, "x@example.com")
    send_reminder(member.pk, UNTIL, "after_30", today=date(2027, 1, 30))
    assert send_email.call_args.kwargs["subject"] == "Your DdS membership expired on 31 December 2026"
