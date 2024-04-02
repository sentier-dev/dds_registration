# @module billing_event_stripe.py
# @changed 2024.04.01, 23:57

import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

import stripe

from django.conf import settings
from django.http import HttpRequest

from .helpers.create_stripe_return_url import create_stripe_return_url

from ..core.helpers.errors import errorToString

from .get_invoice_context import get_event_invoice_context


LOG = logging.getLogger(__name__)


# Stripe payment for event...


@csrf_exempt
def billing_event_payment_stripe_create_checkout_session(
    request: HttpRequest, event_code: str, currency: str, amount: float
):
    """
    Create stripe session.
    Called from js code on checkout page.

    TODO: To use `PaymentIntent` instead of `checkout.Session`?

    @see: https://docs.stripe.com/payments/accept-a-payment?platform=web&ui=elements
    """
    try:
        product_data = {
            # TODO: Set product name by event registration type?
            "name": settings.STRIPE_PAYMENT_PRODUCT_NAME,
        }
        return_args = {
            "event_code": event_code,
            "session_id": "CHECKOUT_SESSION_ID_PLACEHOLDER",  # "{CHECKOUT_SESSION_ID}",  # To substitute by stripe
        }
        return_url = create_stripe_return_url(request, "billing_event_stripe_payment_success", return_args)
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": product_data,
                        # NOTE: The amount value is an integer, and (sic!) in cents (must be multiplied by 100)
                        "unit_amount": round(amount * 100),
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
    Proceed stripe payment for event registration.
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
    # Make a payment to stripe
    template = "dds_registration/billing/billing_event_stripe_payment_proceed.html.django"
    return render(request, template, context)


@login_required
def billing_event_stripe_payment_success(request: HttpRequest, event_code: str, session_id: str):
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
    invoice = context["invoice"]
    try:
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
