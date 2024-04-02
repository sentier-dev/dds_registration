# -*- coding: utf-8 -*-
# @module get_event_invoice_context.py
# @changed 2024.03.22, 19:21

import logging
import traceback
from datetime import date

from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest

from ..core.constants.date_time_formats import dateFormat
from ..core.constants.payments import (
    payment_details_by_currency,
    payment_recipient_name,
    payment_recipient_address,
    default_payment_deadline_days,
)
from ..core.helpers.errors import errorToString

from ..models import (
    REGISTRATION_ACTIVE_QUERY,
    Event,
    Registration,
    RegistrationOption,
    User,
    Invoice,
    Membership,
)
from .helpers.events import calculate_total_registration_price
from .helpers.get_membership_cost import get_membership_cost


LOG = logging.getLogger(__name__)

# Default dds parameters

# TODO: To store them in constants or in the settings or in the site configuration?

table_header = (
    # Header...
    "Quantity",
    "Event",
    "Option",
    "Costs",
)


def get_event_text(event: Event) -> str:
    text = "**{}**".format(event.title)
    if event.description:
        text += "\n" + event.description
    return text


def get_registration_payment_currency(registration: Registration):
    """
    A naive way to get currency (considering all the options have the same currency)...
    """
    # options = registration.options.all()  # XXX: Multiple options approach
    option = registration.option
    return option.currency


def create_event_services_table(user: User, event: Event, registration: Registration, currency: str):
    # options = registration.options.all()  # XXX: Multiple options approach
    option = registration.option
    options = [option]
    event_text = get_event_text(event)
    #  count = 1
    total = 0

    table_header_copy = list(table_header)
    # Add currency to the last (price) column...
    if currency:
        table_header_copy[3] += " ({})".format(currency)
    table = (tuple(table_header_copy),)

    def add_option_row(opt: RegistrationOption):
        nonlocal total
        price_items = [
            #  opt.currency,
            opt.price,
        ]
        price_str = " ".join(filter(None, map(str, price_items))) if opt.price else ""
        row_data = (
            1,
            event_text,
            opt.item,
            price_str,
        )
        if opt.price:
            total += opt.price
        #  count += 1
        return row_data

    rows = tuple(map(add_option_row, options))
    total_row = (
        "",
        "__Total__",
        "",
        "__{}__".format(total),
    )
    table = (*table, *rows, total_row)
    # TODO: addons, total
    return table


def get_basic_site_context(request: HttpRequest):
    user: User = request.user
    # Check for non-anonymous user...
    if not user or not user.id:
        raise Exception("Required registered user")
    scheme = "https" if request.is_secure() else "http"
    context = {
        "user": user,
        "site": get_current_site(request),
        "scheme": scheme,
    }
    return context


def get_basic_event_registration_context(request: HttpRequest, event_code: str):
    """
    Check if there already is an invoice for this event/registration.
    Create it if it doesn't already exist.
    """
    context = get_basic_site_context(request)
    context["event_code"] = event_code
    user: User = context["user"]
    event: Event | None = None
    registration: Registration | None = None
    invoice: Invoice | None = None
    # Try to get event object by code...
    try:
        event = Event.objects.get(code=event_code)
        registrations = event.registrations.filter(REGISTRATION_ACTIVE_QUERY, user=user)
        if not len(registrations) or not registrations[0]:
            raise Exception("Not found active registration for the event '{}'".format(event.title))
        registration = registrations[0]
        invoice = registration.invoice
        context["event"] = event
        context["registration"] = registration
        context["invoice"] = invoice
        return context
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot create basic event invoice context for event "{}": {}'.format(event_code, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (redirecting to profile): %s", error_text, debug_data)
        raise Exception(error_text)


def get_event_invoice_context(request: HttpRequest, event_code: str):
    user: User = request.user
    context = get_basic_event_registration_context(request, event_code)
    event: Event = context["event"]
    if not event:
        raise Exception("No event found for the event code '{}'".format(event_code))
    registration: Registration = context["registration"]
    if not registration:
        raise Exception("No registration found for the event '{}' ({})".format(event.title, event_code))
    invoice: Invoice = context["invoice"]
    if not invoice:
        raise Exception("No invoice found for the event '{}' ({})".format(event.title, event_code))
    # TODO: Check if all the parameters have defined?
    try:
        currency = invoice.currency
        table_data = create_event_services_table(user, event, registration, currency)
        payment_deadline_days = event.payment_deadline_days
        # TInvoicePdfParams data...
        optional_text = invoice.extra_invoice_text
        client_name = invoice.name
        client_address = invoice.address
        today = date.today()
        # NOTE: Probably the year in the invoice id should rely on the registration date, not on the invoice creatiion one?
        # year_str = today.strftime("%y")
        invoice_date = today.strftime(dateFormat)
        invoice_no = invoice.invoice_no if invoice else "Unknown"
        payment_terms = "Within **{} business days** of invoice issuance".format(payment_deadline_days)
        payment_details = payment_details_by_currency[
            currency
        ]  # event.payment_details if event.payment_details else default_payment_details
        # TInvoicePdfParams data...
        context["total_price"] = calculate_total_registration_price(registration)
        context["currency"] = currency
        context["optional_text"] = optional_text
        context["client_name"] = client_name
        context["client_address"] = client_address
        context["dds_name"] = payment_recipient_name
        context["dds_address"] = payment_recipient_address
        context["invoice_no"] = invoice_no
        context["invoice_date"] = invoice_date
        context["payment_terms"] = payment_terms
        context["payment_details"] = payment_details
        context["table_data"] = table_data
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot create event registration invoice context for event "{}": {}'.format(event_code, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (redirecting to profile): %s", error_text, debug_data)
        raise Exception(error_text)
    return context


def create_membership_services_table(user: User, membership: Membership):
    invoice = membership.invoice
    currency = invoice.currency  # TODO: Get currency from membership option
    membership_type = membership.membership_type
    item = membership_type  # TODO: get membership text,
    items = [item]
    item_text = "Membership {}".format(membership_type)
    item_price = get_membership_cost(membership)
    #  count = 1
    total = 0

    table_header_copy = list(table_header)
    # Add currency to the last (price) column...
    if currency:
        table_header_copy[3] += " ({})".format(currency)
    table = (tuple(table_header_copy),)

    def add_item_row(item):
        nonlocal total
        price_items = [
            #  currency,
            item_price,
        ]
        price_str = " ".join(filter(None, map(str, price_items))) if item_price else ""
        row_data = (
            1,
            item_text,
            item,
            price_str,
        )
        if item_price:
            total += item_price
        #  count += 1
        return row_data

    rows = tuple(map(add_item_row, items))
    total_row = (
        "",
        "__Total__",
        "",
        "__{}__".format(total),
    )
    table = (*table, *rows, total_row)
    return table


def get_basic_membership_registration_context(request: HttpRequest):
    """
    Check if there already is an invoice for this event/registration.
    Create it if it doesn't already exist.
    """
    context = get_basic_site_context(request)
    user: User = context["user"]
    event: Event | None = None
    membership: Membership | None = None
    try:
        memberships = Membership.objects.filter(user=user)
        if not len(memberships) or not memberships[0]:
            raise Exception("Not found active membership")
        membership = memberships[0]
        invoice = membership.invoice
        context["membership"] = membership
        context["invoice"] = invoice
        return context
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = "Cannot create basic membership invoice context: {}".format(sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (redirecting to profile): %s", error_text, debug_data)
        raise Exception(error_text)


def get_membership_invoice_context(request: HttpRequest):
    context = get_basic_membership_registration_context(request)
    user: User = context["user"]
    membership: Membership = context["membership"]
    if not membership:
        raise Exception("No membership found")
    invoice: Invoice = context["invoice"]
    if not invoice:
        raise Exception("No invoice found for the membership")
    # TODO: Check if all the parameters have defined?
    try:
        currency = invoice.currency  # if invoice else site_default_currency
        table_data = create_membership_services_table(user, membership)
        # TInvoicePdfParams data...
        optional_text = ""  # invoice.extra_invoice_text
        client_name = user.get_full_name()
        client_address = user.address
        today = date.today()
        invoice_date = today.strftime(dateFormat)
        invoice_no = invoice.invoice_no  # if invoice else "Unknown"
        payment_deadline_days = default_payment_deadline_days
        payment_terms = "Within **{} business days** of invoice issuance".format(payment_deadline_days)
        payment_details = payment_details_by_currency[currency]
        # TInvoicePdfParams data...
        context["total_price"] = get_membership_cost(membership)
        context["currency"] = currency
        context["payment_deadline_days"] = payment_deadline_days
        context["optional_text"] = optional_text
        context["client_name"] = client_name
        context["client_address"] = client_address
        context["dds_name"] = payment_recipient_name
        context["dds_address"] = payment_recipient_address
        context["invoice_no"] = invoice_no
        context["invoice_date"] = invoice_date
        context["payment_terms"] = payment_terms
        context["payment_details"] = payment_details
        context["table_data"] = table_data
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = "Cannot create membership invoice context: {}".format(sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (redirecting to profile): %s", error_text, debug_data)
        raise Exception(error_text)
    return context
