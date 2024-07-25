# Generated by Django 5.0.3 on 2024-07-25 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dds_registration', '0014_event_no_vat_for_credit_cards'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='members_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='registrationoption',
            name='includes_membership',
            field=models.BooleanField(default=False),
        ),
    ]
