"""Celery entry points for membership renewal reminders."""

from datetime import date

from celery import shared_task

from ..core.membership import reminders


@shared_task(name="dds_registration.tasks.membership_reminders.sweep")
def sweep() -> int:
    """Daily beat task: enqueue one send per member who is due today."""
    count = 0
    for membership, stage in reminders.due_reminders(date.today()):
        send_reminder.delay(membership.pk, membership.until.isoformat(), stage)
        count += 1
    return count


@shared_task(
    name="dds_registration.tasks.membership_reminders.send_reminder",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_reminder(membership_id: int, until_iso: str, stage: str) -> bool:
    return reminders.send_reminder(membership_id, date.fromisoformat(until_iso), stage)
