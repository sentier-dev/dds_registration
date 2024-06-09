# Generated by Django 5.0.3 on 2024-06-08 08:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dds_registration', '0010_event_application_submitted_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='application_accepted_email',
            field=models.TextField(blank=True, help_text='The email sent when an application is accepted and registration can be done', null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='application_submitted_email',
            field=models.TextField(blank=True, help_text='The email sent the application is submitted', null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='success_email',
            field=models.TextField(help_text='The email sent when registration is complete and paid for'),
        ),
        migrations.AlterField(
            model_name='registration',
            name='send_update_emails',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='registration',
            name='status',
            field=models.TextField(choices=[('SUBMITTED', 'Application submitted but not accepted'), ('SELECTED', 'Applicant selected but not yet registered'), ('WAITLIST', 'Applicant waitlisted'), ('DECLINED', 'Applicant declined'), ('PAYMENT_PENDING', 'Registered (payment pending)'), ('REGISTERED', 'Registered'), ('WITHDRAWN', 'Withdrawn'), ('CANCELLED', 'Cancelled')]),
        ),
    ]