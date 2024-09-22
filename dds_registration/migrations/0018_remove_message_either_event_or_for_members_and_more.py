# Generated by Django 5.0.3 on 2024-09-22 05:26

import dds_registration.core.helpers.dates
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dds_registration', '0017_alter_registrationoption_membership_end_year'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='message',
            name='either_event_or_for_members',
        ),
        migrations.AddField(
            model_name='message',
            name='registration_option',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dds_registration.registrationoption'),
        ),
        migrations.AlterField(
            model_name='registrationoption',
            name='membership_end_year',
            field=models.IntegerField(default=dds_registration.core.helpers.dates.this_year, help_text='If membership is included, until what year is it valid?'),
        ),
        migrations.AddConstraint(
            model_name='message',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('event__isnull', True), ('for_members', True), ('registration_option__isnull', True)), models.Q(('event__isnull', False), ('for_members', False), ('registration_option__isnull', True)), models.Q(('event__isnull', True), ('for_members', False), ('registration_option__isnull', False)), _connector='OR'), name='either_event_or_registration_option_or_for_members'),
        ),
    ]
