import random
import string
from datetime import date
from functools import partial

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.sites.models import Site  # To access site properties
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from .core.constants.date_time_formats import dateTimeFormat

alphabet = string.ascii_lowercase + string.digits
random_code_length = 8


def random_code(length=random_code_length):
    return ''.join(random.choices(alphabet, k=length))


class User(AbstractUser):

    # NOTE: It seems to be imposible to completely remove the `username` because it's used in django_registration
    # username = None

    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, default='')

    # NOTE: Using the email field for the username is incompatible with `django_registration`:
    # @see https://django-registration.readthedocs.io/en/3.4/custom-user.html#compatibility-of-the-built-in-workflows-with-custom-user-models
    # The username and email fields must be distinct. If you wish to use the
    # email address as the username, you will need to write your own completely
    # custom registration form.

    # Username isn't used by itself, but it's still used in the django_registration internals. Both these fields are synced.

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # These variables are used to determine if email or username have changed on save
    _original_email = None
    _original_username = None

    class Meta(AbstractUser.Meta):
        #  # TODO: Add correct check if email and username are the same?
        #  constraints = [
        #      models.CheckConstraint(
        #          check=models.Q(email=models.F('username')),
        #          name='username_is_email',
        #      )
        #  ]
        pass

    def sync_email_and_username(self):
        # Check if email or username had changed?
        email_changed = self.email != self._original_email
        username_changed = self.username != self._original_username
        # Auto sync username and email
        if email_changed:
            self.username = self.email
        elif username_changed:
            self.email = self.username
        if email_changed or username_changed:
            self._original_email = self.email
            self._original_username = self.username
            # TODO: To do smth else if email has changed?

    def clean(self):
        # NOTE: This method is called before `save`: it's useless to compare email and here
        #  from django.core.exceptions import ValidationError
        #  if self.email != self.username:
        #      raise ValidationError('Email and username should be equal')
        self.sync_email_and_username()
        return super(User, self).clean()

    def save(self, *args, **kwargs):
        self.sync_email_and_username()
        return super(User, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self._original_email = self.email
        self._original_username = self.username


#  # UNUSED: Address has integrated into the base user model
#  class Profile(models.Model):
#      """
#      Profile is optional now. It's required to use `Profile.objects.get_or_create`, for example to ensure profile object.
#      """
#
#      user = models.OneToOneField(
#          User, related_name='profile', on_delete=models.CASCADE)
#      address = models.TextField()
#
#      def __str__(self):
#          return self.user.username


class Event(models.Model):
    code = models.TextField(unique=True, default=random_code)  # Show as an input
    title = models.TextField(unique=True, null=False, blank=False)  # Show as an input
    description = models.TextField(blank=True)
    public = models.BooleanField(default=False)
    registration_open = models.DateField(auto_now_add=True, help_text='Date registration opens (inclusive)')
    registration_close = models.DateField(blank=True, help_text='Date registration closes (inclusive)')
    max_participants = models.PositiveIntegerField(
        default=0,
        help_text='Maximum number of participants to this event (0 = no limit)',
    )
    currency = models.TextField(null=True, blank=True)  # Show as an input

    payment_deadline_days = models.IntegerField(default=30)
    payment_details = models.TextField(blank=True, default='')

    # TODO: Add closed/finished status?

    @property
    def can_register(self):
        return self.registration_open <= date.today() <= self.registration_close

    def get_active_registrations(self):
        """
        Return the active registrations
        """
        return self.registrations.all().filter(active=True)

    def get_active_user_registration(self, user: User | None):
        """
        Get the user registration for this event
        """
        # Return empty list if no user has specified or it's a `lazy user` (not from system)
        if not user or not user.id:
            return []
        active_user_registrations = self.registrations.all().filter(active=True, user=user)
        if len(active_user_registrations):
            return active_user_registrations[0]
        return None

    def has_active_user_registration(self, user: User | None):
        """
        Has the user registration for this event?
        """
        active_user_registration = self.get_active_user_registration(user)
        return bool(active_user_registration)

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
    #  user = models.ForeignKey(User, related_name='registrations', on_delete=models.CASCADE)
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
                fields=['event', 'user'],
                condition=models.Q(active=True),
                name='Single active registration',
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
