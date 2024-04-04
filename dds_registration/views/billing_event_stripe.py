# @module billing_event_stripe.py
# @changed 2024.04.01, 23:57

import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import render

from django.http import HttpRequest

from ..core.helpers.errors import errorToString

#  from .helpers.send_payment_receipt import send_payment_receipt
from .helpers.start_stripe_payment_intent import start_stripe_payment_intent

from .get_invoice_context import get_event_invoice_context

LOG = logging.getLogger(__name__)


# Stripe payment for event...


@login_required
def billing_event_stripe_payment_proceed(request: HttpRequest, event_code: str):
    """
    Proceed stripe payment for event registration.
    """
    try:
        context = get_event_invoice_context(request, event_code)
        event = context["event"]
        registration = context["registration"]
        total_price = context["total_price"]
        currency = context["currency"]
        payment_data = {
            "event_code": event_code,
        }
        intent_session = start_stripe_payment_intent(
            request=request,
            currency=currency,
            amount=total_price,
            payment_data=payment_data,
        )
        context.update(intent_session)
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
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot start stripe intent session for "{}": {}'.format(payment_data, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


@login_required
def billing_event_stripe_payment_success(request: HttpRequest, event_code: str):
    """
    Show payment success info.
    """
    context = get_event_invoice_context(request, event_code)
    invoice = context["invoice"]
    messages.success(request, "Your payment successfully proceed")
    # Update invoice status
    if invoice.status != "PAID":
        # XXX: To do it only on the first payment? (TODO: Disable payments if invoice has been already paid?)
        invoice.mark_paid()
        # TODO: To save some other payment details to invoice?
        invoice.save()
        #  # TODO: Issue #103: Send payment receipt message (do we need to send these messages?)
        #  email_body_template = "dds_registration/event/event_payment_receipt_message_body.txt"
        #  email_subject_template = "dds_registration/event/event_payment_receipt_message_subject.txt"
        #  send_payment_receipt(
        #      request=request,
        #      email_body_template=email_body_template,
        #      email_subject_template=email_subject_template,
        #      context=context,
        #  )
    template = "dds_registration/billing/billing_event_stripe_payment_success.html.django"
    return render(request, template, context)
