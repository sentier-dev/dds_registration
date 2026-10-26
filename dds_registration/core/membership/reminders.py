"""Which members get a renewal reminder today, and sending one.

Stages fire at fixed offsets from the membership end date. For a given member only
the latest stage that is already due is considered, so a backlog never produces a
burst of stale emails. Each send is logged in ``MembershipReminder`` keyed on the
end date it was about, which keeps sends idempotent and lets next year's cycle start
clean once the end date moves.
"""

from datetime import date, timedelta
from typing import Iterator

from django.template.loader import render_to_string
from loguru import logger

from ...models import Membership, MembershipReminder
from ..helpers.email import send_email

STAGES = (
    ("before_60", -60),
    ("before_30", -30),
    ("expiry", 0),
    ("after_30", 30),
    ("after_60", 60),
)
WINDOW_DAYS = 60
PENDING_PAYMENT_STATUSES = ("CREATED", "ISSUED")
RENEW_URL = "https://events.d-d-s.ch/membership/apply"
SUBJECT_TEMPLATE = "dds_registration/membership/reminder/subject.txt"
BODY_TEMPLATE = "dds_registration/membership/reminder/body.txt"


def stage_due(until: date, today: date) -> str | None:
    """Latest stage whose fire date is on or before ``today``; None when nothing is due yet."""
    due = None
    for name, offset in STAGES:
        if until + timedelta(days=offset) <= today:
            due = name
    return due


def _has_pending_renewal(membership: Membership) -> bool:
    """A renewal invoice is already out: issued within this end date's reminder window, unpaid."""
    payment = membership.payment
    return bool(
        payment
        and payment.status in PENDING_PAYMENT_STATUSES
        and payment.data.get("kind") == "membership"
        and payment.created >= membership.until - timedelta(days=WINDOW_DAYS)
    )


def due_reminders(today: date) -> Iterator[tuple[Membership, str]]:
    """Yield ``(membership, stage)`` pairs that should be emailed today."""
    window = (
        Membership.objects.filter(
            until__gte=today - timedelta(days=WINDOW_DAYS),
            until__lte=today + timedelta(days=WINDOW_DAYS),
        )
        .exclude(membership_type="HONORARY")
        .select_related("user", "payment")
        .order_by("until", "pk")
    )
    for membership in window:
        stage = stage_due(membership.until, today)
        if stage is None or _has_pending_renewal(membership):
            continue
        if MembershipReminder.objects.filter(membership=membership, until=membership.until, stage=stage).exists():
            continue
        yield membership, stage


def send_reminder(membership_id: int, until: date, stage: str, today: date | None = None) -> bool:
    """Render and send one reminder; return False when it was already sent."""
    today = today or date.today()
    membership = Membership.objects.select_related("user").get(pk=membership_id)
    if MembershipReminder.objects.filter(membership=membership, until=until, stage=stage).exists():
        return False
    context = {
        "user": membership.user,
        "membership": membership,
        "until": until,
        "stage": stage,
        "days_left": (until - today).days,
        "expired": until < today,
        "renew_url": RENEW_URL,
    }
    subject = " ".join(render_to_string(SUBJECT_TEMPLATE, context).split())
    body = render_to_string(BODY_TEMPLATE, context)
    send_email(recipient_address=membership.user.email, subject=subject, message=body)
    MembershipReminder.objects.create(membership=membership, until=until, stage=stage)
    logger.info("Membership reminder {} sent to {}", stage, membership.user.email)
    return True
