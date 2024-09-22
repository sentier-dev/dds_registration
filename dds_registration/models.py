# @module models.py
# @changed 2024.03.28, 19:28

import random
import string
from datetime import date

import requests
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Model, Q, QuerySet
from django.urls import reverse
from fpdf import FPDF
from loguru import logger

from .core.constants.date_time_formats import dateFormat
from .core.constants.payments import (
    currency_emojis,
    payment_details_by_currency,
    site_default_currency,
    site_supported_currencies,
)
from .core.helpers.create_pdf import (
    create_invoice_pdf_from_payment,
    create_receipt_pdf_from_payment,
)
from .core.helpers.dates import this_year
from .core.helpers.email import send_email

alphabet = string.ascii_lowercase + string.digits
random_code_length = 8


# NOTE: A single reusable QuerySet to check if the registration active
REGISTRATION_ACTIVE_QUERY = ~Q(status__in=("CANCELLED", "WITHDRAWN", "DECLINED"))


def random_code(length=random_code_length):
    return "".join(random.choices(alphabet, k=length))


class User(AbstractUser):

    # NOTE: It seems to be imposible to completely remove the `username` because it's used in django_registration
    # username = None

    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, default="")

    # NOTE: Using the email field for the username is incompatible with `django_registration`:
    # @see https://django-registration.readthedocs.io/en/3.4/custom-user.html#compatibility-of-the-built-in-workflows-with-custom-user-models
    # The username and email fields must be distinct. If you wish to use the
    # email address as the username, you will need to write your own completely
    # custom registration form.

    # Username isn't used by itself, but it's still used in the django_registration internals. Both these fields are synced.

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    # These variables are used to determine if email or username have changed on save
    _original_email = None
    _original_username = None

    class Meta(AbstractUser.Meta):
        #  # TODO: Add correct check if email and username are the same?
        #  constraints = [
        #      models.CheckConstraint(
        #          check=Q(email=models.F('username')),
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

    def get_full_name_with_email(self):
        name = self.get_full_name()
        email = self.email
        if not name and email:
            name = email
        items = [
            name,
            "<{}>".format(email) if email and email != name else "",
        ]
        info = "  ".join(filter(None, map(str, items)))
        return info

    @property
    def full_name_with_email(self):
        return self.get_full_name_with_email()

    def clean(self):
        self.sync_email_and_username()
        return super().clean()

    def save(self, *args, **kwargs):
        self.sync_email_and_username()
        return super().save(*args, **kwargs)

    @property
    def is_member(self) -> bool:
        try:
            return Membership.objects.get(user=self).active
        except ObjectDoesNotExist:
            return False

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self._original_email = self.email
        self._original_username = self.username

    def email_user(
        self,
        subject: str,
        message: str,
        html_content: bool = False,
        attachment_content: FPDF | None = None,
        attachment_name: str | None = None,
        from_email: str | None = settings.DEFAULT_FROM_EMAIL,
    ) -> None:
        send_email(
            recipient_address=self.email,
            subject=subject,
            message=message,
            pdf=attachment_content,
            pdf_name=attachment_name,
        )


class Payment(Model):
    STATUS = [
        ("CREATED", "Created"),
        ("ISSUED", "Issued"),
        ("PAID", "Paid"),
        ("REFUNDED", "Refunded"),
        ("OBSOLETE", "Obsolete"),  # Payment no longer needed
    ]
    DEFAULT_STATUS = STATUS[0][0]

    METHODS = [
        ("STRIPE", "Credit Card (Stripe - costs 2-4% more due to credit card fees)"),
        ("INVOICE", "Bank Transfer (Invoice)"),
        #  ("WISE", "Wise"),  # Not yet implemented
    ]
    METHOD_LABELS = {"STRIPE": "Credit Card via Stripe", "INVOICE": "Bank Transfer"}
    DEFAULT_METHOD = "INVOICE"

    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
    status = models.TextField(choices=STATUS, default=DEFAULT_STATUS)

    # Format for memberships:
    # {
    #     "user": {
    #         "id": request.user.id,
    #         "name": form.cleaned_data["name"],
    #         "address": form.cleaned_data["address"],
    #     },
    #     "extra": form.cleaned_data["extra"],
    #     "kind": "membership",
    #     "membership": {
    #         "type": form.cleaned_data["membership_type"],
    #     },
    #     "method": form.cleaned_data["payment_method"],
    #     "price": MEMBERSHIP_DATA[form.cleaned_data["membership_type"]]["price"],
    #     "currency": MEMBERSHIP_DATA[form.cleaned_data["membership_type"]]["currency"],
    # }
    # Format for event registration
    # {
    #     "user": {
    #         "id": request.user.id,
    #         "name": form.cleaned_data["name"],
    #         "address": form.cleaned_data["address"],
    #     },
    #     "extra": form.cleaned_data["extra"],
    #     "kind": "event",
    #     "method": form.cleaned_data["payment_method"],
    #     "event": {
    #         "id": event.id,
    #         "title": event.title,
    #     },
    #     "registration": {
    #         "id": registration.id,
    #     },
    #     "option": {
    #         "id": option.id,
    #         "item": option.item,
    #     },
    #     "price": option.price,
    #     "currency": option.currency,
    #     "includes_membership": option.includes_membership,
    #     "membership_end_year": option.membership_end_year,
    # }
    data = models.JSONField(help_text="Read-only JSON object", default=dict)

    def __str__(self):
        return "Payment {} | {} {:.2f} | {} | {}".format(
            self.id,
            self.data.get("currency", ""),
            self.data.get("price"),
            self.get_status_display(),
            self.data.get("method", ""),
        )

    def mark_obsolete(self):
        """Mark a payment obsolete.

        Normally for when they change their mind on event registration options."""
        if self.status == "OBSOLETE":
            return
        self.status == "OBSOLETE"
        user = User.objects.get(id=self.data["user"]["id"])
        send_email(
            recipient_address=user.email,
            subject=f"Invoice #{self.invoice_no} is obsolete - please do not pay",
            message=f"Invoice {self.invoice_no} is obsolete - {self.data['user']['name']} changed their mind and chose a different item with a different price. An updated invoice will be sent. Please do not pay invoice {self.invoice_no}.\n\nIf you have questions, please contact events@d-d-s.ch. Thanks!",
        )
        self.save()

    def mark_paid(self):
        if self.status == "PAID":
            return
        self.status = "PAID"
        self.data["paid_date"] = date.today().strftime("%Y-%m-%d")

        if self.data.get("includes_membership"):
            user = User.objects.get(id=self.data["user"]["id"])
            try:
                membership = Membership.objects.get(user=user)
                membership.until = max(membership.until, self.data["membership_end_year"])
                membership.save()
            except ObjectDoesNotExist:
                Membership(
                    user=user,
                    membership_type="NORMAL",
                    payment=self,
                    mailing_list=True,
                    until=self.data["membership_end_year"]
                ).save()

        if settings.SLACK_PAYMENTS_WEBHOOK:
            title = self.data["event"]["title"] if self.data["kind"] == "event" else "membership"
            requests.post(
                url=settings.SLACK_PAYMENTS_WEBHOOK,
                json={
                    "text": "Payment by {} of {}{} for {}".format(
                        self.data["user"]["name"], currency_emojis[self.data["currency"]], self.data["price"], title
                    )
                },
            )
        self.email_receipt()
        self.save()

    @property
    def invoice_no(self):
        """
        Same as the actual invoice number, which normally has the form
        {two-digit-year}{zero-padded four digit number starting from 1}
        """
        if not self.id:
            return "NOT-CREATED-YET"
        return "{}{:0>4}".format(self.created.strftime("%y"), self.id)

    @property
    def account(self):
        return payment_details_by_currency[self.data["currency"]]

    @property
    def has_unpaid_invoice(self):
        return self.data["method"] == "INVOICE" and self.status != "PAID"

    def items(self):
        """Adapt items format for events and membership"""
        pass

    def user_extract(self):
        return self.data.get("user", {}).get("name", "(UNKNOWN)")
        "user_extract",
        "amount_extract",
        "currency_extract",

    user_extract.short_description = "Username"

    def amount_extract(self):
        return self.data.get("price", 0.0)

    amount_extract.short_description = "Amount"

    def currency_extract(self):
        return self.data.get("currency", "---")

    currency_extract.short_description = "Cur."

    @property
    def payment_label(self):
        try:
            return self.METHOD_LABELS[self.data["method"]]
        except KeyError:
            return "No payment needed"

    @property
    def currency_label(self):
        return dict(site_supported_currencies).get(self.data["currency"], "")

    @property
    def title(self):
        if self.data["kind"] == "membership":
            return ""

    def invoice_pdf(self):
        return create_invoice_pdf_from_payment(self)

    def receipt_pdf(self):
        return create_receipt_pdf_from_payment(self)

    def email_invoice(self, extra_address: str | None = None):
        user = User.objects.get(id=self.data["user"]["id"])
        # TODO: Issue #149: To extract these (and all other hardcoded here, in `send_email` methods?) texts to template files, with substiting names, urls and emails from settings or preferences values?
        if self.data["kind"] == "membership":
            subject = f"DdS Membership Invoice {self.invoice_no}"
            message = f"Thanks for signing up for Départ de Sentier membership! Membership fees allow us to write awesome open source code, deploy open infrastructure, and run community events without spending all our time fundraising.\n\nYour membership will run until December 31st, {user.membership.until} (Don't worry, you will get a reminder to renew for another year :).\n\nPlease find attached the membership invoice. Your membership is not in force until the bank transfer is received.\n\nYou can change your invoice details here: https://events.d-d-s.ch{reverse('membership_application')}.\n\nIf you have any questions, please contact events@d-d-s.ch."
        else:
            event = Event.objects.get(id=self.data["event"]["id"])
            subject = f"DdS Event {event.title} Registration Invoice {self.invoice_no}"
            message = f"Thanks for registering for {event.title}! We look forward to seeing your, in person or virtually.\n\nDépart de Sentier runs its events and schools on a cost-neutral basis - i.e. we don't make a profit off the registration fees. They are used for catering, room, hotel, and equipment rental, AV hosting and technician fees, and guest speaker costs. We literally could not run this event without your support.\n\nYou can view your registration status and apply for membership at https://events.d-d-s.ch/profile.\n\nPlease find attached the registration invoice. Your registration is not finalized until the bank transfer is received.\n\nYou can change your invoice details here: https://events.d-d-s.ch{reverse('event_registration', args=(event.code,))}.\n\nIf you have any questions, please contact events@d-d-s.ch."
        if extra_address:
            logger.debug(f"Sending additional email to {extra_address}")
            send_email(
                recipient_address=extra_address,
                subject=subject + f" for {user.email}",
                message=message,
                pdf=self.invoice_pdf(),
                pdf_name=f"DdS Invoice {self.invoice_no}.pdf",
            )
        user.email_user(
            subject=subject,
            message=message,
            attachment_content=self.invoice_pdf(),
            attachment_name=f"DdS Invoice {self.invoice_no}.pdf",
        )

    def email_receipt(self):
        user = User.objects.get(id=self.data["user"]["id"])
        kind = "Membership" if self.data["kind"] == "membership" else "Event"
        user.email_user(
            subject=f"DdS {kind} Receipt {self.invoice_no}",
            message="Thanks! A receipt for your event or membership payment is attached. You can always find more information about your item at your your profile: https://events.d-d-s.ch/profile.\n\nWe really appreciate your support. If you have any questions, please contact events@d-d-s.ch.",
            attachment_content=self.receipt_pdf(),
            attachment_name=f"DdS receipt {self.invoice_no}.pdf",
        )


class MembershipData:
    data = [
        {
            "tag": "ACADEMIC",
            "label": "Academic",
            "price": 25,
            "currency": "EUR",
        },
        {
            "tag": "NORMAL",
            "label": "Normal",
            "price": 50,
            "currency": "EUR",
            "default": True,
        },
        {
            "tag": "HONORARY",
            "label": "Honorary",
            "price": 0,
            "currency": "EUR",
        },
    ]
    default = "NORMAL"
    available = {"NORMAL", "ACADEMIC"}

    def __getitem__(self, key: str) -> dict:
        dct = {o["tag"]: o for o in self.data}
        return dct[key]

    @property
    def choices(self):
        return [(o["tag"], o["label"]) for o in self.data]

    @property
    def public_choice_field_with_prices(self):
        return [
            (obj["tag"], "{} ({} {})".format(obj["label"], obj["price"], obj["currency"]))
            for obj in self.data
            if obj["tag"] in self.available
        ]


MEMBERSHIP_DATA = MembershipData()
HUMANS = ("ACADEMIC", "NORMAL", "HONORARY")


class Membership(Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    membership_type = models.TextField(choices=MEMBERSHIP_DATA.choices, default=MEMBERSHIP_DATA.default)

    started = models.IntegerField(default=this_year)
    until = models.IntegerField(default=this_year)
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    mailing_list = models.BooleanField(default=False)

    @property
    def active(self) -> bool:
        return this_year() <= self.until

    @classmethod
    def mailinglist_people(cls):
        return cls.objects.filter(until__gte=this_year(), mailing_list=True, membership_type__in=HUMANS)

    def __str__(self):
        items = [
            self.user.full_name_with_email,
            self.get_membership_type_display(),
            self.started,
        ]
        info = ", ".join(filter(None, map(str, items)))
        return info


class Event(Model):
    code = models.TextField(unique=True, default=random_code)  # Show as an input
    title = models.TextField(unique=True, null=False, blank=False)  # Show as an input
    description = models.TextField(blank=False, null=False)
    success_email = models.TextField(
        blank=False, null=False, help_text="The email sent when registration is complete and paid for"
    )
    public = models.BooleanField(default=True)
    application_form = models.OneToOneField(
        "djf_surveys.Survey", related_name="for_event", null=True, blank=True, on_delete=models.SET_NULL
    )
    application_submitted_email = models.TextField(
        blank=True, null=True, help_text="The email sent when the application is submitted"
    )
    application_accepted_email = models.TextField(
        blank=True, null=True, help_text="The email sent when an application is accepted and registration can proceed"
    )
    application_rejected_email = models.TextField(
        blank=True, null=True, help_text="The email sent when an application is rejected"
    )
    application_open = models.DateField(auto_now_add=True, help_text="Date applications open (inclusive)", null=True)
    application_close = models.DateField(help_text="Date applications close (inclusive)", null=True)
    registration_open = models.DateField(auto_now_add=True, help_text="Date registration opens (inclusive)")
    registration_close = models.DateField(help_text="Date registration closes (inclusive)")
    refund_last_day = models.DateField(null=True, blank=True, help_text="Last day that a fee refund can be offered")
    max_participants = models.PositiveIntegerField(
        default=0,
        help_text="Maximum number of participants (0 = no limit)",
    )
    free = models.BooleanField(default=False)
    credit_cards = models.BooleanField(default=True)
    vat_rate = models.FloatField(null=True, blank=True)
    members_only = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(registration_close__gte=models.F("registration_open")),
                name="registration_close_after_open",
            ),
            models.CheckConstraint(
                name="no_vat_for_credit_cards",
                check=(
                    Q(
                        vat_rate__isnull=True,
                        credit_cards=True,
                    )
                    | Q(
                        vat_rate__isnull=False,
                        credit_cards=False,
                    )
                ),
            ),
            # models.CheckConstraint(
            #     name="application_forms_need_valid_dates",
            #     check=(
            #         Q(
            #             application_form__isnull=True,
            #             application_open__isnull=True,
            #         )
            #         | Q(
            #             application_form__isnull=False,
            #             application_open__isnull=False,
            #             application_close__gte=models.F("application_open")
            #         )
            #     ),
            # ),
        ]

    def get_admin_url(self):
        return "https://{}{}".format(
            Site.objects.get_current().domain,
            reverse(
                "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
                args=(self.id,)
            )
        )

    def today_within_registration_band(self):
        today = date.today()
        return (
            today >= self.registration_open
            and today <= self.registration_close
        )

    def today_within_application_band(self):
        if not self.application_open:
            return False
        today = date.today()
        return (
            today >= self.application_open
            and today <= self.application_close
        )

    @property
    def can_register(self, user):
        # Only users who were selected can register after application deadline
        if self.max_participants and self.active_registration_count >= self.max_participants:
            return False
        if self.application_form:
            if Registration.objects.filter(user=user, event__id=self.id, status="SELECTED").count():
                return self.today_within_registration_band()
            return self.today_within_application_band()
        return self.today_within_registration_band()

    @property
    @admin.display(description="Registration Count")
    def active_registration_count(self):
        return self.registrations.all().filter(REGISTRATION_ACTIVE_QUERY).count()

    def get_active_event_registration_for_user(self, user: User):
        if not user.is_anonymous:
            active_user_registrations = list(self.registrations.all().filter(REGISTRATION_ACTIVE_QUERY, user=user))
        else:
            active_user_registrations = []
        if active_user_registrations:
            return active_user_registrations[0]
        return None

    @property
    def edit_registration_url(self):
        return "https://{}{}".format(
            Site.objects.get_current().domain, reverse("event_registration", args=(self.code,))
        )

    def __str__(self):
        name_items = [
            self.title,
            "({})".format(self.code) if self.code else None,
        ]
        return " ".join(filter(None, map(str, name_items)))


class RegistrationOption(Model):
    event = models.ForeignKey(Event, related_name="options", on_delete=models.CASCADE)
    item = models.TextField(null=False, blank=False)  # Show as an input
    price = models.FloatField(default=0, null=False)
    includes_membership = models.BooleanField(
        default=False, help_text="Does this registration option include DdS membership?"
    )
    membership_end_year = models.IntegerField(
        default=this_year, help_text="If membership is included, until what year is it valid?"
    )

    SUPPORTED_CURRENCIES = site_supported_currencies
    DEFAULT_CURRENCY = site_default_currency
    currency = models.TextField(choices=SUPPORTED_CURRENCIES, null=False, default=DEFAULT_CURRENCY)

    def net_price(self):
        if not self.has_vat:
            return self.price
        else:
            return round(self.price * (1 + self.event.vat_rate), 2)

    @property
    def has_vat(self):
        return bool(self.event.vat_rate)

    @property
    def vat_percentage(self):
        return round(self.event.vat_rate * 100, 0)

    @property
    def form_label(self):
        if self.includes_membership:
            membership = " (includes DdS membership through {})".format(self.membership_end_year)
        else:
            membership = ""
        if self.has_vat:
            amount = f"{self.price} plus {self.vat_percentage}% VAT: {self.net_price()}"
        else:
            amount = self.price
        return f"{self.item}: {amount} {self.get_currency_display()}{membership}"

    def __str__(self):
        price_items = [
            self.currency,
            self.price,
        ]
        price = " ".join(filter(None, map(str, price_items))) if self.price else ""
        items = [
            self.item,
            "({})".format(price) if price else None,
        ]
        info = " ".join(filter(None, map(str, items)))
        return info


class Message(Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, blank=True, null=True)
    registration_option = models.ForeignKey(RegistrationOption, on_delete=models.CASCADE, blank=True, null=True)
    for_members = models.BooleanField(default=False)
    subject = models.TextField(blank=True, null=True)
    message = models.TextField()
    emailed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}: {} ({})".format(self.event or self.registration_option or "Members", self.subject[:50], "sent" if self.emailed else "not sent")

    def send_email(self):
        if self.emailed:
            return 0

        if self.for_members:
            qs = Membership.mailinglist_people()
            for obj in qs:
                obj.user.email_user(subject=self.subject or "DdS email for members", message=self.message)
        else:
            qs = Registration.objects.filter(REGISTRATION_ACTIVE_QUERY, event__id=self.event_id)
            for obj in qs:
                obj.user.email_user(
                    subject=self.subject or f"Update for DdS Event {self.event.title}", message=self.message
                )
        self.emailed = True
        self.save()
        return qs.count()

    def send_email_if_selected(self):
        if self.emailed:
            return 0

        qs = Registration.objects.filter(status="SELECTED", event__id=self.event_id)
        for obj in qs:
            obj.user.email_user(
                subject=self.subject or f"Update for DdS Event {self.event.title}", message=self.message
            )
        self.emailed = True
        self.save()
        return qs.count()

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="either_event_or_registration_option_or_for_members",
                check=(
                    models.Q(
                        event__isnull=True,
                        registration_option__isnull=True,
                        for_members=True,
                    )
                    | models.Q(
                        event__isnull=False,
                        registration_option__isnull=True,
                        for_members=False,
                    )
                    | models.Q(
                        event__isnull=True,
                        registration_option__isnull=False,
                        for_members=False,
                    )
                ),
            )
        ]


class Registration(Model):
    REGISTRATION_STATUS = [
        # For schools
        ("SUBMITTED", "Application submitted but not accepted"),
        ("SELECTED", "Applicant selected but not yet registered"),
        ("WAITLIST", "Applicant waitlisted"),
        ("DECLINED", "Applicant declined"),
        ("PAYMENT_PENDING", "Registered (payment pending)"),
        ("REGISTERED", "Registered"),
        ("WITHDRAWN", "Withdrawn"),  # Cancelled by user
        ("CANCELLED", "Cancelled"),  # Cancelled by DdS
    ]

    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    event = models.ForeignKey(Event, related_name="registrations", on_delete=models.CASCADE)
    application = models.OneToOneField(
        "djf_surveys.UserAnswer", blank=True, null=True, related_name="registration", on_delete=models.SET_NULL
    )
    user = models.ForeignKey(User, related_name="registrations", on_delete=models.CASCADE)
    option = models.ForeignKey(
        RegistrationOption, on_delete=models.CASCADE, related_name="registrations", null=True, blank=True
    )
    status = models.TextField(choices=REGISTRATION_STATUS)
    send_update_emails = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                condition=REGISTRATION_ACTIVE_QUERY,
                name="Single active registration per verified user account",
            )
        ]

    @classmethod
    def active_for_user(cls, user: User) -> QuerySet:
        return cls.objects.filter(REGISTRATION_ACTIVE_QUERY, user=user)

    def accept_application(self):
        """Change status from SUBMITTED to SELECTED"""
        self.status = "SELECTED"
        self.save()
        self.user.email_user(
            subject=f"Application accepted for {self.event.title}",
            message=self.event.application_accepted_email,
        )

    def decline_application(self):
        """Change status from SUBMITTED to SELECTED"""
        self.status = "DECLINED"
        self.save()
        self.user.email_user(
            subject=f"Application declined for {self.event.title}",
            message=self.event.application_rejected_email,
        )

    def complete_registration(self):
        """Change status to REGISTERED"""
        self.status = "REGISTERED"
        self.save()
        self.user.email_user(
            subject=f"Registration complete for {self.event.title}",
            message=self.event.success_email,
        )

    def __str__(self):
        items = [
            self.user.full_name_with_email,
            self.option,
            self.get_status_display(),
            self.created_at.strftime(dateFormat) if self.created_at else None,
        ]
        info = ", ".join(filter(None, map(str, items)))
        return info
