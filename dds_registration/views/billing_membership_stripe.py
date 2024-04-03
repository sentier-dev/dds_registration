# @module billing_membership_stripe.py
# @changed 2024.04.01, 23:57

import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render

from django.http import HttpRequest

from ..core.helpers.errors import errorToString

from ..models import Membership

from .helpers.start_stripe_payment_intent import start_stripe_payment_intent

from .get_invoice_context import get_membership_invoice_context


LOG = logging.getLogger(__name__)


# Stripe payment for membership...


@login_required
def billing_membership_stripe_payment_proceed(request: HttpRequest):
    """
    Proceed stripe payment for a membership: show embedded stripe form.
    """
    user = request.user
    if not user.is_authenticated:
        return redirect("index")
    # Find membership and invoice...
    membership: Membership = None
    #  invoice: Invoice = None
    try:
        membership = Membership.objects.get(user=user)
    except Membership.DoesNotExist:
        raise Exception("Membership does not exist")
    try:
        context = get_membership_invoice_context(request)
        total_price = context["total_price"]
        currency = context["currency"]
        intent_session = start_stripe_payment_intent(
            request=request,
            currency=currency,
            amount=total_price,
        )
        context.update(intent_session)
        debug_data = {
            "membership": membership,
            "total_price": total_price,
            "currency": currency,
            "context": context,
        }
        LOG.debug("Start stripe payment: %s", debug_data)
        template = "dds_registration/billing/billing_membership_stripe_payment_proceed.html.django"
        return render(request, template, context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = "Cannot create invoice page for the membership: {}".format(sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


@login_required
def billing_membership_stripe_payment_success(request: HttpRequest):
    """
    Success info.
    """
    context = get_membership_invoice_context(request)
    invoice = context["invoice"]
    messages.success(request, "Your payment successfully proceed")
    # Update invoice status
    invoice.status = "PAID"
    # TODO: To save some payment details to invoice?
    invoice.save()
    template = "dds_registration/billing/billing_membership_stripe_payment_success.html.django"
    return render(request, template, context)
