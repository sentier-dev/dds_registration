"""Send (or list) today's membership renewal reminders without going through Celery.

Use ``--dry-run`` on the server before the first automated sweep, and the plain form
for manual catch-up if the worker was down.
"""

from datetime import date

from django.core.management.base import BaseCommand

from ...core.membership.reminders import due_reminders, send_reminder


class Command(BaseCommand):
    help = "Send membership renewal reminders that are due today (synchronously)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--today", type=date.fromisoformat, default=None, help="Pretend today is this date (YYYY-MM-DD)"
        )
        parser.add_argument("--dry-run", action="store_true", help="List what would be sent, send nothing")

    def handle(self, *args, **options):
        today = options["today"] or date.today()
        due = list(due_reminders(today))
        for membership, stage in due:
            self.stdout.write(f"{membership.user.email}\t{membership.until}\t{stage}")
        if options["dry_run"]:
            self.stdout.write(f"Dry run: {len(due)} reminder(s) due on {today}")
            return
        sent = sum(1 for membership, stage in due if send_reminder(membership.pk, membership.until, stage, today=today))
        self.stdout.write(self.style.SUCCESS(f"Sent {sent} reminder(s) for {today}"))
