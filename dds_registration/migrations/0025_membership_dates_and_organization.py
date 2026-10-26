"""Membership validity as dates, organization fields, reminder log.

Existing rows keep their entitlement: ``until`` year N becomes N-12-31. ``started``
uses the linked payment's paid date when known, else Jan 1 of the stored year.
"""

from datetime import date

import django.db.models.deletion
from django.db import migrations, models

import dds_registration.core.helpers.dates


def year_to_until(year: int) -> date:
    return date(int(year), 12, 31)


def started_from(payment_data, started_year: int) -> date:
    paid = (payment_data or {}).get("paid_date")
    if paid:
        return date.fromisoformat(paid)
    return date(int(started_year), 1, 1)


def forwards(apps, schema_editor):
    Membership = apps.get_model("dds_registration", "Membership")
    for membership in Membership.objects.select_related("payment").iterator():
        membership.until_date = year_to_until(membership.until)
        payment_data = membership.payment.data if membership.payment_id else None
        membership.started_date = started_from(payment_data, membership.started)
        membership.save(update_fields=["until_date", "started_date"])
    RegistrationOption = apps.get_model("dds_registration", "RegistrationOption")
    for option in RegistrationOption.objects.iterator():
        option.membership_until_date = year_to_until(option.membership_end_year)
        option.save(update_fields=["membership_until_date"])


def backwards(apps, schema_editor):
    Membership = apps.get_model("dds_registration", "Membership")
    for membership in Membership.objects.iterator():
        membership.until = membership.until_date.year
        membership.started = membership.started_date.year
        membership.save(update_fields=["until", "started"])
    RegistrationOption = apps.get_model("dds_registration", "RegistrationOption")
    for option in RegistrationOption.objects.iterator():
        option.membership_end_year = option.membership_until_date.year
        option.save(update_fields=["membership_end_year"])


ORGANIZATION_TYPES = [
    ("UNIVERSITY", "University"),
    ("RESEARCH", "Research institute"),
    ("COMPANY", "Company"),
    ("CONSULTANCY", "Consultancy"),
    ("PUBLIC", "Public sector"),
    ("NGO", "NGO / non-profit"),
    ("INDEPENDENT", "Independent / freelance"),
    ("STUDENT", "Student"),
    ("OTHER", "Other"),
]

REMINDER_STAGES = [
    ("before_60", "60 days before expiry"),
    ("before_30", "30 days before expiry"),
    ("expiry", "On expiry"),
    ("after_30", "30 days after expiry"),
    ("after_60", "60 days after expiry"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("dds_registration", "0024_event_has_invitation_event_invitation_text_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="membership",
            name="organization",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="membership",
            name="organization_type",
            field=models.CharField(blank=True, choices=ORGANIZATION_TYPES, default="", max_length=16),
        ),
        migrations.AddField(model_name="membership", name="started_date", field=models.DateField(null=True)),
        migrations.AddField(model_name="membership", name="until_date", field=models.DateField(null=True)),
        migrations.AddField(
            model_name="registrationoption", name="membership_until_date", field=models.DateField(null=True)
        ),
        migrations.CreateModel(
            name="MembershipReminder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("until", models.DateField()),
                ("stage", models.CharField(choices=REMINDER_STAGES, max_length=16)),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
                (
                    "membership",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reminders",
                        to="dds_registration.membership",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="membershipreminder",
            constraint=models.UniqueConstraint(fields=("membership", "until", "stage"), name="one_reminder_per_stage"),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(model_name="membership", name="started"),
        migrations.RemoveField(model_name="membership", name="until"),
        migrations.RemoveField(model_name="registrationoption", name="membership_end_year"),
        migrations.RenameField(model_name="membership", old_name="started_date", new_name="started"),
        migrations.RenameField(model_name="membership", old_name="until_date", new_name="until"),
        migrations.RenameField(
            model_name="registrationoption", old_name="membership_until_date", new_name="membership_until"
        ),
        migrations.AlterField(
            model_name="membership",
            name="started",
            field=models.DateField(default=date.today, help_text="Date the member first joined"),
        ),
        migrations.AlterField(
            model_name="membership",
            name="until",
            field=models.DateField(
                default=dds_registration.core.helpers.dates.one_year_from_today,
                help_text="Last day the membership is valid (inclusive)",
            ),
        ),
        migrations.AlterField(
            model_name="registrationoption",
            name="membership_until",
            field=models.DateField(
                default=dds_registration.core.helpers.dates.end_of_this_year,
                help_text="If membership is included, last day it is valid (inclusive)",
            ),
        ),
    ]
