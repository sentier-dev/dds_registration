# @module dds_registration/views/billing.py
# @changed 2024.03.29, 18:16

import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site

import stripe

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from ..core.helpers.create_invoice_pdf import create_invoice_pdf
from ..core.helpers.errors import errorToString

from ..forms import BillingEventForm
from ..models import Invoice

from .get_invoice_context import (
    get_basic_event_registration_context,
    get_event_invoice_context,
)


stripe.api_key = settings.STRIPE_SECRET_KEY  # 'sk_...'


LOG = logging.getLogger(__name__)


# Basic billing form...


@login_required
def billing_event(request: HttpRequest, event_code: str):
    """
    Basic form to create invoice and/or payment.

    Show the form to select payment options:
    - RegistrationOption (from available ones for this event)
    - `payment_method`: Payment method (either Credit Card or Invoice)
    - `extra_invoice_text`: Extra information they might want to add to the
      Invoice (help text is "Any additional text for the invoice, such as a
      reference or purchase order number").

    Form should display the name and address that we have for that user account.

    Users must be logged in, and registered for the event - otherwise they get
    redirected to the homepage.

    If they are registered, then they have chosen a RegistrationOption, so we
    can use that to look up the price and currency.

    """
    try:
        user = request.user
        if not user.is_authenticated:
            return redirect("index")
        # TODO: Check if invoice has been already created?
        context = get_basic_event_registration_context(request, event_code)
        # TODO: Catch registration doesn't exist
        # event = context["event"]
        registration = context["registration"]
        invoice = context["invoice"]
        is_new = False
        if not invoice:
            is_new = True
            # Create default invoice and initialize default values...
            invoice = Invoice()
            invoice.name = user.get_full_name()
            invoice.address = user.address
        context_redirect = context.get("redirect")
        if context_redirect:
            return context_redirect
        if request.method == "POST":
            # Create a form instance and populate it with data from the request:
            form = BillingEventForm(request.POST, instance=invoice)
            # Check whether it's valid:
            if form.is_valid():
                cleaned_data = form.cleaned_data
                invoice = form.save()
                #  invoice.registration.set(registration)
                debug_data = {
                    "cleaned_data": cleaned_data,
                    "invoice": invoice,
                }
                LOG.debug("Get form data: %s", debug_data)
                new_verb = "created" if is_new else "updated"
                messages.success(request, "Invoice has been successfully " + new_verb)
                # TODO: What if changing an existing invoice and the `payment_method` parameter has changed?
                invoice.save()
                # Update registration...
                registration.invoice = invoice  # Link the invoice
                registration.status = "PAYMENT_PENDING"  # Change the status -- now we're expecting the payment
                registration.save()
                # TODO: Redirect to invoice downloading or to payment page?
                redirect_to = (
                    "billing_event_proceed_invoice"
                    if invoice.payment_method == "INVOICE"
                    else "billing_event_stripe_payment_proceed"
                    # TODO: Add other payment method redirects here (eg, for WISE)
                )
                return redirect(redirect_to, event_code=event_code)
        else:
            form = BillingEventForm(instance=invoice)
        context["form"] = form
        template = "dds_registration/billing/billing_event_form.html.django"
        return render(request, template, context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot process billing for the event "{}": {}'.format(event_code, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


# Invoice pdf...


@login_required
def billing_event_proceed_invoice(request: HttpRequest, event_code: str):
    """
    Show page with information about successfull invoice creation and a link to
    download it.
    """
    context = get_basic_event_registration_context(request, event_code)
    template = "dds_registration/billing/billing_event_proceed_invoice.html.django"
    return render(request, template, context)


@login_required
def billing_event_invoice_download(request: HttpRequest, event_code: str):
    """
    Show page with information about successfull invoice creation and a link to
    download it.
    """
    context = get_event_invoice_context(request, event_code)
    show_debug = False
    if show_debug:
        # DEBUG: Show test page with prepared invoice data
        template = "dds_registration/billing/billing_event_invoice_download_debug.html.django"
        return render(request, template, context)
    pdf = create_invoice_pdf(context)
    return HttpResponse(bytes(pdf.output()), content_type="application/pdf")


# Stripe payment...


@csrf_exempt
def billing_event_payment_stripe_create_checkout_session(request: HttpRequest, event_code: str):
    """
    Create stripe session.

    TODO: Add params for currency and amout
    """
    try:
        return_args = {
            "event_code": event_code,
            "session_id": "CHECKOUT_SESSION_ID_PLACEHOLDER",  # "{CHECKOUT_SESSION_ID}",  # To substitute by stripe
        }
        # route billing_event_stripe_payment_success:
        # "billing/event/<str:event_code>/payment/stripe/success/<str:session_id>"
        # Example from stripe docs:
        # return_url="https://example.com/checkout/return?session_id={CHECKOUT_SESSION_ID}",
        return_url_path = reverse("billing_event_stripe_payment_success", kwargs=return_args)
        return_url_path = return_url_path.replace("CHECKOUT_SESSION_ID_PLACEHOLDER", "{CHECKOUT_SESSION_ID}")
        scheme = "https" if request.is_secure() else "http"
        site = get_current_site(request)
        return_url = scheme + "://" + site.domain + return_url_path
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Test",
                        },
                        "unit_amount": 100,  # NOTE: The price is in cents
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            ui_mode="embedded",
            return_url=return_url,
        )
        result = {
            "clientSecret": session.client_secret,
        }
        return JsonResponse(result)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot start checkout session for the event "{}": {}'.format(event_code, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


@login_required
def billing_event_stripe_payment_proceed(request: HttpRequest, event_code: str):
    """
    Proceed stripe payment.

    Show page with information about successfull payment creation and a link to
    proceed it.
    """
    context = get_event_invoice_context(request, event_code)
    event = context["event"]
    registration = context["registration"]
    total_price = context["total_price"]
    currency = context["currency"]
    debug_data = {
        "event": event,
        "registration": registration,
        "total_price": total_price,
        "currency": currency,
        "context": context,
    }
    LOG.debug("Start stripe payment: %s", debug_data)
    # TODO: Make a payment to stripe
    # @see https://testdriven.io/blog/django-stripe-tutorial/
    # DEBUG
    template = "dds_registration/billing/billing_event_stripe_payment_proceed.html.django"
    return render(request, template, context)


@login_required
def billing_event_stripe_payment_success(request: HttpRequest, event_code: str, session_id: str):
    """
    Proceed stripe payment.

    Show page with information about successfull payment creation and a link to
    proceed it.
    """
    try:
        context = get_event_invoice_context(request, event_code)
        event = context["event"]
        registration = context["registration"]
        total_price = context["total_price"]
        currency = context["currency"]
        invoice = context["invoice"]
        # Try to fetch stripe data...
        session = stripe.checkout.Session.retrieve(session_id)
        session_payment_status = session.get("payment_status")
        session_status = session.get("status")
        payment_success = session_payment_status == "paid" and session_status == "complete"
        # DEBUG...
        debug_data = {
            "payment_success": payment_success,
            "session": session,
            "session_payment_status": session_payment_status,
            "session_status": session_status,
            "event_code": event_code,
            "session_id": session_id,
            "event": event,
            "registration": registration,
            "invoice": invoice,
            "total_price": total_price,
            "currency": currency,
            "context": context,
        }
        LOG.debug("Start stripe payment: %s", debug_data)
        if not payment_success:
            messages.error(request, "Your payment was unsuccessfull")
            return redirect("billing_event", event_code=event_code)
        messages.success(request, "Your payment successfully proceed")
        # Update invoice status
        invoice.status = "PAID"
        # TODO: To save some payment details to invoice?
        invoice.save()
        # TODO:
        # Send email message?
        # Smth else?
        template = "dds_registration/billing/billing_event_stripe_payment_success.html.django"
        return render(request, template, context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot start checkout session for the event "{}": {}'.format(event_code, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


# Membership (TODO)...


@login_required
def billing_membership(request: HttpRequest):
    """
    The first thing users need to do is select if this is an academic,
    business, or normal membership (see `Membership.membership_type`).
    """
    context = {}
    template = "dds_registration/billing/billing_test.html.django"
    return render(request, template, context)


__all__ = []
