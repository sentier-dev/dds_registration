# Generated by Django 5.0.3 on 2024-04-06 06:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dds_registration', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='refund_window_days',
        ),
        migrations.AddField(
            model_name='event',
            name='refund_last_day',
            field=models.DateField(help_text='Last day that a fee refund can be offered', null=True),
        ),
        migrations.AlterField(
            model_name='registrationoption',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='dds_registration.event'),
        ),
    ]