import logging
from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.template import loader
from django.core.mail import mail_admins
from django.core.mail.message import EmailMultiAlternatives
from django.db.models.query_utils import Q
from django.contrib.auth.models import User
from django.db.models.aggregates import Count
from timezones import CITY_CHOICES, get_tzinfo, add_to_zones_map

import icalendar
from icalendar.prop import vCalAddress, vText
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import Encoders


def end_of_day(when, timezone):
    '''
    Returns the end of the day after of the given datetime object
    @param when: the datetime to use
    @param timezone: the timezone in which to calculate the end of the day
    '''
    local_dt = when.astimezone(timezone)
    return timezone.normalize(local_dt.replace(hour=23, minute=59, second=59))


class Event(models.Model):
    '''
    An event being organised
    '''
    PUB_STATUS_CHOICES = (
        ('PUB', 'Public'),
        ('REST', 'Restricted'),
        ('PRIV', 'Private'),
        ('UNPUB', 'Unpublished'),
        ('ARCH', 'Archived')
    )

    title = models.CharField(max_length=64, unique=True)
    start = models.DateTimeField(help_text='Local start date and time')
    end = models.DateTimeField(blank=True, null=True,
                               help_text='Local end date and time')
    city = models.CharField(max_length=32, choices=CITY_CHOICES,
                            help_text='Timezone of your event')

    description = models.TextField(blank=True)

    pub_status = models.CharField(
        max_length=8, choices=PUB_STATUS_CHOICES, default='UNPUB',
        verbose_name='Publication status',
        help_text='Public: Visible and bookable by all; ' +
                  'Restricted: Visible and Bookable by invited groups; ' +
                  'Private: Visible by participant, bookable by all; ' +
                  'Unpublished: Visible by organisers, not bookable; ' +
                  'Archived: Not visible, not bookable')

    location_name = models.CharField(max_length=64, null=True, blank=True,
                                     help_text='Venue of your event')
    location_address = models.TextField(null=True, blank=True)

    owner = models.ForeignKey('auth.User', related_name='events_owned',
                              help_text='Main organiser')
    organisers = models.ManyToManyField('auth.User', blank=True, related_name='events_organised')

    booking_close = models.DateTimeField(blank=True, null=True,
                                         help_text='Limit date and time for registering')
    choices_close = models.DateTimeField(blank=True, null=True,
                                         help_text='Limit date and time for changing choices')

    max_participant = models.PositiveSmallIntegerField(
        default=0,
        help_text='Maximum number of participants to this event (0 = no limit)')

    price_for_employees = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    price_for_contractors = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    price_currency = models.CharField(max_length=3, null=True, blank=True,
                                      verbose_name='Currency for prices')

    employees_groups = models.ManyToManyField('auth.Group', blank=True,
                                              related_name='employees_for_event+',
                                              verbose_name='Groups considered as Employees')
    contractors_groups = models.ManyToManyField('auth.Group', blank=True,
                                                related_name='contractors_for_event+',
                                                verbose_name='Groups considered as Contractors')

    def __unicode__(self):
        result = u'{0} - {1:%x %H:%M}'.format(self.title, self.start)
        if self.end is not None:
            result += u' to {0:%x %H:%M}'.format(self.end)
        return result

    def __init__(self, *args, **kwargs):
        '''
        Constructor to initialise some instance-level variables
        '''
        super(Event, self).__init__(*args, **kwargs)
        # Cache dictionnary to save DB queries
        self.users_values_cache = None

    def clean(self):
        '''
        Validate this model
        '''
        super(Event, self).clean()
        if self.booking_close and self.booking_close > self.start:
            raise ValidationError("Bookings must close before the event starts")
        if self.choices_close and self.choices_close > self.start:
            raise ValidationError("Choices must close before the event starts")
        if self.booking_close and self.choices_close and self.booking_close > self.choices_close:
            raise ValidationError("Bookings must close before choices")

    def _populate_users_cache(self):
        '''
        Fill in the cache of info about users related to this event
        '''
        if self.users_values_cache is not None:
            return

        self.users_values_cache = {}

        def add_cache(user, category):
            user_cache = self.users_values_cache.get(user, {})
            user_cache[category] = True
            self.users_values_cache[user] = user_cache

        for orga in self.organisers.all():
            add_cache(orga.id, 'orga')

        employees_groups_ids = self.employees_groups.values_list('id', flat=True)
        employees = User.objects.filter(groups__id__in=employees_groups_ids).distinct()
        for employee in employees.values_list('id', flat=True):
            add_cache(employee, 'empl')

        contractors_groups_ids = self.contractors_groups.values_list('id', flat=True)
        contractors = User.objects.filter(groups__id__in=contractors_groups_ids).distinct()
        for contractor in contractors.values_list('id', flat=True):
            add_cache(contractor, 'contr')

    def _get_from_users_cache(self, user_id, key, default=None):
        '''
        @return: the value for a user_id/key pair from the cache.
        @param default: default value if user/key is not found
        '''
        self._populate_users_cache()
        return self.users_values_cache.get(user_id, {}).get(key, default)

    def user_is_organiser(self, user):
        '''
        Check if the given user is part of the organisers of the event
        '''
        is_orga = self._get_from_users_cache(user.id, 'orga', False)
        is_owner = (user == self.owner)
        return is_orga or is_owner

    def user_is_employee(self, user):
        '''
        Check if the user is part of the employees groups of the event
        '''
        return self._get_from_users_cache(user.id, 'empl', False)

    def user_is_contractor(self, user):
        '''
        Check if the user is part of the contractors groups of the event
        '''
        return self._get_from_users_cache(user.id, 'contr', False)

    def user_can_update(self, user):
        '''
        Check that the given user can update the event
        '''
        return user.is_superuser or self.user_is_organiser(user)

    def user_can_list(self, user, list_archived):
        '''
        Check that the given user can view the event in the list
        @param user: The user signed in. If not specified, assume anonymous user
        @param list_archived: Boolean to indicated it archived events are visible
        '''
        if self.pub_status == 'PUB':
            return True
        elif user.is_anonymous():
            # All other statuses are invisible to anonymous
            return False
        elif self.pub_status == 'REST':
            return (user.is_superuser
                    or self.user_is_organiser(user)
                    or self.user_is_employee(user)
                    or self.user_is_contractor(user)
                    )
        elif self.pub_status == 'PRIV' or self.pub_status == 'UNPUB':
            user_has_booking = self.bookings.filter(person=user, cancelledBy=None).count() > 0
            return (user.is_superuser
                    or user_has_booking
                    or self.user_is_organiser(user)
                    )
        elif self.pub_status == 'ARCH':
            if list_archived:
                return user.is_superuser or self.user_is_organiser(user)
            else:
                return False
        else:
            raise Exception("Unknown publication status: {0}".format(self.pub_status))

    def user_can_book(self, user):
        '''
        Check if the given user can book the event
        '''
        if user.is_anonymous():
            # All statuses are non-bookable by anonymous
            return False

        if self.pub_status == 'PUB':
            return True
        elif self.pub_status == 'REST':
            return (self.user_is_organiser(user)
                    or self.user_is_employee(user)
                    or self.user_is_contractor(user))
        elif self.pub_status == 'PRIV':
            return True
        elif self.pub_status == 'UNPUB':
            return False
        elif self.pub_status == 'ARCH':
            return False
        else:
            raise Exception("Unknown publication status: {0}".format(self.pub_status))

    def get_tzinfo(self):
        '''
        Get the tzinfo object applicable to this event
        '''
        return get_tzinfo(self.city)

    def get_real_end(self):
        '''
        Get the real datetime of the end of the event
        '''
        if self.end is not None:
            return self.end
        else:
            return end_of_day(self.start, self.get_tzinfo())

    def is_ended(self):
        '''
        Check if the event is ended
        '''
        return self.get_real_end() < timezone.now()

    def is_booking_open(self):
        '''
        Check if the event is still open for bookings
        '''
        closed = (self.booking_close is not None
                  and timezone.now() > self.booking_close)
        published = self.pub_status in ('PUB', 'REST', 'PRIV')
        return self.is_choices_open() and not self.is_ended() and not closed and published

    def is_choices_open(self):
        '''
        Check if the event is still open for choices
        '''
        closed = (self.choices_close is not None
                  and timezone.now() > self.choices_close)
        published = self.pub_status in ('PUB', 'REST', 'PRIV')
        return not self.is_ended() and not closed and published

    def get_active_bookings(self):
        '''
        Return the active bookings
        '''
        return self.bookings.filter(cancelledBy__isnull=True)

    def get_cancelled_bookings(self):
        '''
        Return the cancelled bookings
        '''
        return self.bookings.filter(cancelledBy__isnull=False)

    def get_participants_ids(self):
        '''
        Return the ids of users with active bookings
        '''
        return self.get_active_bookings().values_list('person__id', flat=True)

    def get_options_counts(self):
        '''
        Get a summary of the options chosen for this event
        @return: a map of the form {Choice: {Option: count}}
        '''
        result = {}
        event_options = Option.objects.filter(choice__event=self)
        event_options = event_options.filter(bookingoption__booking__cancelledBy=None)
        event_options = event_options.annotate(total=Count('bookingoption'))
        event_options = event_options.select_related('choice')

        for option in event_options:
            choice_counts = result.get(option.choice) or {}
            choice_counts[option] = option.total
            result[option.choice] = choice_counts
        return result

    def get_collected_money_sums(self):
        '''
        Calculate the total money collected by each organiser, for each class of participant
        @return: a list of the form [(orga, {participant_class: total collected}]. This also
        includes a special participant class "Total" and a special organiser "Total" for the
        sums of values per organiser and per participant class
        '''
        organisers_sums = {}
        bookings = self.bookings.select_related(
            'person',
            'paidTo'
        ).filter(paidTo__isnull=False, exempt_of_payment=False)

        for booking in bookings:
            if booking.is_employee():
                entry_name = "Employees"
                entry_price = self.price_for_employees
            elif booking.is_contractor():
                entry_name = "Contractors"
                entry_price = self.price_for_contractors
            else:
                entry_name = "Other"
                entry_price = 1

            orga_entries = organisers_sums.get(booking.paidTo) or {}
            total = orga_entries.get(entry_name) or Decimal(0)
            orga_entries[entry_name] = total + entry_price
            organisers_sums[booking.paidTo] = orga_entries

        overall_totals = {}
        for orga, orga_entries in organisers_sums.iteritems():
            orga_entries["Total"] = sum(organisers_sums[orga].values())
            yield (orga, orga_entries,)

            for entry_name, entry_value in orga_entries.iteritems():
                entry_total = overall_totals.get(entry_name) or Decimal(0)
                overall_totals[entry_name] = entry_total + entry_value
        yield ("Total", overall_totals,)


class Choice(models.Model):
    '''
    A choice that participants have to make for an event
    '''
    event = models.ForeignKey('Event', related_name='choices')
    title = models.CharField(max_length=64)

    class Meta:
        unique_together = ('event', 'title')
        ordering = ['id']

    def __unicode__(self):
        return u'{0}: {1} choice'.format(self.event.title, self.title)


class Option(models.Model):
    '''
    An option available for a choice of an event
    '''
    choice = models.ForeignKey('Choice', related_name='options')
    title = models.CharField(max_length=256)
    default = models.BooleanField(default=False)

    class Meta:
        unique_together = ('choice', 'title')
        ordering = ['choice__id', 'id']

    def __unicode__(self):
        if self.default:
            return u'{0} : option {1} (default)'.format(self.choice, self.title)
        else:
            return u'{0} : option {1}'.format(self.choice, self.title)


class Booking(models.Model):
    '''
    Entry recording a user registration to an event
    '''
    event = models.ForeignKey('Event', related_name='bookings')
    person = models.ForeignKey('auth.User', related_name='bookings')

    confirmedOn = models.DateTimeField(blank=True, null=True)
    cancelledBy = models.ForeignKey('auth.User', blank=True, null=True, related_name='cancelled_bookings')
    cancelledOn = models.DateTimeField(blank=True, null=True)

    paidTo = models.ForeignKey('auth.User', blank=True, null=True, related_name='received_payments')
    datePaid = models.DateTimeField(blank=True, null=True)
    exempt_of_payment = models.BooleanField(default=False)

    class Meta:
        unique_together = ('event', 'person')
        ordering = ['id']

    def __unicode__(self):
        return u'{0} : {1}'.format(self.event.title, self.person)

    def clean(self):
        '''
        Validate the contents of this Model
        '''
        super(Booking, self).clean()
        if (self.paidTo is not None
                and self.must_pay() == 0
                and not self.exempt_of_payment):
            raise ValidationError("{0} does not have to pay for {1}".format(self.person,
                                                                            self.event))
        # Reset the date paid against paid To
        if self.paidTo is not None and self.datePaid is None:
            self.datePaid = timezone.now()
        if self.paidTo is None and self.datePaid is not None:
            self.datePaid = None

        # Reset the cancel date against cancelledBy
        if self.cancelledBy is not None and self.cancelledOn is None:
            self.cancelledOn = timezone.now()
        if self.cancelledBy is None and self.cancelledOn is not None:
            self.cancelledOn = None

        # Checked that the booking is not cancelled and confirmed
        if self.cancelledBy is not None and self.confirmedOn is not None:
            raise ValidationError("Booking can not be both cancelled and confirmed")

    def user_can_update(self, user):
        '''
        Check that the user can update the booking
        '''
        if self.event.user_is_organiser(user):
            # Organisers can always update
            return True
        elif user == self.person:
            # updating a cancelled booking is like re-booking
            if self.cancelledBy is not None:
                return self.event.user_can_book(user)
            else:
                return self.event.is_choices_open()
        return False

    def user_can_cancel(self, user):
        '''
        Check that the user can cancel the booking
        '''
        return ((self.event.is_booking_open() and user == self.person)
                or self.event.user_is_organiser(user))

    def user_can_update_payment(self, user):
        '''
        Check that the user can update payment informations
        '''
        return self.event.user_is_organiser(user)

    def is_employee(self):
        '''
        Check if the user is part of the employees groups of the event
        '''
        return self.event.user_is_employee(self.person)

    def is_contractor(self):
        '''
        Check if the user is part of the contractors groups of the event
        '''
        return self.event.user_is_contractor(self.person)

    def must_pay(self):
        '''
        Returns the amount that the person has to pay for the booking
        @return the amount to be paid as a Decimal value, 0 if no paiment is needed. If the
        amount can not be determined, returns 9999.99
        '''
        if self.exempt_of_payment:
            return Decimal(0)

        if self.is_employee():
            if self.event.price_for_employees is not None:
                return self.event.price_for_employees
            else:
                return Decimal(0)
        elif self.is_contractor():
            if self.event.price_for_contractors is not None:
                return self.event.price_for_contractors
            else:
                return Decimal(0)
        elif (self.event.price_for_employees is not None
              or self.event.price_for_contractors is not None):
            logging.error("User {0} is neither employee not contractor for {1}".format(self.person,
                                                                                       self.event))
            return Decimal(999999) / 100  # To make sure there is no floating point rounding
        else:
            return Decimal(0)

    def get_payment_status_class(self):
        '''
        Return the status of payment (as a Bootstrap context CSS class)
        '''
        if self.paidTo is not None:
            if self.cancelledBy is not None:
                return 'danger'
            else:
                return 'success'
        else:
            if self.cancelledBy is not None:
                return 'default'
            elif self.must_pay() == Decimal(0):
                return 'success'
            else:
                return 'warning'
        return ''

    def get_invite_texts(self):
        '''
        Get the text contents for an invite to the event
        @return: a tuple (title, description_plain, description_html)
        '''
        event = self.event
        event_tz = event.get_tzinfo()

        title_text = 'Invitation to {0}'.format(event.title)

        plain_lines = [
            u'You have registered to an event',
            u'Add it to your calendar!',
            u'',
            u'Event: {0}',
            u'Start: {1}',
            u'End: {2}',
            u'Location: {3}',
            u'Address: {4}',
            u'Description: {5}'
        ]
        plain_text = u'\n'.join(plain_lines).format(
            event.title,
            event.start.astimezone(event_tz),
            event.get_real_end().astimezone(event_tz),
            event.location_name,
            event.location_address,
            event.description
        )

        html_lines = [
            u'<h2>You have registered to an event</h2>',
            u'<h4>Add it to your calendar!</h4>',
            u'<ul>',
            u'<li><label>Event: </label>{0}</li>',
            u'<li><label>Start: </label>{1}</li>',
            u'<li><label>End: </label>{2}</li>',
            u'<li><label>Location: </label>{3}</li>',
            u'<li><label>Address: </label>{4}</li>',
            u'</ul>',
            u'<hr />',
            u'<p>{5}</p>'
        ]
        html_text = u'\n'.join(html_lines).format(
            event.title,
            event.start.astimezone(event_tz),
            event.get_real_end().astimezone(event_tz),
            event.location_name,
            event.location_address,
            event.description
        )

        if self.options.count() > 0:
            plain_lines = [
                u'',
                u'Your Choices:'
            ]
            html_lines = [
                u'<hr />',
                u'<h4>Your Choices</h4>',
                u'<ul>'
            ]
            for part_opt in self.options.all():
                plain_lines.append(
                    u'* {0} : {1}'.format(part_opt.option.choice.title,
                                          part_opt.option.title)
                )
                html_lines.append(
                    u'<li><label>{0} : </label>{1}</li>'.format(part_opt.option.choice.title,
                                                                part_opt.option.title)
                )
            plain_text = plain_text + u'\n'.join(plain_lines)
            html_lines.append(u'</ul>')
            html_text = html_text + u'\n'.join(html_lines)

        return (title_text, plain_text, html_text)

    def get_calendar_entry(self):
        '''
        Build the iCalendar string for the event
        iCal validator, useful for debugging: http://icalvalid.cloudapp.net/
        '''
        event = self.event
        event_tz = event.get_tzinfo()
        creation_time = timezone.now()

        # Generate some description strings
        title, desc_plain, _desc_html = self.get_invite_texts()

        # Generate the Calendar event
        cal = icalendar.Calendar()
        cal.add('prodid', '-//OneEvent event entry//onevent//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'REQUEST')

        # Generate timezone infos relevant to the event
        tzmap = {}
        tzmap = add_to_zones_map(tzmap, event_tz.zone, event.start)
        tzmap = add_to_zones_map(tzmap, event_tz.zone, event.get_real_end())
        tzmap = add_to_zones_map(tzmap, timezone.get_default_timezone_name(), creation_time)

        for (tzid, transitions) in tzmap.items():
            cal_tz = icalendar.Timezone()
            cal_tz.add('tzid', tzid)
            cal_tz.add('x-lic-location', tzid)

            for (transition, tzinfo) in transitions.items():

                if tzinfo['dst']:
                    cal_tz_sub = icalendar.TimezoneDaylight()
                else:
                    cal_tz_sub = icalendar.TimezoneStandard()

                cal_tz_sub.add('tzname', tzinfo['name'])
                cal_tz_sub.add('dtstart', transition)
                cal_tz_sub.add('tzoffsetfrom', tzinfo['tzoffsetfrom'])
                cal_tz_sub.add('tzoffsetto', tzinfo['tzoffsetto'])
                cal_tz.add_component(cal_tz_sub)
            cal.add_component(cal_tz)

        cal_evt = icalendar.Event()

        cal_evt.add('uid', 'event{0}-booking{1}@oneevent'.format(event.id, self.id))
        cal_evt.add('dtstamp', creation_time)
        cal_evt.add('dtstart', event.start.astimezone(event_tz))
        cal_evt.add('dtend', event.get_real_end().astimezone(event_tz))
        cal_evt.add('created', creation_time)
        cal_evt.add('sequence', '1')

        cal_evt.add('summary', title)
        cal_evt.add('description', desc_plain)
        cal_evt.add('location', vText('{0} - {1}'.format(event.city, event.location_name)))

        cal_evt.add('category', 'Event')
        cal_evt.add('status', 'CONFIRMED')
        cal_evt.add('transp', 'OPAQUE')
        cal_evt.add('priority', '5')
        cal_evt.add('class', 'PUBLIC')

        organiser = vCalAddress('mailto:{0}'.format(event.owner.email))
        organiser.params['cn'] = vText(event.owner.get_full_name())
        organiser.params['role'] = vText('CHAIR')
        cal_evt.add('organizer', organiser, encode=0)

        attendee = vCalAddress('mailto:{0}'.format(self.person.email))
        attendee.params['cutype'] = vText('INDIVIDUAL')
        attendee.params['role'] = vText('REQ-PARTICIPANT')
        attendee.params['partstat'] = vText('NEEDS-ACTION')
        attendee.params['rsvp'] = vText('FALSE')
        attendee.params['cn'] = vText(self.person.get_full_name())
        cal_evt.add('attendee', attendee, encode=0)

        cal.add_component(cal_evt)

        return cal.to_ical()

    def send_calendar_invite(self):
        '''
        Send a calendar entry to the participant
        '''
        title, _desc_plain, desc_html = self.get_invite_texts()
        cal_text = self.get_calendar_entry()

        # "Parts" used in various formats
#         part_plain = MIMEText(desc_plain, "plain", 'utf-8')
#         del(part_plain['MIME-Version'])

        part_html = MIMEText(desc_html, 'html', 'utf-8')
        del(part_html['MIME-Version'])

#         part_cal = MIMEText(cal_text, 'calendar; method=REQUEST', 'utf-8')
#         del(part_cal['MIME-Version'])

#         ical_atch = MIMEApplication(cal_text,
#                                     'ics; charset="UTF-8"; name="%s"' % ("invite.ics"))
#         del(ical_atch['MIME-Version'])
#         ical_atch.add_header('Content-Disposition', 'attachment', filename='invite.ics')

        # The "Lotus Notes" fomat
#         msgAlternative = MIMEMultipart('alternative')
#         del(msgAlternative['MIME-Version'])
#         msgAlternative.attach(part_html)
#         msgAlternative.attach(part_cal)
#
#         msgRelated = MIMEMultipart('related')
#         del(msgRelated['MIME-Version'])
#         msgRelated.attach(msgAlternative)
#         msgAlternative.attach(part_html)
#
#         msgMixed = MIMEMultipart('mixed')
#         del(msgMixed['MIME-Version'])
#         msgMixed.attach(msgRelated)
#         msgMixed.attach(ical_atch)
#
#         msg = EmailMultiAlternatives(subject='test invite',
#                                      body=None,
#                                      to=['g.chazot@gmail.com'])
#         msg.attach(msgMixed)

#         # The "Google Calendar" format
#         msgAlternative = MIMEMultipart('alternative')
#         del(msgAlternative['MIME-Version'])
#         msgAlternative.add_header('Content-class', 'urn:content-classes:calendarmessage')
#         msgAlternative.attach(part_plain)
#         msgAlternative.attach(part_html)
#         msgAlternative.attach(part_cal)
#
#         # Create the message object
#         msg = EmailMultiAlternatives(subject=title,
#                                      body=None,
#                                      to=[self.person.email])
#         msg.attach(msgAlternative)
#         msg.attach(ical_atch)

        # The "Outlook" format
        # Create the message object
        msg = EmailMultiAlternatives(subject=title,
                                     body=None,
                                     to=[self.person.email],
                                     from_email=self.event.owner.email)
        msg.extra_headers['Content-class'] = 'urn:content-classes:calendarmessage'
        msg.attach(part_html)

        filename = "invite.ics"
        part = MIMEBase('text', "calendar", method="REQUEST", name=filename)
        part.set_payload(cal_text)
        Encoders.encode_base64(part)
        part.add_header('Content-Description', filename)
        part.add_header("Content-class", "urn:content-classes:calendarmessage")
        part.add_header("Filename", filename)
        part.add_header("Path", filename)
        msg.attach(part)

        print cal_text

        # Send the message
        return msg.send(fail_silently=False) == 1


class BookingOption(models.Model):
    '''
    A choice made by a booking for an event
    '''
    booking = models.ForeignKey('Booking', related_name='options')
    option = models.ForeignKey('Option', null=True, blank=True)

    class Meta:
        unique_together = ('booking', 'option')
        ordering = ['option__choice__id', 'option__id', 'id']

    def __unicode__(self):
        return u'{0} -> {1}'.format(self.booking, self.option)

    def clean(self):
        '''
        Validate the contents of this Model
        '''
        super(BookingOption, self).clean()
        dupes = BookingOption.objects.filter(booking=self.booking,
                                             option__choice=self.option.choice)
        if dupes.count() > 0:
            if dupes.count() != 1 or dupes[0].option != self.option:
                error = 'Participant {0} already has a choice for {1}'.format(self.booking,
                                                                              self.option.choice)
                raise ValidationError(error)


class Message(models.Model):
    MSG_CAT_CHOICES = (
        ('QUERY', 'Question'),
        ('COMMENT', 'Comment'),
        ('BUG', 'Bug report'),
        ('FEAT', 'Feature request'),
        ('ADMIN', 'Administration Request'),
    )
    sender = models.ForeignKey('auth.User')
    category = models.CharField(max_length=8, choices=MSG_CAT_CHOICES,
                                verbose_name='Reason')
    title = models.CharField(max_length=128)
    text = models.TextField(max_length=2048)
    thread_head = models.ForeignKey('Message', related_name='thread',
                                    null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    safe_content = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return u'Message: From {0}, On {1}, Title "{2}"'.format(self.sender,
                                                                self.created,
                                                                self.title)

    def safe_title(self):
        '''
        Returns the title marked safe or not depending on safe_content
        '''
        if self.safe_content:
            return mark_safe(self.title)
        else:
            return self.title

    def safe_text(self):
        '''
        Returns the title marked safe or not depending on safe_content
        '''
        if self.safe_content:
            return mark_safe(self.text)
        else:
            return self.text

    def full_thread(self):
        '''
        Get the full thread of messages related to this one
        '''
        query = Q(id=self.id)
        if self.thread_head:
            query = query | Q(thread_head=self.thread_head)
        else:
            query = query | Q(thread_head=self)
        return Message.objects.filter(query)

    def send_message_notification(self):
        '''
        Send a notification email to the relevant person(s)
        '''
        if self.thread_head:
            prefix = "reply"
        else:
            prefix = "message"
        subject = '[OneEvent] [{1}] New {2}: {0}'.format(self.title,
                                                         self.get_category_display(),
                                                         prefix)
        message_html = loader.render_to_string('message_notification.html',
                                               {'message': self})
        message_text = self.safe_text()

        # Send to the user only the replies that do not come from himself
        if self.thread_head and self.sender != self.thread_head.sender:
            msg = EmailMultiAlternatives(subject, message_text,
                                         to=[self.thread_head.sender.email])
            msg.attach_alternative(message_html, "text/html")
            msg.send(fail_silently=True)
            print "Sent message to {0}".format(self.thread_head.sender.email)
        else:
            mail_admins(subject, message_text, html_message=message_html, fail_silently=True)
