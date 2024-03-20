import string
import random
from functools import partial
from datetime import date

from django.conf import settings
from django.contrib.sites.models import Site  # To access site properties
from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth.models import (
    Group,
    User,
)


from core.constants.date_time_formats import dateTimeFormat


alphabet = string.ascii_lowercase + string.digits


random_code_length = 8


def random_code(length=random_code_length):
    return ''.join(random.choices(alphabet, k=length))


class Event(models.Model):
    code = models.TextField(unique=True, default=random_code)   # Show as an input
    title = models.TextField(unique=True, null=False, blank=False)  # Show as an input
    description = models.TextField(blank=True)
    registration_open = models.DateField(auto_now_add=True, help_text='Date registration opens')
    registration_close = models.DateField(blank=True, null=True, help_text='Date registration closes')
    max_participants = models.PositiveIntegerField(
        default=0,
        help_text='Maximum number of participants to this event (0 = no limit)',
    )
    currency = models.TextField(null=True, blank=True)  # Show as an input

    payment_deadline_days = models.IntegerField(default=30)
    payment_details = models.TextField(blank=True, default='')

    # TODO: Add closed/finished status?

    def get_active_registrations(self):
        """
        Return the active registrations
        """
        return self.registrations.all().filter(active=True)

    def __unicode__(self):
        return self.name

    def clean(self):
        super(Event, self).clean()
        if self.registration_close and self.registration_open and self.registration_open >= self.registration_close:
            raise ValidationError('Registration must open before it closes')

    def in_registration_window(self):
        today = date.today()
        return (today >= self.registration_open) and (not self.registration_close or today <= self.registration_close)

    def new_registration_url(self):
        return reverse('event_registration_new', args=(self.code,))

    def new_registration_full_url(self):
        site = Site.objects.get_current()
        scheme = 'https'
        # For dev-server use http
        if settings.LOCAL:
            # TODO: Determine actual protocol scheme
            # Eg, with request: `scheme = 'https' if request.is_secure() else 'http'``
            scheme = 'http'
        return scheme + '://' + site.domain + reverse('event_registration_new', args=(self.code,))

    def __str__(self):
        name_items = [
            self.title,
            '({})'.format(self.code) if self.code else None,
        ]
        items = [
            ' '.join(filter(None, map(str, name_items))),
            # self.created_at.strftime(dateTimeFormat) if self.created_at else None,
        ]
        info = ', '.join(filter(None, map(str, items)))
        return info

    new_registration_full_url.short_description = 'New event registration url'


class RegistrationOption(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    item = models.TextField(null=False, blank=False)  # Show as an input
    price = models.FloatField(default=0, null=False)
    add_on = models.BooleanField(default=False)

    def __str__(self):
        items = [
            self.item,
            '({})'.format(self.price) if self.price else None,
        ]
        info = ' '.join(filter(None, map(str, items)))
        return info


class Registration(models.Model):
    """
    Ex `Booking` class in OneEvent
    """

    invoice_no = models.AutoField(primary_key=True)

    event = models.ForeignKey(Event, related_name='registrations', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='registrations', on_delete=models.CASCADE)

    # If the registration has cancelled, the `active` status should be set to false
    active = models.BooleanField(default=True)

    options = models.ManyToManyField(RegistrationOption)

    # Payment method:
    PAYMENT_METHODS = [
        ('STRIPE', 'Stripe'),
        ('INVOICE', 'Invoice'),
    ]
    DEFAULT_PAYMENT_METHOD = 'STRIPE'
    payment_method = models.TextField(choices=PAYMENT_METHODS, default=DEFAULT_PAYMENT_METHOD)

    extra_invoice_text = models.TextField(blank=True, default='')

    paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'user'], condition=models.Q(active=True), name='Single active registration'
            )
        ]

    def __str__(self):
        items = [
            self.user.get_full_name(),
            self.user.email,
            self.created_at.strftime(dateTimeFormat) if self.created_at else None,
        ]
        info = ', '.join(filter(None, map(str, items)))
        return info


class Message(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    message = models.TextField()
    emailed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        items = [
            self.event,
            self.created_at.strftime(dateTimeFormat) if self.created_at else None,
            'emailed' if self.emailed else None,
        ]
        info = ', '.join(filter(None, map(str, items)))
        return info


class DiscountCode(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    code = models.TextField(default=partial(random_code, length=4))  # Show as an input
    # pyright: ignore [reportArgumentType]
    only_registration = models.BooleanField(default=True)
    percentage = models.IntegerField(help_text='Value as a percentage, like 10', blank=True, null=True)
    absolute = models.FloatField(help_text='Absolute amount of discount', blank=True, null=True)

    def __str__(self):
        items = [
            self.event,
            self.created_at.strftime(dateTimeFormat) if self.created_at else None,
        ]
        info = ', '.join(filter(None, map(str, items)))
        return info


class GroupDiscount(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    only_registration = models.BooleanField(default=True)
    percentage = models.IntegerField(help_text='Value as a percentage, like 10', blank=True, null=True)
    absolute = models.FloatField(help_text='Absolute amount of discount', blank=True, null=True)

    def __str__(self):
        items = [
            self.event,
            'registration only' if self.only_registration else None,
            self.percentage,
            self.absolution,
        ]
        info = ', '.join(filter(None, map(str, items)))
        return info


class Profile(models.Model):
    """
    Profile is optional now. It's required to use `Profile.objects.get_or_create`, for example to ensure profile object.
    """

    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    address = models.TextField()

    def __str__(self):
        return self.user.username
