# Generated by Django 5.0.3 on 2024-07-25 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dds_registration', '0012_event_application_rejected_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='credit_cards',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='event',
            name='vat_rate',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
